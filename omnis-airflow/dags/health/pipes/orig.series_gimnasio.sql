-- Typed gym series from the last raw load. Rows with any missing value are discarded.
-- One row per (fecha, num): the ETL merges them by that key.
SELECT DISTINCT ON (fecha, num)
    fecha, num, ejercicio, peso, reps, rir, rpe
FROM (
    SELECT
        CAST(raw.null_if_placeholder(fecha) AS DATE)                        AS fecha,
        CAST(CAST(raw.null_if_placeholder(num) AS NUMERIC) AS INTEGER)      AS num,
        raw.null_if_placeholder(ejercicio)                                  AS ejercicio,
        CAST(raw.null_if_placeholder(peso) AS FLOAT)                        AS peso,
        CAST(raw.null_if_placeholder(reps) AS FLOAT)                        AS reps,
        CAST(raw.null_if_placeholder(rir) AS FLOAT)                         AS rir,
        CAST(raw.null_if_placeholder(rpe) AS FLOAT)                         AS rpe
    FROM raw.series_gimnasio
) typed
WHERE fecha IS NOT NULL AND num IS NOT NULL AND ejercicio IS NOT NULL
  AND peso IS NOT NULL AND reps IS NOT NULL AND rir IS NOT NULL AND rpe IS NOT NULL
ORDER BY fecha, num
