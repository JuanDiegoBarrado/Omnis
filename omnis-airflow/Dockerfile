FROM apache/airflow:3.1.0
COPY requirements.txt .
RUN PYTHON_VERSION="$(python -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')" \
    && pip install --no-cache-dir \
        --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-${PYTHON_VERSION}.txt" \
        -r requirements.txt
