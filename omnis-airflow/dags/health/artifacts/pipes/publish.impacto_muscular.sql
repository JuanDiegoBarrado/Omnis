-- publish.impacto_muscular: clean.impacto_muscular as published, rebuilt on every run. No rules of its own.
SELECT
    id_serie,
    fecha,
    grupo,
    series,
    si,
    rpe,
    rir
FROM clean.impacto_muscular
