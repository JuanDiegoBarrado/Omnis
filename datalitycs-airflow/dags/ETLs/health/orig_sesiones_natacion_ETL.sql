INSERT INTO {DEST_TABLE} (
    fecha, num, distancia, tiempo, cals, FCavg, FCmax,
    por_Z1, por_Z2, por_Z3, por_Z4, por_Z5
)
SELECT
    CAST(fecha as DATE) fecha,
    num,
    distancia,
    EXTRACT(HOUR FROM CAST(tiempo AS TIME)) * 60 +
    EXTRACT(MINUTE FROM CAST(tiempo AS TIME)) +
    EXTRACT(SECOND FROM CAST(tiempo AS TIME)) / 60.0 AS tiempo,
    cals,
    FCavg,
    FCmax,
    por_Z1 / NULLIF(por_Z1 + por_Z2 + por_Z3 + por_Z4 + por_Z5, 0) AS por_Z1,
    por_Z2 / NULLIF(por_Z1 + por_Z2 + por_Z3 + por_Z4 + por_Z5, 0) AS por_Z2,
    por_Z3 / NULLIF(por_Z1 + por_Z2 + por_Z3 + por_Z4 + por_Z5, 0) AS por_Z3,
    por_Z4 / NULLIF(por_Z1 + por_Z2 + por_Z3 + por_Z4 + por_Z5, 0) AS por_Z4,
    por_Z5 / NULLIF(por_Z1 + por_Z2 + por_Z3 + por_Z4 + por_Z5, 0) AS por_Z5
FROM {ORIGIN1} AS src
