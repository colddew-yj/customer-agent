"""
P3: 知识入库 CLI。

遍历 agent.yaml `knowledge.sources`，每个 source 加载→切分→向量化→持久化。
稳定 ID 让重跑不重复入库。
V2: 同时把 chunks 落 `bm25_chunks.pkl` 给 hybrid retriever 用。
"""
from __future__ import annotations

import argparse
import os
import pickle
import sys
import time
from pathlib import Path

from langchain_core.documents import Document

from ..config import AgentConfig, load
from ..providers import build_embedding, build_vector_store
from .loader import load_dir
from .splitter import split_documents


def _tag_metadata(docs: list[Document], tags: dict, source_name: str) -> list[Document]:
    for d in docs:
        d.metadata.setdefault("source_name", source_name)
        d.metadata.setdefault("source", source_name)
        for k, v in tags.items():
            d.metadata.setdefault(k, v)
    return docs


def _dump_bm25_chunks(chunks: list, path: str) -> None:
    """V2: 落 pickle，给 hybrid retriever 启动时 load（替代运行时空列表）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("wb") as f:
        pickle.dump(chunks, f)


def run(cfg: AgentConfig, base: Path) -> dict:
    start = time.time()
    embedding = build_embedding(cfg.embedding)
    store = build_vector_store(cfg.vector_store, embedding)

    # V3: 优先用 connector.sync() 拉远程内容到 cache，本地直接读 path
    from .connectors.factory import build_connector as _build_connector

    all_chunks: list[Document] = []
    stats: dict = {"sources": [], "total_chunks": 0}
    for src in cfg.knowledge.sources:
        connector = _build_connector(src.name, src.connector_config or {}, base)
        cache_dir = connector.sync()
        glob = "**/*"
        # yaml source 可指定 glob，但 connector 已有 path_filter
        # 简化：默认递归
        if not cache_dir.exists():
            print(f"[skip] {src.name}: cache 目录不存在")
            continue

        print(f"[load] {src.name} <- {cache_dir} (via {src.connector or 'local'})")
        loaded = load_dir(cache_dir, glob=glob)
        loaded = _tag_metadata(loaded, src.metadata_tags, src.name)
        chunks = split_documents(loaded, chunk_size=src.chunk_size, chunk_overlap=src.chunk_overlap)
        for idx, c in enumerate(chunks):
            c.metadata["chunk_index"] = idx
            c.metadata["stable_id"] = f"{src.name}#{idx}"

        store.add_documents(chunks)
        all_chunks.extend(chunks)
        stats["sources"].append({"name": src.name, "chunks": len(chunks), "connector": src.connector or "local"})
        stats["total_chunks"] += len(chunks)

    bm25_path = cfg.retriever.bm25_chunks_path
    _dump_bm25_chunks(all_chunks, bm25_path)
    stats["bm25_chunks_path"] = bm25_path

    stats["duration_sec"] = round(time.time() - start, 2)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="customer-agent ingest")
    parser.add_argument("--config", default="./agent.yaml")
    parser.add_argument("--base", default=".")
    args = parser.parse_args(argv)

    os.environ["AGENT_CONFIG_PATH"] = args.config

    cfg = load()
    base = Path(args.base).resolve()
    stats = run(cfg, base)
    print("\n=== ingest stats ===")
    print(f"sources: {len(stats['sources'])}")
    print(f"total_chunks: {stats['total_chunks']}")
    print(f"bm25_chunks: {stats['bm25_chunks_path']}")
    print(f"duration: {stats['duration_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())