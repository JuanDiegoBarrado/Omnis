-- publish.impacto_zona: clean.impacto_zona as published, rebuilt on every run. No rules of its own.
SELECT
    id_serie,
    fecha,
    zona,
    series,
    si,
    rpe,
    rir
FROM clean.impacto_zona
