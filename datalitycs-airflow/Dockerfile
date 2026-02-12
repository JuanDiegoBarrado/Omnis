FROM apache/airflow:3.1.0
COPY requirements.txt .
RUN pip install --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.11.txt" -r requirements.txt
