INSERT INTO {DEST_TABLE} (
    sesionID,
    fecha,
    deporte,
    tiempo,
    cals,
    FCavg,
    FCmax,
    por_Z1,
    por_Z2,
    por_Z3,
    por_Z4,
    por_Z5,
    TRIMP
)
SELECT
    CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR) || CAST(a.num AS VARCHAR) AS sesionID,
    DATE(a.fecha) AS fecha,
    a.deporte,
    a.tiempo,
    a.cals,
    a.FCavg,
    a.FCmax,
    a.por_Z1,
    a.por_Z2,
    a.por_Z3,
    a.por_Z4,
    a.por_Z5,
    (a.por_Z1 * 1 + a.por_Z2 * 2 + a.por_Z3 * 3 + a.por_Z4 * 4 + a.por_Z5 * 5) AS TRIMP
FROM {ORIGIN1} a
WHERE NOT EXISTS (
    SELECT 1
    FROM {DEST_TABLE} dest
    WHERE dest.sesionID = CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR) || CAST(a.num AS VARCHAR)
);
