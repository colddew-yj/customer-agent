"""Vector store factory。"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from ..config import VectorStoreConfig


def build_vector_store(cfg: VectorStoreConfig, embedding: Embeddings) -> VectorStore:
    if cfg.provider == "chroma":
        # 兼容新 (langchain_chroma) / 老 (langchain_community.vectorstores.Chroma) 包名
        try:
            from langchain_chroma import Chroma
        except ImportError:
            from langchain_community.vectorstores import Chroma
        return Chroma(
            collection_name=cfg.collection_name,
            embedding_function=embedding,
            persist_directory=cfg.persist_dir,
        )
    if cfg.provider == "in-memory":
        from langchain_core.vectorstores import InMemoryVectorStore
        return InMemoryVectorStore(embedding=embedding)
    raise ValueError(f"未实现的 vector store: {cfg.provider}")