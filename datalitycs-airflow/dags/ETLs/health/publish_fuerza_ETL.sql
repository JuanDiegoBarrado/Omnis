DELETE FROM {DEST_TABLE};

INSERT INTO {DEST_TABLE} (
    fuerzaID,
    semana_fecha,
    lunes_semana,
    tonelaje,
    por_RM_avg,
    RIR_avg,
    RPE_avg,
    SI_avg,
    SI_tot
)
SELECT
	CAST(STRFTIME(DATE(fecha), '%Y%W') AS VARCHAR) fuerzaID,
    EXTRACT(WEEK FROM DATE(fecha)) semana_fecha,
    DATE_TRUNC('WEEK', fecha + INTERVAL (1 - EXTRACT(ISODOW FROM fecha)) DAY) lunes_semana,
    sum(peso * reps) tonelaje,
    avg(por_RM) por_RM_avg,
    avg(RIR) RIR_avg,
    avg(RPE) RPE_avg,
    avg(SI) SI_avg,
    sum(SI) SI_tot
FROM {ORIGIN1}
GROUP BY fuerzaID, semana_fecha, lunes_semana;