from airflow.sdk import task
from general_utilities import *
import filesystem_adapter as fls
import pandas as pd
import logging
from config_helper import load_environment_config

logger = logging.getLogger(__name__)

ORIG_SOURCE_SCHEMA = 'raw'
ORIG_DEST_SCHEMA = 'orig'
PARAMS_SET = {
    'series_gimnasio': {
        'ORIGINS': [f'{ORIG_SOURCE_SCHEMA}.v_series_gimnasio_new'],
        'DESTINATION': f'{ORIG_DEST_SCHEMA}.series_gimnasio',
        'QUERY_ETL_PATH': 'dags/ETLs/health/orig_series_gimnasio_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_carrera': {
        'ORIGINS': [f'{ORIG_SOURCE_SCHEMA}.v_sesiones_carrera_new'],
        'DESTINATION': f'{ORIG_DEST_SCHEMA}.sesiones_carrera',
        'QUERY_ETL_PATH': 'dags/ETLs/health/orig_sesiones_carrera_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_natacion': {
        'ORIGINS': [f'{ORIG_SOURCE_SCHEMA}.v_sesiones_natacion_new'],
        'DESTINATION': f'{ORIG_DEST_SCHEMA}.sesiones_natacion',
        'QUERY_ETL_PATH': 'dags/ETLs/health/orig_sesiones_natacion_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_extra': {
        'ORIGINS': [f'{ORIG_SOURCE_SCHEMA}.v_sesiones_extra_new'],
        'DESTINATION': f'{ORIG_DEST_SCHEMA}.sesiones_extra',
        'QUERY_ETL_PATH': 'dags/ETLs/health/orig_sesiones_extra_ETL.sql',
        'ADDITIONAL_TABLES': []
    }
}
    
@task(pool='duckdb_pool')
def orig_load(entity: str):
    """
    Load orig tables from raw files info.
        - This task only fills a temporary table, when DAG completes correctly other task consolidates the results
    """
    rows_affected = execute_ETL(PARAMS_SET[entity])
    return rows_affected


@task.branch
def branch_clean_staging(task: str):
    runtime_context = get_current_context()
    
    if runtime_context['params']['clear staging']: # pyright: ignore[reportTypedDictNotRequiredAccess]
        return task

@task()
def orig_save_in_his(entity: str):
    """
    Saves data from staging csv files to historical files
    """
    runtime_context = get_current_context()
    ENVIRONMENT_CONFIG = load_environment_config()
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    filemanager = fls.S3Storage(**env['storage_bucket_config'], bucket=env['storage_bucket_name'])
    logger.info(f"Filemanager bucket: {env['storage_bucket_name']}")
    
    newFilePath = f'raw/new/{entity}/{entity}_'
    hisFilePath = f'raw/his/{entity}/{entity}_his.csv'
    logger.info(f'Writting on {hisFilePath} from {newFilePath}*.csv')
    
    df_new = filemanager.loadDF(newFilePath)
    try:
        df_his = filemanager.loadDF(hisFilePath)
    except:
        df_his = pd.DataFrame(columns=df_new.columns)
    new_df_his = pd.concat([df_new, df_his], ignore_index=True).drop_duplicates()
    
    logger.info(f'New lines: {len(df_new) if df_new is not None else 0}')
    logger.info(f'Historical lines: {len(df_his)}')
    logger.info(f'Total lines: {len(new_df_his)}')
    
    filemanager.saveDF(hisFilePath, new_df_his)
    
@task()
def orig_restore_staging(entity: str):
    """
    Erases staging files when fully processed
    """
    runtime_context = get_current_context()
    ENVIRONMENT_CONFIG = load_environment_config()
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    filemanager = fls.S3Storage(**env['storage_bucket_config'], bucket=env['storage_bucket_name'])
    logger.info(f"Filemanager bucket: {env['storage_bucket_name']}")
    
    STAGING_PATH = f'raw/new/{entity}'
    PERSISTENT_STAGING_PATH = f"{STAGING_PATH}/{entity}_new.csv"
    
    persistent_staging = filemanager.loadDF(PERSISTENT_STAGING_PATH)    
    filemanager.deleteFile(STAGING_PATH)
    filemanager.saveDF(PERSISTENT_STAGING_PATH, persistent_staging)    