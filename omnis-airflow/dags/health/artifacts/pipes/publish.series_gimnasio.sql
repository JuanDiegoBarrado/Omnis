-- publish.series_gimnasio: clean.series_gimnasio as published, rebuilt on every run. No rules of its own.
SELECT
    id_serie,
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
FROM clean.series_gimnasio
