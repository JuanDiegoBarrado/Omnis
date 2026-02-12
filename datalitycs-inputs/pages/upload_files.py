import streamlit as st
import boto3
import os
import pandas as pd
from io import StringIO, BytesIO
from botocore.exceptions import ClientError
import time

##### PREAMBLE ######
# MinIO client creation
MINIO_BUCKETS = ["files-test", "files-prep", "files-prod"]
MINIO_RAW_FILES_DIR = 'raw/new'

s3 = boto3.client(
    "s3",
    endpoint_url="http://datalitycs-storage:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="secret123",
    region_name="us-east-1",  # MinIO no valida región, pero boto3 lo requiere
)

for bucket in MINIO_BUCKETS:    
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        st.error(f"❌ Bucket named {bucket} doesn't exists")

# Unified function for saving a df in MinIO bucket
def saveDF(s3, bucket, path: str, data: pd.DataFrame) -> None:
    ext = path.split(".")[-1].lower()
    
    if ext == "csv":
        buffer = StringIO()
        data.to_csv(buffer, index=False, encoding="UTF-8")
    elif ext == "parquet":
        buffer = BytesIO()
        data.to_parquet(buffer, index=False)
    else:
        raise ValueError(f"Formato no soportado: {ext}")

    s3.put_object(Bucket=bucket, Key=path, Body=buffer.getvalue())

# Unified function for clearing csv registers after uploading them into MinIO
def clearCSV(csvpath):
    df = pd.read_csv(csvpath, nrows=0)
    df.to_csv(csvpath, index=False, encoding="UTF-8")

        
##### RENDERED CODE #####
# Page config
st.set_page_config(
    page_title="Datawarehouse-Salud inputs",  # Esto se verá en la pestaña del navegador
    page_icon="🖋️",
)

# Title visual
st.title("Datawarehouse Inputs 📓")

# Selectbox visual: csv file selection
data_dir = "./data"
csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv") and f != 'informacion_nutricional.csv']
selected_csv = st.selectbox("📂 Choose any CSV file to visualize it:", csv_files)

# Multiselect visual: MinIO bucket selection
st.multiselect("Select bucket:", MINIO_BUCKETS, default=MINIO_BUCKETS)

# Dataframe visual: selected csv visualization
csv_path = os.path.join(data_dir, selected_csv)
df = pd.read_csv(csv_path)
st.dataframe(df, use_container_width=True)

# Button visual: selected csv will be uploaded to MinIO
if st.button("📤 Upload selected CSV to MinIO"):
    try:
        timestamp = int(time.time())
        if len(df) > 0:
            filename, ext = selected_csv.split('.')
            filepath = f'{MINIO_RAW_FILES_DIR}/{filename}/{filename}_{timestamp}.{ext}'
            for bucket in MINIO_BUCKETS:
                saveDF(s3, bucket, filepath, df)
                st.success(f"✅ '{selected_csv}' uploaded correcto to MinIO: '{filepath}' and bucket: {bucket}. ({len(df)} rows)")
            clearCSV(csv_path)
            st.rerun()
        else:
            st.warning(f"⚠️ Selected CSV {selected_csv} is empty")
    except Exception as e:
        st.error(f"❌ Error while uploading '{selected_csv}' to MinIO: {e}")

# Button visual: all csvs will be uploaded to MinIO
if st.button("📦 Upload every CSV to MinIO"):
    try:
        timestamp = int(time.time())
        for file in csv_files:
            csv_path = os.path.join(data_dir, file)
            df = pd.read_csv(csv_path)
            if len(df) > 0:
                filename, ext = file.split('.')
                filepath = f'{MINIO_RAW_FILES_DIR}/{filename}/{filename}_{timestamp}.{ext}'
                for bucket in MINIO_BUCKETS:
                    saveDF(s3, bucket, filepath, df)
                    st.success(f"✅ '{selected_csv}' uploaded correcto to MinIO: '{filepath}' and bucket: {bucket}. ({len(df)} rows)")
                clearCSV(csv_path)
            else:
                st.warning(f"⚠️ Selected CSV {selected_csv} is empty")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error while uploading every csv to MinIO: {e}")
