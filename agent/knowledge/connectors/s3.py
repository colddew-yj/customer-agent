"""
S3 connector：boto3 拉 S3 / R2 / MinIO / 阿里云 OSS（用 endpoint_url 切）。

yaml 示例：
  connector: s3
  connector_config:
    bucket: my-bucket
    prefix: docs/
    endpoint_url: https://s3.amazonaws.com
    aws_key_env: AWS_ACCESS_KEY_ID
    aws_secret_env: AWS_SECRET_ACCESS_KEY
    region: us-east-1
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


class S3Connector:
    def __init__(self, name: str, config: dict[str, Any], base: Path, cache_dir: Path):
        self.name = name
        self.config = config
        self.base = base
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.bucket = config.get("bucket")
        if not self.bucket:
            raise ValueError(f"s3 connector '{name}' 缺少 bucket")
        self.prefix = config.get("prefix", "").rstrip("/")
        self.endpoint_url = config.get("endpoint_url")
        self.region = config.get("region")
        self.aws_key_env = config.get("aws_key_env", "AWS_ACCESS_KEY_ID")
        self.aws_secret_env = config.get("aws_secret_env", "AWS_SECRET_ACCESS_KEY")

    def _client(self):
        try:
            import boto3
        except ImportError as e:
            raise RuntimeError("S3 connector 需要 boto3：pip install boto3") from e
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=os.environ.get(self.aws_key_env, ""),
            aws_secret_access_key=os.environ.get(self.aws_secret_env, ""),
        )

    def sync(self) -> Path:
        s3 = self._client()
        kwargs: dict[str, Any] = {"Bucket": self.bucket}
        if self.prefix:
            kwargs["Prefix"] = self.prefix + "/"

        downloaded = 0
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(**kwargs):
            for obj in page.get("Contents", []) or []:
                key = obj["Key"]
                rel = key[len(self.prefix) + 1:] if self.prefix else key
                if not rel or rel.endswith("/"):
                    continue
                target = self.cache_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(self.bucket, key, str(target))
                downloaded += 1

        print(f"[s3:{self.name}] downloaded {downloaded} files → {self.cache_dir}")
        return self.cache_dir

    def list_files(self) -> list[Path]:
        return sorted(p for p in self.cache_dir.glob("**/*") if p.is_file())

    def fetch(self, ref: str) -> bytes:
        return (self.cache_dir / ref).read_bytes()

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)