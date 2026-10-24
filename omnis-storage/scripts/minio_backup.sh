#!/bin/sh

# Copia mensual del bucket de datos en /backups/<YYYYMMDDHHMMSS>/<bucket>/, con los objetos como ficheros
# normales (se restaura con mc mirror en sentido contrario).
# Cada hora mira si ya hay una copia de este mes, así que la hace al empezar el mes, o al arrancar si
# entonces el equipo estaba apagado. Las fechas son UTC. La copia se escribe en <nombre>.partial y se
# renombra al terminar, así que una copia interrumpida (el contenedor se paró) no cuenta y se repite.
# Si falla, se renombra a <nombre>.failed con su error.log y se avisa por correo (notify_failure.py).
# No se reintenta: <nombre>.failed cuenta como la copia del mes hasta que se borra.
BACKUPS=/backups

# Es el proceso principal del contenedor: sin esto, docker stop esperaría 10 s y lo mataría
trap 'exit 0' TERM INT

mc alias set local http://$MINIO_ENDPOINT $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

while true; do
    now=$(date +%Y%m%d%H%M%S)
    done_this_month=false
    for backup in "$BACKUPS/${now%????????}"???????? "$BACKUPS/${now%????????}"????????.failed; do
        [ -d "$backup" ] && done_this_month=true
    done
    if [ "$done_this_month" = false ]; then
        rm -rf "$BACKUPS"/*.partial
        mkdir -p "$BACKUPS/$now.partial/$MINIO_DATA_BUCKET"
        if mc mirror --quiet "local/$MINIO_DATA_BUCKET" "$BACKUPS/$now.partial/$MINIO_DATA_BUCKET" \
            2> "$BACKUPS/$now.partial/error.log"; then
            rm "$BACKUPS/$now.partial/error.log"
            mv "$BACKUPS/$now.partial" "$BACKUPS/$now"
            echo "Copia creada en $BACKUPS/$now"
        else
            mv "$BACKUPS/$now.partial" "$BACKUPS/$now.failed"
            echo "La copia ha fallado, no se reintenta hasta que se borre $BACKUPS/$now.failed:"
            cat "$BACKUPS/$now.failed/error.log"
            python3 /usr/local/bin/notify_failure.py "the data bucket" "omnis-storage/backups/$now.failed" \
                "$BACKUPS/$now.failed/error.log"
        fi
    fi
    # En segundo plano, para que el trap salte sin esperar a que acabe
    sleep 3600 &
    wait $!
done
