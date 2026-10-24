-- Typed running sessions from the last raw load. Rows with any missing value are discarded.
-- `tiempo` goes from HH:MM:SS to minutes and the zone shares are normalized to add up to 1.
-- One row per (fecha, num): the ETL merges them by that key.
SELECT DISTINCT ON (fecha, num)
    fecha,
    num,
    categoria,
    modalidad,
    distancia,
    EXTRACT(HOUR FROM tiempo) * 60 + EXTRACT(MINUTE FROM tiempo) + EXTRACT(SECOND FROM tiempo) / 60.0 AS tiempo,
    cals,
    fc_avg,
    fc_max,
    por_z1 / NULLIF(por_z1 + por_z2 + por_z3 + por_z4 + por_z5, 0) AS por_z1,
    por_z2 / NULLIF(por_z1 + por_z2 + por_z3 + por_z4 + por_z5, 0) AS por_z2,
    por_z3 / NULLIF(por_z1 + por_z2 + por_z3 + por_z4 + por_z5, 0) AS por_z3,
    por_z4 / NULLIF(por_z1 + por_z2 + por_z3 + por_z4 + por_z5, 0) AS por_z4,
    por_z5 / NULLIF(por_z1 + por_z2 + por_z3 + por_z4 + por_z5, 0) AS por_z5
FROM (
    SELECT
        CAST(raw.null_if_placeholder(fecha) AS DATE)                        AS fecha,
        CAST(CAST(raw.null_if_placeholder(num) AS NUMERIC) AS INTEGER)      AS num,
        raw.null_if_placeholder(categoria)                                  AS categoria,
        raw.null_if_placeholder(modalidad)                                  AS modalidad,
        CAST(raw.null_if_placeholder(distancia) AS FLOAT)                   AS distancia,
        CAST(raw.null_if_placeholder(tiempo) AS TIME)                       AS tiempo,
        CAST(raw.null_if_placeholder(cals) AS FLOAT)                        AS cals,
        CAST(raw.null_if_placeholder(fc_avg) AS FLOAT)                      AS fc_avg,
        CAST(raw.null_if_placeholder(fc_max) AS FLOAT)                      AS fc_max,
        CAST(raw.null_if_placeholder(por_z1) AS FLOAT)                      AS por_z1,
        CAST(raw.null_if_placeholder(por_z2) AS FLOAT)                      AS por_z2,
        CAST(raw.null_if_placeholder(por_z3) AS FLOAT)                      AS por_z3,
        CAST(raw.null_if_placeholder(por_z4) AS FLOAT)                      AS por_z4,
        CAST(raw.null_if_placeholder(por_z5) AS FLOAT)                      AS por_z5
    FROM raw.sesiones_carrera
) typed
WHERE fecha IS NOT NULL AND num IS NOT NULL AND categoria IS NOT NULL AND modalidad IS NOT NULL
  AND distancia IS NOT NULL AND tiempo IS NOT NULL AND cals IS NOT NULL
  AND fc_avg IS NOT NULL AND fc_max IS NOT NULL
  AND por_z1 IS NOT NULL AND por_z2 IS NOT NULL AND por_z3 IS NOT NULL AND por_z4 IS NOT NULL AND por_z5 IS NOT NULL
ORDER BY fecha, num
