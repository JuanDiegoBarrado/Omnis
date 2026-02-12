INSERT INTO {DEST_TABLE} (fecha, num, ejercicio, peso, reps, RIR, RPE)
SELECT CAST(fecha as DATE) fecha, num, ejercicio, peso, reps, RIR, RPE
FROM {ORIGIN1} src
