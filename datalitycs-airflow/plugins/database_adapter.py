import duckdb
from duckdb import DuckDBPyConnection

def connect(database) -> DuckDBPyConnection:
    conn = duckdb.connect(database)
    
    conn.execute(
    """ INSTALL httpfs;
        LOAD httpfs;

        SET s3_endpoint='datalitycs-storage:9000';
        SET s3_url_style='path';
        SET s3_access_key_id='admin';
        SET s3_secret_access_key='secret123';
        SET s3_use_ssl=false;
    """
    )
    
    return conn