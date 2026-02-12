from airflow.sdk import task
from general_utilities import *

CLEAN_SOURCE_SCHEMA = 'orig'
CLEAN_DEST_SCHEMA = 'clean'
PARAMS_SET = {
    'series_gimnasio': {
        'ORIGINS': [f'{CLEAN_SOURCE_SCHEMA}.series_gimnasio'],
        'DESTINATION': f'{CLEAN_DEST_SCHEMA}.series_gimnasio',
        'QUERY_ETL_PATH': 'dags/ETLs/health/clean_series_gimnasio_ETL.sql',
        'ADDITIONAL_TABLES': ['orig.v_ejercicios_musculares']
    },
    'fatiga_muscular': {
        'ORIGINS': [f'{CLEAN_SOURCE_SCHEMA}.series_gimnasio'],
        'DESTINATION': f'{CLEAN_DEST_SCHEMA}.fatiga_muscular',
        'QUERY_ETL_PATH': 'dags/ETLs/health/clean_fatiga_muscular_ETL.sql',
        'ADDITIONAL_TABLES': ['orig.v_ejercicios_musculares']
    },
    'sesiones_carrera': {
        'ORIGINS': [f'{CLEAN_SOURCE_SCHEMA}.sesiones_carrera'],
        'DESTINATION': f'{CLEAN_DEST_SCHEMA}.sesiones_carrera',
        'QUERY_ETL_PATH': 'dags/ETLs/health/clean_sesiones_carrera_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_natacion': {
        'ORIGINS': [f'{CLEAN_SOURCE_SCHEMA}.sesiones_natacion'],
        'DESTINATION': f'{CLEAN_DEST_SCHEMA}.sesiones_natacion',
        'QUERY_ETL_PATH': 'dags/ETLs/health/clean_sesiones_natacion_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_extra': {
        'ORIGINS': [f'{CLEAN_SOURCE_SCHEMA}.sesiones_extra'],
        'DESTINATION': f'{CLEAN_DEST_SCHEMA}.sesiones_extra',
        'QUERY_ETL_PATH': 'dags/ETLs/health/clean_sesiones_extra_ETL.sql',
        'ADDITIONAL_TABLES': []
    }
}

@task(pool='duckdb_pool')
def clean_load(entity: str):
    """
    Load clean tables from orig tables info.
        - This task only fills a temporary table, when DAG completes correctly other task consolidates the results
    """
    rows_affected = execute_ETL(PARAMS_SET[entity])
    return rows_affected