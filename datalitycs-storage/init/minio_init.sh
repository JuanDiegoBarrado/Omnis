#!/bin/bash

# Configurar alias de MinIO
mc alias set local http://datalitycs-storage:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

# Crear buckets si no existen
for bucket in files-prod files-prep files-test
do
  mc mb local/$bucket || echo "$bucket already exists"
done

# Subir archivos a cada bucket
for bucket in files-prod files-prep files-test
do
  mc cp ./storage/init/raw_csvs/series_gimnasio_his.csv local/$bucket/raw/his/series_gimnasio/
  mc cp ./storage/init/raw_csvs/series_gimnasio_new.csv local/$bucket/raw/new/series_gimnasio/
  mc cp ./storage/init/raw_csvs/sesiones_carrera_his.csv local/$bucket/raw/his/sesiones_carrera/
  mc cp ./storage/init/raw_csvs/sesiones_carrera_new.csv local/$bucket/raw/new/sesiones_carrera/
  mc cp ./storage/init/raw_csvs/sesiones_extra_his.csv local/$bucket/raw/his/sesiones_extra/
  mc cp ./storage/init/raw_csvs/sesiones_extra_new.csv local/$bucket/raw/new/sesiones_extra/
  mc cp ./storage/init/raw_csvs/sesiones_natacion_his.csv local/$bucket/raw/his/sesiones_natacion/
  mc cp ./storage/init/raw_csvs/sesiones_natacion_new.csv local/$bucket/raw/new/sesiones_natacion/
done
