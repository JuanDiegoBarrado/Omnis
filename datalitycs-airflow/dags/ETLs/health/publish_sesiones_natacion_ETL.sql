DELETE FROM {DEST_TABLE};

INSERT INTO {DEST_TABLE} (
    sesionID,
    fecha,
    distancia,
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
    sesionID,
    fecha,
    distancia,
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
FROM {ORIGIN1} a;
