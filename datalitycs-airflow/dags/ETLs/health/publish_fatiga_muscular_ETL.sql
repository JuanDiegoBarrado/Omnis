DELETE FROM {DEST_TABLE};

INSERT INTO {DEST_TABLE} (
    fatigaID,
    fecha,
    grupo_muscular,
    SI
)
SELECT
    fatigaID,
    fecha,
    grupo_muscular,
    SI
FROM (
    select fatigaID,
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
    deltoides_anterior + deltoides_lateral + deltoides_posterior as deltoides,
    fecha,
    from {ORIGIN1}
) a
UNPIVOT (
    SI FOR grupo_muscular IN (
    	pectoral, triceps, dorsal,
    	trapecio, biceps, isquios,
    	cuadriceps, aductores, gluteos,
    	gemelos, abdominales,
    	deltoides
    )
) AS unpvt;
