-- publish.sesiones_carrera: clean.sesiones_carrera as published, rebuilt on every run. No rules of its own.
SELECT
    id_sesion,
    fecha,
    categoria,
    modalidad,
    distancia,
    tiempo,
    cals,
    fc_avg,
    fc_max,
    por_Z1,
    por_Z2,
    por_Z3,
    por_Z4,
    por_Z5,
    TRIMP
FROM clean.sesiones_carrera a
