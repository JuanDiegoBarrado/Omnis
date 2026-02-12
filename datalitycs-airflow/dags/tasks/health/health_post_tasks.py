from airflow.sdk import task, get_current_context
from general_utilities import *
import filesystem_adapter as fls
import database_adapter as db
import logging
from io import BytesIO, StringIO
from config_helper import load_environment_config

logger = logging.getLogger()

@task(pool='duckdb_pool')
def post_make_changes_persistent():
    """
    Consolidate every tmp table to its persistent one
    """
    runtime_context = get_current_context()

    ENVIRONMENT_CONFIG = load_environment_config()
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    
    QUERY_DISCOVER_TMPS = 'dags/ETLs/health/post_get_tmp_tables_ETL.sql'
    QUERY_CONSOLIDATE_TMPS = 'dags/ETLs/health/post_consolidate_tmp_ETL.sql'
    DATABASE = env['db_conn']
    
    # Load querys
    logger.info(f"FILESYSTEM: Reading query from {QUERY_DISCOVER_TMPS}")
    with open(QUERY_DISCOVER_TMPS, "r", encoding="utf-8") as f:
        load_query = f.read()
    logger.info(f"FILESYSTEM: Reading query from {QUERY_CONSOLIDATE_TMPS}")
    with open(QUERY_CONSOLIDATE_TMPS, "r", encoding="utf-8") as f:
        consolidate_query = f.read()     
    
    # Start database connection
    logger.info(f"SQL: Connecting to {DATABASE} database")
    conn = db.connect(DATABASE)    
    
    # Load tmp tables names and schemas
    logger.info(f'SQL: Executed query:\n{load_query}')
    temporary_tables = conn.execute(load_query).fetch_df()
    
    # Traverse tmp tables loading its persistent table information
    logger.info(f'INFO: Temporary tables:\n{temporary_tables}')    
    for _, tmp in temporary_tables.iterrows():
        schema = tmp['table_schema']
        
        tmp_table = tmp['table_name']
        table = tmp_table.removesuffix('_tmp')
        
        temp_source = f"{schema}.{tmp['table_name']}"
        perst_dest = f'{schema}.{table}'
        
        effective_consolidate_query = consolidate_query.format(DEST_TABLE=perst_dest, ORIGIN1=temp_source)
        logger.info(f'SQL: Executed query:\n{effective_consolidate_query}')
        conn.execute(effective_consolidate_query)
    
    # Close database connection
    conn.close()
    logger.info(f"SQL: Closing connection to {DATABASE} database")
    
@task(pool='duckdb_pool')
def post_save_db_parquets():
    """
    Save every regular table info as a parquet file
    """
    runtime_context = get_current_context()
    ENVIRONMENT_CONFIG = load_environment_config()
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    filemanager = fls.S3Storage(**env['storage_bucket_config'], bucket=env['storage_bucket_name'])
    logger.info(f'Filemanager bucket: {env['storage_bucket_name']}') # pyright: ignore[reportGeneralTypeIssues]
    
    QUERY_LOAD_REGULARS = 'dags/ETLs/health/post_get_regular_tables_ETL.sql'
    DATABASE = env['db_conn']
    
    # Load querys
    logger.info(f"FILESYSTEM: Reading query from {QUERY_LOAD_REGULARS}")
    with open(QUERY_LOAD_REGULARS, "r", encoding="utf-8") as f:
        load_query = f.read()
    
    # Start database connection
    logger.info(f"SQL: Connecting to {DATABASE} database")
    conn = db.connect(DATABASE)
    
    # Execute query
    logger.info(f'Executed query:\n{load_query}')
    regular_tables = conn.execute(load_query).df()    
    
    # Close database connection
    conn.close()
    logger.info(f"SQL: Closing connection to {DATABASE} database")
    
    # Traverse regular tables saving its content as a parquet file
    logger.info(f'Regular tables:\n{regular_tables}')
    for _, tmp in regular_tables.iterrows():
        schema = tmp['table_schema']
        reg_table = tmp['table_name']
        filepath = f'{schema}/{schema}_{reg_table}.parquet'
        
        query_load_table_data = f'select * from {schema}.{reg_table}'
        
        # Load table data
        logger.info(f"SQL: Connecting to {DATABASE} database")
        conn = db.connect(DATABASE)
        
        logger.info(f'Executed query:\n{query_load_table_data}')
        df = conn.execute(query_load_table_data).df()
        
        conn.close()
        logger.info(f"SQL: Closing connection to {DATABASE} database")
        
        # Save table data
        logger.info(f"Writting source {schema}.{reg_table} into {filepath}")
        filemanager.saveDF(filepath, df)