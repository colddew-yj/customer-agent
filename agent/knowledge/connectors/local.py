"""
Local connector：直接读业务方本地的 path 目录（V1 默认行为）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class LocalConnector:
    def __init__(self, name: str, config: dict[str, Any], base: Path, cache_dir: Path, source_path: str | None = None):
        """source_path: 直接传 KnowledgeSourceConfig.path（避免要求 connector_config.path）。"""
        self.name = name
        self.config = config
        self.base = base
        self.cache_dir = cache_dir
        path = source_path or config.get("path")
        if not path:
            raise ValueError(
                f"local connector '{name}' 缺少 path 配置（yaml source.path 或 connector_config.path）"
            )
        self.path = (base / path).resolve()

    def sync(self) -> Path:
        return self.path

    def list_files(self) -> list[Path]:
        return sorted(p for p in self.path.glob("**/*") if p.is_file())

    def fetch(self, ref: str) -> bytes:
        return (self.path / ref).read_bytes()

    def cleanup(self) -> None:
        pass