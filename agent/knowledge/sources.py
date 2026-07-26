"""
P3: 知识源清单。

从 agent.yaml `knowledge.sources:` 加载，注入 base path。
"""
from __future__ import annotations

from pathlib import Path

from ..config import AgentConfig


def list_sources(cfg: AgentConfig, base: Path) -> list[tuple[str, Path, str, dict]]:
    """返回 [(name, abs_path, glob, metadata_tags), ...]"""
    out: list[tuple[str, Path, str, dict]] = []
    for src in cfg.knowledge.sources:
        out.append((src.name, base / src.path, src.glob, src.metadata_tags))
    return out