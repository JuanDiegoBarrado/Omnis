SELECT CAST(id AS INTEGER) AS id, CAST(fecha AS DATE) AS fecha, CAST(peso AS FLOAT) AS peso,
       source_file AS sys_source_file
FROM src.origin
