INSERT INTO {DEST_TABLE} (
    serieID,
    fecha,
    ejercicio,
    categoria,
    peso,
    por_RM,
    reps,
    RIR,
    RPE,
    RM,
    SI
)
SELECT
    CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR) || lpad(CAST(a.num AS VARCHAR), 2, '0') AS serieID,
    DATE(a.fecha) AS fecha,
    a.ejercicio as ejercicio,
    b.categoria as categoria,
    a.peso as peso,
    (a.peso / (a.peso / (1.0278 - (0.0278 * (a.reps + a.RIR))))) AS por_RM,
    a.reps as reps,
    a.RIR as RIR,
    a.RPE as RPE,
    (a.peso / (1.0278 - (0.0278 * (a.reps + a.RIR)))) AS RM,
    CASE
        WHEN a.RPE = 6 THEN 0.6
        WHEN a.RPE = 6.5 THEN 0.7
        WHEN a.RPE = 7 THEN 0.8
        WHEN a.RPE = 7.5 THEN 0.9
        WHEN a.RPE = 8 THEN 1.0
        WHEN a.RPE = 8.5 THEN 1.1
        WHEN a.RPE = 9 THEN 1.2
        WHEN a.RPE = 9.5 THEN 1.4
        WHEN a.RPE = 10 THEN 1.6
        ELSE 0
    END AS SI
FROM {ORIGIN1} a
LEFT JOIN {ADDITIONAL1} b ON a.ejercicio = b.ejercicio
WHERE NOT EXISTS (
    SELECT 1
    FROM {DEST_TABLE} dest
    WHERE dest.serieID = CAST(STRFTIME(DATE(a.fecha), '%Y%m%d') AS VARCHAR) || lpad(CAST(a.num AS VARCHAR), 2, '0')
);