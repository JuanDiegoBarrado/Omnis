-- publish.carga_semanal_zona: the gym load of each zona (the categoria of the exercises, plus "Core") in each ISO week, rebuilt on every run.
-- Rules:
--   - One row per week of clean.calendario up to the current one and zona of orig.grupos_musculares,
--     with or without series: a week without series of the zona has 0 `series` and `si`, and no
--     `rpe_medio` (NULL). The current week is that of CURRENT_DATE, in the time zone of the database
--     (UTC in the stack), and a series dated after it isn't counted yet.
--   - `series` and `si` add up those of clean.impacto_zona in the week: each series counts with its
--     largest share among the groups of the zona, so 3 series of Peso muerto rumano add 3 to Pierna
--     posterior, not 4.65. A zona isn't the sum of its groups in publish.carga_semanal_grupo.
--   - `rpe_medio` is the mean RPE of those series, weighted by their share.
SELECT
    w.inicio_semana,
    w.anio_iso,
    w.semana_iso,
    z.zona,
    COALESCE(SUM(i.series), 0) AS series,
    COALESCE(SUM(i.si), 0) AS si,
    SUM(i.rpe * i.series) / NULLIF(SUM(i.series), 0) AS rpe_medio
FROM (
    SELECT DISTINCT inicio_semana, anio_iso, semana_iso
    FROM clean.calendario
    WHERE inicio_semana <= CURRENT_DATE
) w
CROSS JOIN (SELECT DISTINCT zona FROM orig.grupos_musculares) z
LEFT JOIN clean.impacto_zona i
    ON i.zona = z.zona AND i.fecha BETWEEN w.inicio_semana AND w.inicio_semana + 6
GROUP BY w.inicio_semana, w.anio_iso, w.semana_iso, z.zona
