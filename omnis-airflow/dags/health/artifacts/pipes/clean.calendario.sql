-- clean.calendario: one row per day, the calendar the weekly tables of publish are built on, rebuilt on every run.
-- Rules:
--   - It goes from January 1 of the year of the first gym series or running session to December 31
--     of the current year (or of the year of the last one, if it is later), whole years so every
--     period is complete. Days without training have their row too.
--   - It is empty while there are no series nor sessions.
--   - Weeks are ISO weeks: from Monday to Sunday, numbered within the year their Thursday falls in
--     (`anio_iso`).
SELECT
    CAST(d.dia AS DATE) AS fecha,
    CAST(EXTRACT(YEAR FROM d.dia) AS INTEGER) AS anio,
    CAST(EXTRACT(MONTH FROM d.dia) AS INTEGER) AS mes,
    CAST(DATE_TRUNC('week', d.dia) AS DATE) AS inicio_semana,
    CAST(EXTRACT(ISOYEAR FROM d.dia) AS INTEGER) AS anio_iso,
    CAST(EXTRACT(WEEK FROM d.dia) AS INTEGER) AS semana_iso,
    CAST(EXTRACT(ISODOW FROM d.dia) AS INTEGER) AS dia_semana
FROM (
    SELECT
        DATE_TRUNC('year', MIN(fecha)) AS desde,
        DATE_TRUNC('year', GREATEST(MAX(fecha), CURRENT_DATE)) + INTERVAL '1 year - 1 day' AS hasta
    FROM (
        SELECT fecha FROM clean.series_gimnasio
        UNION ALL
        SELECT fecha FROM clean.sesiones_carrera
    ) fechas
) rango
CROSS JOIN LATERAL GENERATE_SERIES(rango.desde, rango.hasta, INTERVAL '1 day') AS d(dia)
