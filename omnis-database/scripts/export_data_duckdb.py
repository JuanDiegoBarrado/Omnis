import duckdb
import os
import argparse

parser = argparse.ArgumentParser(description="Exporta tablas de DuckDB a CSV")
parser.add_argument("--database", default="mi_base.duckdb", help="Ruta al archivo .duckdb")
args = parser.parse_args()

conn = duckdb.connect(args.database)

output_dir = "exported_tables"
os.makedirs(output_dir, exist_ok=True)

tables_df = conn.execute("select * from duckdb_tables();").df()[['schema_name', 'table_name']]
tables = list(tables_df.itertuples(index=False, name=None))

for (schema, table) in tables:
    output_path = os.path.join(output_dir, f"{schema}-{table}.csv")
    conn.execute(f"COPY {schema}.{table} TO '{output_path}' (HEADER, DELIMITER ',')")

conn.close()

print("Exportación completada.")