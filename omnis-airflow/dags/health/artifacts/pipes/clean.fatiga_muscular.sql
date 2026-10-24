-- clean.fatiga_muscular: the work of each muscle group per day, rebuilt on every run.
-- Rules:
--   - One row per day with gym series. id_fatiga is the date (YYYYMMDD).
--   - Each muscle group adds up, over the series of the day, the share of that group in the exercise
--     of each series (orig.ejercicios_musculares). Every series counts the same, whatever its weight,
--     reps or RPE.
--   - An exercise that isn't in orig.ejercicios_musculares adds nothing. A day whose exercises are all
--     missing there has every group NULL.
SELECT
    CAST(TO_CHAR(a.fecha, 'YYYYMMDD') AS VARCHAR) AS id_fatiga,
    a.fecha AS fecha,
    SUM(b.pectoral) AS pectoral,
    SUM(b.triceps) AS triceps,
    SUM(b.dorsal) AS dorsal,
    SUM(b.trapecio) AS trapecio,
    SUM(b.biceps) AS biceps,
    SUM(b.isquios) AS isquios,
    SUM(b.cuadriceps) AS cuadriceps,
    SUM(b.aductores) AS aductores,
    SUM(b.gluteos) AS gluteos,
    SUM(b.gemelos) AS gemelos,
    SUM(b.abdominales) AS abdominales,
    SUM(b.deltoides_anterior) AS deltoides_anterior,
    SUM(b.deltoides_posterior) AS deltoides_posterior,
    SUM(b.deltoides_lateral) AS deltoides_lateral
FROM orig.series_gimnasio a
LEFT JOIN orig.ejercicios_musculares b ON a.ejercicio = b.ejercicio
GROUP BY a.fecha
