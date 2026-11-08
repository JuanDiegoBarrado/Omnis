-- clean.impacto_zona: how much each gym series works each zona (the categoria of the exercises, plus "Core"), rebuilt on every run.
-- Rules:
--   - One row per series and zona with any of its muscle groups in clean.impacto_muscular. The zona of
--     each group comes from orig.grupos_musculares.
--   - `series` is the largest share of the series among the groups of the zona, not their sum: a Peso
--     muerto rumano (1 isquios + 0.55 gluteos) counts 1 for Pierna posterior, not 1.55. So a series
--     never counts more for a zona than for its most worked group in it, and a zona isn't the sum of
--     its groups.
--   - `si` is the SI of the series times that share. `rpe` and `rir` are those of the series, to be
--     averaged weighted by `series`.
--   - A group of clean.impacto_muscular that isn't in orig.grupos_musculares makes the whole ETL fail
--     (its zona would be NULL, and zona is part of the key), instead of losing its series.
SELECT
    i.id_serie,
    i.fecha,
    g.zona,
    MAX(i.series) AS series,
    -- The SI of the series times its largest share: the SI of the series is the same in all of its rows
    MAX(i.si) AS si,
    i.rpe,
    i.rir
FROM clean.impacto_muscular i
LEFT JOIN orig.grupos_musculares g ON g.grupo = i.grupo
GROUP BY i.id_serie, i.fecha, g.zona, i.rpe, i.rir
