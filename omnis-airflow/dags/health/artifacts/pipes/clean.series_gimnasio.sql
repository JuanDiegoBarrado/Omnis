-- clean.series_gimnasio: every gym series of orig with its category and effort metrics, rebuilt on every run.
-- Rules:
--   - id_serie is the date (YYYYMMDD) and `num` padded to 2 digits. lpad truncates, so a `num` of
--     100 or more gives the id of another series (100 -> "10").
--   - `categoria` comes from orig.ejercicios_musculares. An exercise that isn't there makes the whole
--     ETL fail (`categoria` is NOT NULL) until it is added to that table.
--   - RM is the estimated one-repetition maximum (Brzycki, counting reps + RIR): peso / (1.0278 - 0.0278 * (reps + RIR)).
--   - por_RM is peso / RM, the share of the estimated maximum lifted. It is NULL when peso is 0
--     (bodyweight exercises), which has no RM to compare with.
--   - The CHECKs of the table make the whole ETL fail for a series with reps + RIR = 0 (por_RM
--     would be 1.0278, above 1) or reps + RIR above 36.97 (RM would be negative).
--   - SI (stress index) comes from the RPE: 6 -> 0.6, 6.5 -> 0.7, 7 -> 0.8, 7.5 -> 0.9, 8 -> 1.0,
--     8.5 -> 1.1, 9 -> 1.2, 9.5 -> 1.4, 10 -> 1.6. Any other RPE gives 0.
SELECT
    CAST(TO_CHAR(a.fecha, 'YYYYMMDD') AS VARCHAR) || lpad(CAST(a.num AS VARCHAR), 2, '0') AS id_serie,
    DATE(a.fecha) AS fecha,
    a.ejercicio as ejercicio,
    b.categoria as categoria,
    a.peso as peso,
    (a.peso / (NULLIF(a.peso, 0) / (1.0278 - (0.0278 * (a.reps + a.RIR))))) AS por_RM,
    a.reps as reps,
    a.RIR as RIR,
    a.RPE as RPE,
    (a.peso / (1.0278 - (0.0278 * (a.reps + a.RIR)))) AS RM,
    CASE
        WHEN a.RPE = 6 THEN 0.6
        WHEN a.RPE = 6.5 THEN 0.7
        WHEN a.RPE = 7 THEN 0.8
        WHEN a.RPE = 7.5 THEN 0.9
        WHEN a.RPE = 8 THEN 1.0
        WHEN a.RPE = 8.5 THEN 1.1
        WHEN a.RPE = 9 THEN 1.2
        WHEN a.RPE = 9.5 THEN 1.4
        WHEN a.RPE = 10 THEN 1.6
        ELSE 0
    END AS SI
FROM orig.series_gimnasio a
LEFT JOIN orig.ejercicios_musculares b ON a.ejercicio = b.ejercicio
