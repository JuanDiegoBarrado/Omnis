import duckdb
import os
from duckdb import DuckDBPyConnection

def connect(database) -> DuckDBPyConnection:
    conn = duckdb.connect(database)
    
    conn.execute(
    f""" INSTALL httpfs;
        LOAD httpfs;

        SET s3_endpoint='{os.getenv('MINIO_ENDPOINT')}';
        SET s3_url_style='path';
        SET s3_access_key_id='{os.getenv('MINIO_ROOT_USER')}';
        SET s3_secret_access_key='{os.getenv('MINIO_ROOT_PASSWORD')}';
        SET s3_use_ssl=false;
    """
    )
    
    return conn