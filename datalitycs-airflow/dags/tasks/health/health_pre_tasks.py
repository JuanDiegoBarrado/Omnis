from airflow.sdk import task, get_current_context
from general_utilities import *
import database_adapter as db
import logging
from config_helper import load_environment_config

logger = logging.getLogger()        # Internal logger for debugging and execution info

@task(pool='duckdb_pool')           # Take the writter lock for concurrency in db
def pre_load_tmp_tables():
    """
    Copy regular tables onto its temp version
    """
    runtime_context = get_current_context()
    ENVIRONMENT_CONFIG = load_environment_config()
    logger.info(f"DEBUG: este es el entorno {ENVIRONMENT_CONFIG}")
    logger.info(f"patata")
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    
    QUERY_DISCOVER_TMPS = 'dags/ETLs/health/pre_get_tmp_tables_ETL.sql'
    QUERY_LOAD_TMP = 'dags/ETLs/health/pre_load_tmp_table.sql'
    DATABASE = env['db_conn']
    
    # Load querys
    logger.info(f"FILESYSTEM: Reading query from {QUERY_DISCOVER_TMPS}")
    with open(QUERY_DISCOVER_TMPS, "r", encoding="utf-8") as f:
        discover_tmps_query = f.read()
    logger.info(f"FILESYSTEM: Reading query from {QUERY_LOAD_TMP}")
    with open(QUERY_LOAD_TMP, "r", encoding="utf-8") as f:
        load_a_tmp_table_query = f.read()
    
    # Start database connection
    logger.info(f"SQL: Connecting to {DATABASE} database")
    conn = db.connect(DATABASE)    
    
    # Load tmp tables names and schemas
    logger.info(f'SQL: Executed query:\n{discover_tmps_query}')
    temporary_tables = conn.execute(discover_tmps_query).fetch_df()
    
    # Traverse tmp tables loading its persistent table information
    logger.info(f'INFO: Temporary tables:\n{temporary_tables}')    
    for _, tmp in temporary_tables.iterrows():
        schema = tmp['table_schema']
        
        tmp_table = tmp['table_name']
        perst_table = tmp_table.removesuffix('_tmp')
        
        tmp_dest = f"{schema}.{tmp['table_name']}"
        perst_source = f'{schema}.{perst_table}'
        
        effective_load_query = load_a_tmp_table_query.format(DEST_TABLE=tmp_dest, ORIGIN1=perst_source)
        logger.info(f'SQL: Executed query:\n{effective_load_query}')
        conn.execute(effective_load_query)
    
    # Close database connection
    conn.close()
    logger.info(f"SQL: Closing connection to {DATABASE} database")