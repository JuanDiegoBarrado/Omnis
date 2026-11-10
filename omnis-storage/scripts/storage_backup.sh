#!/bin/sh

# Copia mensual de los ficheros raw de la landing zone (/data/raw, montada solo para lectura) en
# /backups/<YYYYMMDDHHMMSS>/raw/, tal cual (se restaura copiándola de vuelta, ver README.md).
# Cada hora mira si ya hay una copia de este mes, así que la hace al empezar el mes, o al arrancar si
# entonces el equipo estaba apagado. Las fechas son UTC. La copia se escribe en <nombre>.partial y se
# renombra al terminar, así que una copia interrumpida (el contenedor se paró) no cuenta y se repite.
# Si falla, se renombra a <nombre>.failed con su error.log y se avisa por correo (notify_failure.py).
# No se reintenta: <nombre>.failed cuenta como la copia del mes hasta que se borra.
BACKUPS=/backups

# Es el proceso principal del contenedor: sin esto, docker stop esperaría 10 s y lo mataría
trap 'exit 0' TERM INT

while true; do
    now=$(date +%Y%m%d%H%M%S)
    done_this_month=false
    for backup in "$BACKUPS/${now%????????}"???????? "$BACKUPS/${now%????????}"????????.failed; do
        [ -d "$backup" ] && done_this_month=true
    done
    if [ "$done_this_month" = false ]; then
        rm -rf "$BACKUPS"/*.partial
        mkdir -p "$BACKUPS/$now.partial/raw"
        # Antes de que se entregue el primer fichero no hay /data/raw: la copia queda vacía, no falla
        if { [ ! -d /data/raw ] || cp -a /data/raw/. "$BACKUPS/$now.partial/raw/"; } \
            2> "$BACKUPS/$now.partial/error.log"; then
            rm "$BACKUPS/$now.partial/error.log"
            mv "$BACKUPS/$now.partial" "$BACKUPS/$now"
            echo "Copia creada en $BACKUPS/$now"
        else
            mv "$BACKUPS/$now.partial" "$BACKUPS/$now.failed"
            echo "La copia ha fallado, no se reintenta hasta que se borre $BACKUPS/$now.failed:"
            cat "$BACKUPS/$now.failed/error.log"
            python3 /usr/local/bin/notify_failure.py "the raw files" "omnis-storage/backups/$now.failed" \
                "$BACKUPS/$now.failed/error.log"
        fi
    fi
    # En segundo plano, para que el trap salte sin esperar a que acabe
    sleep 3600 &
    wait $!
done
