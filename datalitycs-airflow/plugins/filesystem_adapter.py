from abc import ABC, abstractmethod
import boto3 as aws
import pandas as pd
from io import StringIO, BytesIO
import os
import glob
import numpy as np

def read_and_clean_csv(file):
    df = pd.read_csv(file)
    
    df = df.replace(["-", "", "#VALOR!", "#DIV/0!", "#N/A"], np.nan)
    df = df.dropna(how="any")
    
    return df

class StorageInterface(ABC):
    
    @abstractmethod
    def loadDF(self, path: str) -> pd.DataFrame:
        """Lee un archivo y devuelve su contenido en bytes"""
        pass

    @abstractmethod
    def saveDF(self, path: str, data: pd.DataFrame) -> None:
        """Escribe datos en un archivo"""
        pass
    
    @abstractmethod
    def deleteFile(self, path: str):
        pass

class LocalStorage(StorageInterface):
    def loadDF(self, path: str) -> pd.DataFrame:
        raise NotImplementedError()
        dirname = os.path.dirname(path)
        prefix, _ = os.path.splitext(os.path.basename(path))
        pattern = os.path.join(dirname, prefix)
        
        # list all files
        files = glob.glob(pattern)
        if not files:
            raise RuntimeError(f"No files found for pattern: {pattern}")
        else:
            # load and concat
            df_list = [pd.read_and_clean_csv(f) for f in files]
        
        return pd.concat(df_list)
    
    def saveDF(self, path: str, data: pd.DataFrame) -> None:
        raise NotImplementedError()
        data.to_csv(path, index=false)
            
    def deleteFile(self, path: str) -> None:
        raise NotImplementedError()
        for entry in os.listdir(path):
            fullPath = os.path.join(path, entry)
            
            if os.path.isfile(fullPath) and entry.lower().endswith(".csv"):
                os.remove(fullPath)
            else:
                pass

class S3Storage(StorageInterface):
    def __init__(self, service_name, endpoint_url, aws_access_key_id, aws_secret_access_key, bucket):
        self.s3 = aws.client(
            service_name=service_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.bucket = bucket

    def loadDF(self, path: str) -> pd.DataFrame:
        objetos = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=path)
        
        df_list = []
        for obj in objetos["Contents"]:
            key = obj["Key"]
            if key.endswith(".csv"):
                response = self.s3.get_object(Bucket=self.bucket, Key=key)
                csv_content = response["Body"].read().decode("utf-8")
                df = read_and_clean_csv(StringIO(csv_content))
                df_list.append(df)
        
        return pd.concat(df_list, ignore_index=True)

    def saveDF(self, path: str, data: pd.DataFrame) -> None:
        ext = path.split(".")[-1].lower()
        
        if ext == "csv":
            buffer = StringIO()
            data.to_csv(buffer, index=False)
        elif ext == "parquet":
            buffer = BytesIO()
            data.to_parquet(buffer, index=False)
        else:
            raise ValueError(f"Formato no soportado: {ext}")

        self.s3.put_object(Bucket=self.bucket, Key=path, Body=buffer.getvalue())
    
    def deleteFile(self, path) -> None:
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=path)
        if "Contents" in response:
            for obj in response["Contents"]:
                self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])