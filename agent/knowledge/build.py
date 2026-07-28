"""
Retriever strategy 路由。

按 agent.yaml `retriever.strategy` 选：
  vector       纯向量
  hybrid       向量 + BM25（fusion 选 rrf/weighted）
  multiquery   langchain MultiQueryRetriever（自动生成 query 变体）
  hyde         HyDE（LLM 生成假设文档 → 向量检索）
"""
from __future__ import annotations

import pickle
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

from ..config import RetrieverConfig
from .bm25 import build_bm25_retriever
from .fusion import rrf as rrf_fusion
from .fusion import weighted as weighted_fusion
from .hyde import HydeRetriever
from .query_rewrite import QueryRewriteRetriever
from .reranker import maybe_wrap_with_rerank


def _load_bm25_chunks(path: str) -> list:
    p = Path(path)
    if not p.is_file():
        return []
    with p.open("rb") as f:
        return pickle.load(f)


def build_retriever(
    cfg: RetrieverConfig,
    vector_store: VectorStore,
    embedding: Embeddings,
    llm: BaseChatModel | None = None,
) -> BaseRetriever:
    """按 strategy 组装 retriever。"""
    candidate_k = max(cfg.top_k, cfg.fetch_k, cfg.rerank_top_n)
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": candidate_k})

    def finish(retriever: BaseRetriever) -> BaseRetriever:
        if cfg.query_rewrite.enabled:
            if llm is None:
                raise ValueError("query_rewrite 需要 llm")
            retriever = QueryRewriteRetriever(
                base=retriever,
                llm=llm,
                max_rewrites=cfg.query_rewrite.max_rewrites,
            )
        return maybe_wrap_with_rerank(
            retriever,
            cfg_rerank_enabled=cfg.rerank,
            rerank_model=cfg.rerank_model,
            rerank_top_n=cfg.top_k,
            fetch_k=candidate_k,
        )

    if cfg.strategy == "vector":
        return finish(vector_retriever)

    if cfg.strategy == "hyde":
        if llm is None:
            raise ValueError("hyde strategy 需要 llm")
        hyde = HydeRetriever(llm=llm, vector_store=vector_store, top_k=candidate_k)
        return finish(hyde)

    if cfg.strategy == "multiquery":
        if llm is None:
            raise ValueError("multiquery strategy 需要 llm")
        from langchain.retrievers.multi_query import MultiQueryRetriever
        mq = MultiQueryRetriever.from_llm(retriever=vector_retriever, llm=llm)
        return finish(mq)

    if cfg.strategy == "hybrid":
        bm25_chunks = _load_bm25_chunks(cfg.bm25_chunks_path)
        bm25 = build_bm25_retriever(bm25_chunks, k=candidate_k, tokenizer=cfg.bm25_tokenizer)
        retrievers = [vector_retriever, bm25]
        weights = [0.7, 0.3]
        if cfg.fusion == "rrf":
            hybrid = rrf_fusion(retrievers, weights, k_final=candidate_k)
        else:
            hybrid = weighted_fusion(retrievers, weights, k_final=candidate_k)
        return finish(hybrid)

    raise ValueError(
        f"未知 retriever strategy: {cfg.strategy}\n"
        f"可选: vector | hybrid | multiquery | hyde"
    )
