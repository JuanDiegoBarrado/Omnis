-- publish.carga_semanal_grupo: the gym load of each muscle group in each ISO week, rebuilt on every run.
-- Rules:
--   - One row per week of clean.calendario up to the current one and muscle group of
--     orig.grupos_musculares, with or without series: a week without series of the group has 0
--     `series` and `si`, and no `rpe_medio` (NULL). The current week is that of CURRENT_DATE, in the
--     time zone of the database (UTC in the stack), and a series dated after it isn't counted yet.
--   - `series` and `si` add up those of clean.impacto_muscular in the week: each series counts with
--     its share in the group, so a bench press adds 1 series to pectoral and 0.35 to triceps.
--   - `rpe_medio` is the mean RPE of those series, weighted by their share.
SELECT
    w.inicio_semana,
    w.anio_iso,
    w.semana_iso,
    g.grupo,
    COALESCE(SUM(i.series), 0) AS series,
    COALESCE(SUM(i.si), 0) AS si,
    SUM(i.rpe * i.series) / NULLIF(SUM(i.series), 0) AS rpe_medio
FROM (
    SELECT DISTINCT inicio_semana, anio_iso, semana_iso
    FROM clean.calendario
    WHERE inicio_semana <= CURRENT_DATE
) w
CROSS JOIN orig.grupos_musculares g
LEFT JOIN clean.impacto_muscular i
    ON i.grupo = g.grupo AND i.fecha BETWEEN w.inicio_semana AND w.inicio_semana + 6
GROUP BY w.inicio_semana, w.anio_iso, w.semana_iso, g.grupo
