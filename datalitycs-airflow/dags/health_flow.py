from airflow.sdk import dag, Param
from tasks.health.health_orig_tasks import *
from tasks.health.health_clean_tasks import *
from tasks.health.health_publish_tasks import *
from tasks.health.health_post_tasks import *
from tasks.health.health_pre_tasks import *
from general_utilities import build_dependencies

@dag(
    schedule=None,
    start_date=None,
    catchup=False,
    tags=["test"],
    params= {
        "environment": Param("PROD", enum=["TEST", "PREP", "PROD"], type="string"),
        "clear staging": Param(True, type="boolean"),
        # "consolidate changes": Param(True, type="boolean")
    }
)
def health_flow():
    """
    Health data pipeline
    """
    TASKS = {}
    ORIG_ENTITIES = ['series_gimnasio', 'sesiones_carrera']
    CLEAN_ENTITIES = ['series_gimnasio', 'fatiga_muscular', 'sesiones_carrera']
    PUBLISH_ENTITIES = ['series_gimnasio', 'fatiga_muscular', 'sesiones_carrera']
    
    # Tasks definitions
    # Pre
    TASKS['pre_load_tmps'] = pre_load_tmp_tables()
    
    # Post
    TASKS['post_consolidate_changes'] = post_make_changes_persistent()
    TASKS['post_save_parquets'] = post_save_db_parquets()
    
    # Orig
    for entity in ORIG_ENTITIES:
        TASKS[f'orig_load_{entity}'] = orig_load.override(task_id=f'orig_load_{entity}')(entity)
        TASKS[f'orig_restore_staging_{entity}'] = orig_restore_staging.override(task_id=f'orig_restore_staging_{entity}')(entity)
        TASKS[f'orig_save_in_his_{entity}'] = orig_save_in_his.override(task_id=f'orig_save_in_his_{entity}')(entity)
        TASKS[f'orig_branch_clean_staging_{entity}'] = branch_clean_staging.override(task_id=f'orig_branch_clean_staging_{entity}')(task=f'orig_save_in_his_{entity}')
        
        TASKS['post_consolidate_changes'] >> TASKS[f'orig_branch_clean_staging_{entity}'] >> TASKS[f'orig_save_in_his_{entity}'] >> TASKS[f'orig_restore_staging_{entity}'] # pyright: ignore[reportUnusedExpression]
    
    # Clean
    for entity in CLEAN_ENTITIES:
        TASKS[f'clean_load_{entity}'] = clean_load.override(task_id=f'clean_load_{entity}')(entity)

    # Publish
    for entity in PUBLISH_ENTITIES:
        TASKS[f'publish_{entity}'] = publish_load.override(task_id=f'publish_load_{entity}')(entity)

    # Task dependencies
    build_dependencies(TASKS, 'dags/graphs/health_graph.yaml')

health_flow()