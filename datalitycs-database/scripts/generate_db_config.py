import duckdb

SCHEMAS = ['raw', 'origin', 'clean', 'publish']
db_original = 'datalitycs-database/database-prod.duckdb'
archivo_sql = 'db_config.sql'

con = duckdb.connect(database=db_original, read_only=True)
tablas = [(schema, tabla[0], tabla[1]) for schema in SCHEMAS for tabla in con.execute(f"SELECT table_name, sql FROM duckdb_tables() WHERE schema_name='{schema}';").fetchall()]
vistas = [(schema, vista[0], vista[1]) for schema in SCHEMAS for vista in con.execute(f"SELECT view_name, sql FROM duckdb_views() WHERE schema_name='{schema}';").fetchall()]

with open(archivo_sql, 'w', encoding='utf-8') as f:
    for schema in SCHEMAS:
        f.write(f'create schema {schema};' + '\n\n')
    
    for schema, objeto, sql in tablas + vistas:
        f.write(sql + ';\n\n')

con.close()
