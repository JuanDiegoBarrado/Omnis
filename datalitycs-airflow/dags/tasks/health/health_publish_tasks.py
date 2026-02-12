from airflow.sdk import task
from general_utilities import *

PUBLISH_SOURCE_SCHEMA = 'clean'
PUBLISH_DEST_SCHEMA = 'publish'
PARAMS_SET = {
    'series_gimnasio': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.series_gimnasio'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.series_gimnasio',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_series_gimnasio_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'fatiga_muscular': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.fatiga_muscular'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.fatiga_muscular',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_fatiga_muscular_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_carrera': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.sesiones_carrera'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.sesiones_carrera',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_sesiones_carrera_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'sesiones_natacion': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.sesiones_natacion'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.sesiones_natacion',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_sesiones_natacion_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'fuerza': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.series_gimnasio'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.fuerza',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_fuerza_ETL.sql',
        'ADDITIONAL_TABLES': []
    },
    'cardio': {
        'ORIGINS': [f'{PUBLISH_SOURCE_SCHEMA}.sesiones_carrera'],
        'DESTINATION': f'{PUBLISH_DEST_SCHEMA}.cardio',
        'QUERY_ETL_PATH': 'dags/ETLs/health/publish_cardio_ETL.sql',
        'ADDITIONAL_TABLES': ['clean.sesiones_natacion', 'clean.sesiones_extra']
    }
}

@task(pool='duckdb_pool')
def publish_load(entity: str):
    """
    Load publish tables for final parquet files.
        - This task only fills a temporary table, when DAG completes correctly other task consolidates the results
    """
    rows_affected = execute_ETL(PARAMS_SET[entity])
    return rows_affected