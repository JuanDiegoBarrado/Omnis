DELETE FROM {DEST_TABLE};

INSERT INTO {DEST_TABLE} (
    cardioID,
    semana_fecha,
    lunes_semana,
    tiempo_tot,
    tiempo_avg,
    cals_tot,
    cals_avg,
    FCavg,
    FCmax,
    por_Z1,
    por_Z2,
    por_Z3,
    por_Z4,
    por_Z5,
    TRIMP_tot,
    TRIMP_avg
)
SELECT
    CAST(STRFTIME(DATE(fecha), '%Y%W') AS VARCHAR) cardioID,
    EXTRACT(WEEK FROM DATE(fecha)) semana_fecha,
    DATE_TRUNC('WEEK', fecha + INTERVAL (1 - EXTRACT(ISODOW FROM fecha)) DAY) lunes_semana,
    sum(tiempo) tiempo_tot,
    avg(tiempo) tiempo_avg,
    sum(cals) cals_tot,
    avg(cals) cals_avg,
    (sum(FCavg * tiempo) / nullif(sum(tiempo), 0)) FCavg,
    max(FCmax) FCmax,
    (sum(por_Z1 * tiempo) / nullif(sum(tiempo), 0)) por_Z1,
    (sum(por_Z2 * tiempo) / nullif(sum(tiempo), 0)) por_Z2,
    (sum(por_Z3 * tiempo) / nullif(sum(tiempo), 0)) por_Z3,
    (sum(por_Z4 * tiempo) / nullif(sum(tiempo), 0)) por_Z4,
    (sum(por_Z5 * tiempo) / nullif(sum(tiempo), 0)) por_Z5,
    sum(TRIMP) TRIMP_tot,
    (sum(TRIMP * tiempo) / nullif(sum(tiempo), 0)) TRIMP_avg
FROM (
	select fecha, tiempo, cals, FCavg, FCmax, por_Z1, por_Z2, por_Z3, por_Z4, por_Z5, TRIMP  from {ORIGIN1}
	UNION
	select fecha, tiempo, cals, FCavg, FCmax, por_Z1, por_Z2, por_Z3, por_Z4, por_Z5, TRIMP  from {ADDITIONAL1}
	UNION
	select fecha, tiempo, cals, FCavg, FCmax, por_Z1, por_Z2, por_Z3, por_Z4, por_Z5, TRIMP  from {ADDITIONAL2}
)
GROUP BY cardioID, semana_fecha, lunes_semana