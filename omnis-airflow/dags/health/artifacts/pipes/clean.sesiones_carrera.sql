-- clean.sesiones_carrera: every running session of orig with its training load, rebuilt on every run.
-- Rules:
--   - id_sesion is the date (YYYYMMDD) and `num` padded to 2 digits. lpad truncates, so a `num` of
--     100 or more gives the id of another session (100 -> "10").
--   - TRIMP weighs each zone share by its zone number: 1 * por_z1 + 2 * por_z2 + ... + 5 * por_z5.
--     It doesn't account for the length of the session, so it goes from 1 to 5.
--     It is NULL when the zone shares are (all zones 0 in orig).
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
