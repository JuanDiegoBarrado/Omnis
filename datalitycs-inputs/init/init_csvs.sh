#!/bin/sh
set -e

BASE_DIR="datalitycs-inputs/data"

mkdir -p "$BASE_DIR"

if [ ! -f "$BASE_DIR/series_gimnasio.csv" ]; then
  echo "Creating series_gimnasio.csv"
  echo "fecha,num,ejercicio,peso,reps,RIR,RPE" > "$BASE_DIR/series_gimnasio.csv"
fi

if [ ! -f "$BASE_DIR/sesiones_carrera.csv" ]; then
  echo "Creating sesiones_carrera.csv"
  echo "Fecha,Num,Categoria,Modalidad,Distancia,Tiempo,Cals,FCavg,FCmax,por_Z1,por_Z2,por_Z3,por_Z4,por_Z5" > "$BASE_DIR/sesiones_carrera.csv"
fi

echo "Init completed."
