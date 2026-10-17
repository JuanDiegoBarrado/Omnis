import psycopg2
import os
import argparse

parser = argparse.ArgumentParser(description="Exporta tablas de PostgreSQL a CSV")
parser.add_argument("--host",     default="localhost",        help="Host de la base de datos")
parser.add_argument("--database", default="tu_base_de_datos", help="Nombre de la base de datos")
parser.add_argument("--user",     default="tu_usuario",       help="Usuario")
parser.add_argument("--password", default="tu_password",      help="Contraseña")
args = parser.parse_args()

conn = psycopg2.connect(
    host=args.host,
    database=args.database,
    user=args.user,
    password=args.password
)

output_dir = "exported_tables"
os.makedirs(output_dir, exist_ok=True)

cur = conn.cursor()

cur.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public';
""")

tables = cur.fetchall()

for table in tables:
    table_name = table[0]
    with open(os.path.join(output_dir, f"{table_name}.csv"), "w", encoding="utf-8") as f:
        cur.copy_expert(f"COPY {table_name} TO STDOUT WITH CSV HEADER", f)

cur.close()
conn.close()

print("Exportación completada.")