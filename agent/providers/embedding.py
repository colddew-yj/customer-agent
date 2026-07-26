"""Embedding factory。"""
from __future__ import annotations

import os

from langchain_core.embeddings import Embeddings

from ..config import EmbeddingConfig


def build_embedding(cfg: EmbeddingConfig) -> Embeddings:
    api_key = os.environ.get(cfg.api_key_env, "") or os.environ.get("_EMB_KEY", "")
    common = dict(model=cfg.model)

    if cfg.provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=api_key, base_url=cfg.base_url, **common)
    if cfg.provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=cfg.model)
    if cfg.provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(base_url=cfg.base_url or "http://localhost:11434", model=cfg.model)
    raise ValueError(f"未实现的 embedding provider: {cfg.provider}")