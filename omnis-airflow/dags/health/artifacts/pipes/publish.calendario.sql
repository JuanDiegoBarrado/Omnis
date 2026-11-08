-- publish.calendario: clean.calendario as published, rebuilt on every run. No rules of its own.
SELECT
    fecha,
    anio,
    mes,
    inicio_semana,
    anio_iso,
    semana_iso,
    dia_semana
FROM clean.calendario
