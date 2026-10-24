#!/bin/sh

# Crear el bucket de datos, donde los productores dejan los ficheros raw que leen los DAGs
mc alias set local http://$MINIO_ENDPOINT $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc mb --ignore-existing local/$MINIO_DATA_BUCKET
