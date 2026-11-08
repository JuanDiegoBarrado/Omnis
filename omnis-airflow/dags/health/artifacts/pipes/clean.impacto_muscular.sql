-- clean.impacto_muscular: how much each gym series works each muscle group, rebuilt on every run.
-- Rules:
--   - One row per series and muscle group whose share in the exercise (orig.ejercicios_musculares) is
--     above 0. The groups are the columns of that table, with their names: the three deltoid heads are
--     three groups.
--   - `series` is that share: how much of the series counts for the group. A series adds up to more
--     than 1 over its groups (a bench press is 1 pectoral + 0.35 triceps + 0.30 anterior deltoid), so
--     the sum of `series` over every group isn't the number of series done.
--   - `si` is the SI of the series times its share. `rpe` and `rir` are those of the series, to be
--     averaged weighted by `series`.
--   - Every series has its exercise in orig.ejercicios_musculares: clean.series_gimnasio fails otherwise.
SELECT
    s.id_serie,
    s.fecha,
    g.grupo,
    g.factor AS series,
    s.si * g.factor AS si,
    s.rpe,
    s.rir
FROM clean.series_gimnasio s
JOIN orig.ejercicios_musculares e ON s.ejercicio = e.ejercicio
CROSS JOIN LATERAL (
    VALUES
        ('pectoral',            e.pectoral),
        ('triceps',             e.triceps),
        ('dorsal',              e.dorsal),
        ('trapecio',            e.trapecio),
        ('biceps',              e.biceps),
        ('isquios',             e.isquios),
        ('cuadriceps',          e.cuadriceps),
        ('aductores',           e.aductores),
        ('gluteos',             e.gluteos),
        ('gemelos',             e.gemelos),
        ('abdominales',         e.abdominales),
        ('deltoides_anterior',  e.deltoides_anterior),
        ('deltoides_posterior', e.deltoides_posterior),
        ('deltoides_lateral',   e.deltoides_lateral)
) AS g(grupo, factor)
WHERE g.factor > 0
