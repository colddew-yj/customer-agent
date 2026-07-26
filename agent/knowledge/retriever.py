"""
P3: 检索 strategy 路由（V2 重构）。

V1 只支持 hybrid weighted 单一策略；V2 按 `retriever.strategy` 选：
  vector / hybrid / multiquery / hyde

业务方在 agent.yaml 切换。
"""
from __future__ import annotations

# V2 重构后，build_retriever 在 knowledge/build.py
# 此处 re-export 保持 V1 接口
from .build import build_retriever  # noqa: F401
from .fusion import rrf, weighted  # noqa: F401
from .hyde import HydeRetriever  # noqa: F401


# V1 兼容接口：build_hybrid_retriever 老路径
def build_hybrid_retriever(vector_retriever, bm25_chunks: list, cfg) -> object:
    """V1 兼容：旧调用方传 vector_retriever + bm25_chunks + cfg.retriever 实例。"""
    from langchain.retrievers import EnsembleRetriever
    if not getattr(cfg, "hybrid", True):
        return vector_retriever
    from .bm25 import build_bm25_retriever
    bm25 = build_bm25_retriever(
        bm25_chunks,
        k=getattr(cfg, "fetch_k", 10),
        tokenizer=getattr(cfg, "bm25_tokenizer", "jieba"),
    )
    return EnsembleRetriever(retrievers=[vector_retriever, bm25], weights=[0.7, 0.3])