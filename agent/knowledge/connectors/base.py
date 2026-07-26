"""
KnowledgeConnector 抽象。
"""
from __future__ import annotations

import abc
import shutil
from pathlib import Path
from typing import Any


class KnowledgeConnector(abc.ABC):
    """知识源 connector 抽象基类。"""

    def __init__(self, name: str, config: dict[str, Any], base: Path, cache_dir: Path):
        self.name = name
        self.config = config
        self.base = base
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @abc.abstractmethod
    def sync(self) -> Path:
        """同步远程内容到本地 cache，返回 cache 目录路径。"""
        ...

    def list_files(self) -> list[Path]:
        cache = self.sync()
        return sorted(p for p in cache.glob("**/*") if p.is_file())

    def fetch(self, ref: str) -> bytes:
        cache = self.sync()
        return (cache / ref).read_bytes()

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)