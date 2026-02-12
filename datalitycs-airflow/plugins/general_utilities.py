from airflow.sdk import task, get_current_context
import database_adapter as db
import yaml
import logging
from config_helper import load_environment_config

def __decide_if_tmp__(entity_name: str, persistent: bool):
    schema, table = entity_name.split('.', 1)
    if persistent or schema=='publish' or table.startswith('v_'):
        return entity_name
    else:
        return f'{entity_name}_tmp'
    

def execute_ETL(substitutions: dict, persistent: bool = False):
    """
    Execute a parametrized SQL statement given a particular configuration.
        - This task only fills a temporary table, when DAG completes correctly other task consolidates the results
    """
    runtime_context = get_current_context()
    ENVIRONMENT_CONFIG = load_environment_config()
    env = ENVIRONMENT_CONFIG[runtime_context['params']['environment']] # pyright: ignore[reportTypedDictNotRequiredAccess]
    DATABASE = env['db_conn']
    
    # Start logger for execution info
    logger = logging.getLogger(__name__)
    
    # Start database connection
    logger.info(f"SQL: Connecting to {DATABASE} database")
    conn = db.connect(DATABASE)
    
    # Pre-ETL
    # TODO: Not implemented
    
    # ETL
    # Reading query statement
    logger.info(f"FILESYSTEM: Reading query from {substitutions['QUERY_ETL_PATH']}")
    with open(substitutions['QUERY_ETL_PATH'], "r", encoding="utf-8") as f:
        query = f.read()
    
    # Perform sources and destination substitution given the specified parameters
    subs = {'DEST_TABLE': __decide_if_tmp__(substitutions['DESTINATION'], persistent)}
    for i, origin_table in enumerate(substitutions['ORIGINS']):
        subs[f'ORIGIN{i+1}'] = __decide_if_tmp__(origin_table, persistent)
    for i, ad_table in enumerate(substitutions['ADDITIONAL_TABLES']):
        subs[f'ADDITIONAL{i+1}'] = __decide_if_tmp__(ad_table, persistent)
    query = query.format(**subs)
    
    # Execute query
    logger.info(f'SQL: Executed query:\n{query}')
    result = conn.execute(query)
    
    # Post-ETL
    # TODO: Not implemented

    # Close connection to database
    conn.close()
    logger.info(f"SQL: Closing connection to {DATABASE} database")
    
    return result.rowcount
    
def build_dependencies(tasks, graph_filepath):
    """
    Generate main tasks dependencies from a yaml graph specification.
    """
    # Load YAML
    with open(graph_filepath, 'r') as f:
        dependencies = yaml.safe_load(f)
    
    for task_name, prereqs in dependencies.items():
        if task_name not in tasks:
            raise ValueError(f"Task '{task_name}' not found in tasks list")
        elif not prereqs:
            continue
        else:
            for prereq_name in prereqs:
                if prereq_name not in tasks:
                    raise ValueError(f"Pretask '{prereq_name}' of task {task_name} not found in list")
                else:
                    tasks[prereq_name] >> tasks[task_name] # pyright: ignore[reportUnusedExpression]