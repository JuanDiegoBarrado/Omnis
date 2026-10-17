import argparse
import csv
import os
import sys
import psycopg2
from psycopg2 import sql


def parse_args():
    parser = argparse.ArgumentParser(description="Importa CSVs a PostgreSQL")
    parser.add_argument("--folder",   required=True, help="Carpeta con los archivos CSV")
    parser.add_argument("--host",     required=True, help="Host de PostgreSQL")
    parser.add_argument("--port",     default="5432", help="Puerto de PostgreSQL (default: 5432)")
    parser.add_argument("--database", required=True, help="Nombre de la base de datos")
    parser.add_argument("--user",     required=True, help="Usuario de PostgreSQL")
    parser.add_argument("--password", required=True, help="Contraseña de PostgreSQL")
    parser.add_argument("--delimiter", default=",", help="Delimitador del CSV (default: ,)")
    return parser.parse_args()


def get_csv_files(folder):
    """Devuelve lista de rutas de archivos CSV cuyo nombre sigue el patrón esquema-tabla.csv"""
    files = []
    for filename in os.listdir(folder):
        if not filename.lower().endswith(".csv"):
            continue
        name = filename[:-4]  # quitar .csv
        parts = name.split("-", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            print(f"[WARN] Archivo ignorado (nombre no sigue 'esquema-tabla'): {filename}")
            continue
        schema, table = parts
        files.append((os.path.join(folder, filename), schema, table))
    return files


def create_table_if_not_exists(cursor, schema, table, columns):
    """Crea el esquema y la tabla si no existen, con todas las columnas como TEXT."""
    cursor.execute(
        sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
    )
    col_defs = sql.SQL(", ").join(
        sql.SQL("{} TEXT").format(sql.Identifier(col)) for col in columns
    )
    cursor.execute(
        sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} ({})").format(
            sql.Identifier(schema),
            sql.Identifier(table),
            col_defs,
        )
    )


def insert_rows(cursor, schema, table, columns, rows):
    """Inserta filas en la tabla usando executemany."""
    col_identifiers = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(columns))
    query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        col_identifiers,
        placeholders,
    )
    cursor.executemany(query, rows)


def process_csv(conn, filepath, schema, table, delimiter):
    print(f"\n→ Procesando: {os.path.basename(filepath)}  →  {schema}.{table}")
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        columns = reader.fieldnames
        if not columns:
            print("  [WARN] CSV vacío o sin cabecera, omitiendo.")
            return
        rows = [tuple(row[c] for c in columns) for row in reader]

    with conn.cursor() as cur:
        create_table_if_not_exists(cur, schema, table, columns)
        insert_rows(cur, schema, table, columns, rows)
        conn.commit()
        print(f"  [OK] {len(rows)} filas insertadas.")


def main():
    args = parse_args()

    csv_files = get_csv_files(args.folder)
    
    print(f"Conectando a {args.host}:{args.port}/{args.database} como {args.user}...")
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.database,
        user=args.user,
        password=args.password,
    )

    print(f"Conexión establecida. {len(csv_files)} archivo(s) a procesar.\n")

    for filepath, schema, table in csv_files:
        process_csv(conn, filepath, schema, table, args.delimiter)

    conn.close()


if __name__ == "__main__":
    main()