#!/bin/sh

# Configura el warehouse en cada arranque y termina: Airflow espera a que acabe bien. Todo lo que
# aplica es idempotente. La conexión, como superusuario, sale de PGHOST, PGUSER, PGPASSWORD y PGDATABASE.
#   1. Crea omnis_airflow, el rol con el que se conecta el engine, si no existe, y le pone la
#      contraseña de POSTGRES_AIRFLOW_PASSWORD, así que un cambio en .env se aplica al arrancar.
#   2. Aplica sql/*.sql en orden, cada fichero en una transacción: si uno falla, no se aplica nada de
#      él y el init acaba con error.
set -e

: "${POSTGRES_AIRFLOW_PASSWORD:?falta POSTGRES_AIRFLOW_PASSWORD en .env}"

# Sin los NOTICE de lo que ya existe, que saldrían en cada arranque
export PGOPTIONS="-c client_min_messages=warning"

# Al crearse por primera vez, la imagen de Postgres arranca un servidor temporal solo por socket, que
# el healthcheck de omnis-database puede dar por bueno: se espera a que acepte conexiones por red
attempts=0
until pg_isready --quiet; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
        echo "$PGHOST no acepta conexiones"
        exit 1
    fi
    sleep 1
done

# La contraseña se lee del entorno (\getenv), para que no aparezca en los argumentos de ningún proceso
psql -v ON_ERROR_STOP=1 --quiet <<'EOF'
SELECT 'CREATE ROLE omnis_airflow LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'omnis_airflow')
\gexec
\getenv airflow_password POSTGRES_AIRFLOW_PASSWORD
ALTER ROLE omnis_airflow WITH LOGIN PASSWORD :'airflow_password';
EOF

for file in "$(dirname "$0")"/sql/*.sql; do
    echo "Aplicando $(basename "$file")"
    psql -v ON_ERROR_STOP=1 --quiet --single-transaction -f "$file"
done
echo "Warehouse configurado"
