import os
from typing import Dict, Any

def get_env_config(environment: str) -> Dict[str, Any]:
    valid_envs = ['TEST', 'PREP', 'PROD']
    
    if environment not in valid_envs:
        raise ValueError(
            f"Environment '{environment}' no válido. "
            f"Debe ser uno de: {', '.join(valid_envs)}"
        )
    
    # Leer variables de entorno
    minio_endpoint = os.getenv('MINIO_ENDPOINT')
    minio_access_key = os.getenv('MINIO_ROOT_USER')
    minio_secret_key = os.getenv('MINIO_ROOT_PASSWORD')
    env_mapping = {
        'TEST': {
            'db_conn': os.getenv('DUCKDB_TEST'),
            'bucket': os.getenv('MINIO_BUCKET_TEST'),
        },
        'PREP': {
            'db_conn': os.getenv('DUCKDB_PREP'),
            'bucket': os.getenv('MINIO_BUCKET_PREP'),
        },
        'PROD': {
            'db_conn': os.getenv('DUCKDB_PROD'),
            'bucket': os.getenv('MINIO_BUCKET_PROD'),
        }
    }
    env_data = env_mapping[environment]
    
    # Construir configuración completa
    config = {
        'db_conn': env_data['db_conn'],
        'storage_bucket_name': env_data['bucket'],
        'storage_bucket_config': {
            'service_name': 's3',
            'endpoint_url': f'http://{minio_endpoint}',
            'aws_access_key_id': minio_access_key,
            'aws_secret_access_key': minio_secret_key,
        }
    }
    
    return config


def load_environment_config() -> Dict[str, Dict[str, Any]]:
    return {
        'TEST': get_env_config('TEST'),
        'PREP': get_env_config('PREP'),
        'PROD': get_env_config('PROD'),
    }