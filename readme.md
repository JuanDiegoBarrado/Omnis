docker-compose --profile airflow start
docker-compose --profile airflow stop
docker-compose --profile airflow restart

pip install apache-airflow==3.1.0 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.11.txt"