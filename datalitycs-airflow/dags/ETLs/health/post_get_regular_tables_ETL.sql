SELECT DISTINCT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE' and table_name not like '%_tmp'
order by 1, 2;