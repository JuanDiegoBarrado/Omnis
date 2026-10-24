SELECT
    CAST(TO_CHAR(a.fecha, 'YYYYMMDD') AS VARCHAR) || lpad(CAST(a.num AS VARCHAR), 2, '0') AS id_sesion,
    DATE(a.fecha) AS fecha,
    a.categoria,
    a.modalidad,
    a.distancia,
    a.tiempo,
    a.cals,
    a.fc_avg,
    a.fc_max,
    a.por_Z1,
    a.por_Z2,
    a.por_Z3,
    a.por_Z4,
    a.por_Z5,
    (a.por_Z1 * 1 + a.por_Z2 * 2 + a.por_Z3 * 3 + a.por_Z4 * 4 + a.por_Z5 * 5) AS TRIMP
FROM orig.sesiones_carrera a
