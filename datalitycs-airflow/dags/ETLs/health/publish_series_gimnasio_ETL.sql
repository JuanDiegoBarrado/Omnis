DELETE FROM {DEST_TABLE};

INSERT INTO {DEST_TABLE} (
    serieID,
    fecha,
    ejercicio,
    categoria,
    peso,
    por_RM,
    reps,
    RIR,
    RPE,
    RM,
    SI
)
SELECT
    serieID,
    fecha,
    ejercicio,
    categoria,
    peso,
    por_RM,
    reps,
    RIR,
    RPE,
    RM,
    SI
FROM {ORIGIN1};