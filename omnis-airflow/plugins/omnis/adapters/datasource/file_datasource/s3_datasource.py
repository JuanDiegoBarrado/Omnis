import boto3
from botocore.exceptions import ClientError

from omnis.ports import FileDataSource


class S3DataSource(FileDataSource):
    """FileDataSource over a bucket of an S3-compatible storage (AWS S3, MinIO...)."""

    def __init__(self, service_name, endpoint_url, aws_access_key_id, aws_secret_access_key, bucket):
        self._client_arguments = {
            "service_name": service_name,
            "endpoint_url": endpoint_url,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }
        self._client = None
        self._bucket = bucket

    @property
    def _s3(self):
        # Built on first use: DAG files build their adapters every time they are parsed
        if self._client is None:
            self._client = boto3.client(**self._client_arguments)
        return self._client

    def list_files(self, prefix: str) -> list[str]:
        paginator = self._s3.get_paginator("list_objects_v2")
        return [
            obj["Key"]
            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if not obj["Key"].endswith("/")
        ]

    def exists(self, path: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=path)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def read_file(self, path: str) -> bytes:
        response = self._s3.get_object(Bucket=self._bucket, Key=path)
        return response["Body"].read()

    def move_file(self, path: str, new_path: str) -> None:
        # S3 has no move: copy, then delete the original
        self._s3.copy_object(Bucket=self._bucket, Key=new_path, CopySource={"Bucket": self._bucket, "Key": path})
        self._s3.delete_object(Bucket=self._bucket, Key=path)
