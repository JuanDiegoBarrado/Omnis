-- publish.fatiga_muscular: the work of each muscle group per day, one row per day and group, rebuilt on every run.
-- Rules:
--   - The three deltoid heads (anterior, lateral, posterior) add up into one group, `deltoides`.
--   - Every group of a day has its row, also when its SI is 0 or NULL.
SELECT
    id_fatiga,
    fecha,
    grupo_muscular,
    SI
FROM (
    SELECT
        id_fatiga,
        fecha,
        pectoral,
        triceps,
        dorsal,
        trapecio,
        biceps,
        isquios,
        cuadriceps,
        aductores,
        gluteos,
        gemelos,
        abdominales,
        deltoides_anterior + deltoides_lateral + deltoides_posterior AS deltoides
    FROM clean.fatiga_muscular
) a
CROSS JOIN LATERAL (
    VALUES
        ('pectoral',    a.pectoral),
        ('triceps',     a.triceps),
        ('dorsal',      a.dorsal),
        ('trapecio',    a.trapecio),
        ('biceps',      a.biceps),
        ('isquios',     a.isquios),
        ('cuadriceps',  a.cuadriceps),
        ('aductores',   a.aductores),
        ('gluteos',     a.gluteos),
        ('gemelos',     a.gemelos),
        ('abdominales', a.abdominales),
        ('deltoides',   a.deltoides)
) AS unpvt(grupo_muscular, SI)
