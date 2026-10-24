-- orig.series_gimnasio: the gym series of the last raw load, typed. The ETL merges them by (fecha, num).
-- Rules:
--   - Placeholder values are NULL (raw.null_if_placeholder). `num` may come as a decimal ("1.0").
--   - A value that doesn't cast to its type (a date that isn't one...) fails the whole ETL, and orig
--     is left as it was until the raw file is fixed.
--   - Rows with any missing value are discarded, without failing.
--   - One row per (fecha, num). If the raw load has several rows with the same fecha and num (the
--     same series in two files, or twice in one), one of them is kept at random.
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
