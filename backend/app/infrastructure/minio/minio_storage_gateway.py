from __future__ import annotations

import os
from io import BytesIO

from minio import Minio


class MinioStorageGateway:
    def __init__(self) -> None:
        endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
        self._bucket_raw = os.getenv("MINIO_BUCKET_RAW", "trade-raw")
        self._bucket_rendered = os.getenv("MINIO_BUCKET_RENDERED", "trade-rendered")
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=use_ssl)

    def upload_raw(self, object_key: str, content: bytes, content_type: str) -> str:
        return self._upload(self._bucket_raw, object_key, content, content_type)

    def upload_rendered(self, object_key: str, content: bytes, content_type: str = "image/png") -> str:
        return self._upload(self._bucket_rendered, object_key, content, content_type)

    def _upload(self, bucket_name: str, object_key: str, content: bytes, content_type: str) -> str:
        data = BytesIO(content)
        self._client.put_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=data,
            length=len(content),
            content_type=content_type,
        )
        return f"{bucket_name}/{object_key}"

    def presigned_get_url(self, object_ref: str, expires_seconds: int = 3600) -> str:
        if "/" not in object_ref:
            raise ValueError("object_ref must be '<bucket>/<object_key>' format")
        bucket, object_key = object_ref.split("/", 1)
        return self._client.presigned_get_object(bucket, object_key, expires=expires_seconds)
