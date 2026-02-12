INSERT INTO {DEST_TABLE} (
    fatigaID,
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
    deltoides_anterior,
    deltoides_posterior,
    deltoides_lateral
)
SELECT
    CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR) AS fatigaID,
    DATE(a.fecha) AS fecha,
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
FROM {ORIGIN1} a
LEFT JOIN {ADDITIONAL1} b ON a.ejercicio = b.ejercicio
WHERE NOT EXISTS (
    SELECT 1
    FROM {DEST_TABLE} AS dest
    WHERE dest.fatigaID = CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR)
)
GROUP BY DATE(a.fecha);
