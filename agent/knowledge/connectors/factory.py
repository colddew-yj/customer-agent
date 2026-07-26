"""
V3: connector factory。按 yaml `connector` 字段路由。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .local import LocalConnector
from .s3 import S3Connector
from .git_repo import GitConnector
from .notion import NotionConnector


_REGISTRY: dict[str, type] = {
    "local": LocalConnector,
    "s3": S3Connector,
    "git": GitConnector,
    "notion": NotionConnector,
}


def build_connector(
    name: str,
    config: dict[str, Any],
    base: Path,
    cache_root: Path | None = None,
    connector_type: str | None = None,
    source_path: str | None = None,
) -> object:
    """name: source 名（仅用于 cache 目录）。connector_type 决定走哪类（默认 local）。"""
    ctype = (connector_type or "local").lower()
    if ctype not in _REGISTRY:
        raise ValueError(f"未知 connector: {ctype}，可选: {list(_REGISTRY.keys())}")
    cache_root = cache_root or Path("./data/cache")
    cfg = {**config, "__source_name": name}
    cache_dir = cache_root / name
    cls = _REGISTRY[ctype]
    if ctype == "local":
        return cls(name, cfg, base, cache_dir, source_path=source_path)
    return cls(name, cfg, base, cache_dir)