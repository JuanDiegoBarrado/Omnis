import duckdb
import os

SQL_FILE = './database/init/db_config.sql'
DATABASES = [('prod', os.getenv('DUCKDB_PROD')), ('prep', os.getenv('DUCKDB_PREP')), ('test', os.getenv('DUCKDB_TEST'))]
with open(SQL_FILE, 'r', encoding='utf-8') as f:
    init_querys = f.read()
    

for (env, db) in DATABASES:
    if os.path.exists(f'./database/{db}'):
        continue

    print(f'Conecting to: {db}')
    con = duckdb.connect(f'./database/{db}')

    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    print(f"S3 endpoint is: {os.getenv('MINIO_ENDPOINT')}")
    con.execute(f"SET s3_endpoint='{os.getenv('MINIO_ENDPOINT')}';")
    con.execute("SET s3_url_style='path';")
    print(f"S3 access key is: {os.getenv('MINIO_ROOT_USER')}")
    con.execute(f"SET s3_access_key_id='{os.getenv('MINIO_ROOT_USER')}';")
    print(f"S3 secret access key is: {os.getenv('MINIO_ROOT_PASSWORD')}")
    con.execute(f"SET s3_secret_access_key='{os.getenv('MINIO_ROOT_PASSWORD')}';")
    con.execute("SET s3_use_ssl=false;")
    con.execute("SET s3_region='eu-west-1';")


    querys = init_querys.replace('files-prod', f'files-{env}')
    con.execute(querys)
    
    con.close()