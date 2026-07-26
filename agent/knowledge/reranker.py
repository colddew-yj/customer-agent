"""
V3: Rerank（cross-encoder 精排）。

召回 top_k=20 候选 → cross-encoder 打分 → 取 top_n=5。

依赖（可选 install）：
  pip install -e ".[rerank]"
  → sentence-transformers + FlagEmbedding

业务方不装：retriever 退化为无 rerank（不影响主流程）。
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class CrossEncoderReranker:
    """HuggingFace cross-encoder rerank。"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        try:
            from FlagEmbedding import FlagReranker
            self._rerank = FlagReranker(model_name, use_fp16=True)
        except ImportError as e:
            raise RuntimeError(
                "rerank 需要 FlagEmbedding：pip install FlagEmbedding"
            ) from e

    def rerank(self, query: str, docs: list[Document], top_n: int = 5) -> list[Document]:
        if not docs:
            return []
        pairs = [[query, d.page_content] for d in docs]
        scores = self._rerank.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]
        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [d for _, d in ranked[:top_n]]


class RerankRetriever(BaseRetriever):
    """给任一 BaseRetriever 包一层 rerank。"""

    base: BaseRetriever
    reranker: CrossEncoderReranker
    top_n: int = 5
    fetch_k: int = 20

    def _get_relevant_documents(self, query, *, run_manager=None):
        candidates = self.base.invoke(query)
        if not candidates:
            return []
        return self.reranker.rerank(query, candidates, top_n=self.top_n)

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        candidates = await self.base.ainvoke(query)
        if not candidates:
            return []
        return self.reranker.rerank(query, candidates, top_n=self.top_n)


def maybe_wrap_with_rerank(
    retriever: BaseRetriever,
    cfg_rerank_enabled: bool,
    rerank_model: str,
    rerank_top_n: int,
    fetch_k: int,
) -> BaseRetriever:
    """如果启用了 rerank 且 deps 装了，包一层；否则原样返回。"""
    if not cfg_rerank_enabled:
        return retriever
    try:
        reranker = CrossEncoderReranker(model_name=rerank_model)
    except RuntimeError as e:
        print(f"[rerank] {e}，跳过（仍用原 retriever）")
        return retriever
    return RerankRetriever(
        base=retriever, reranker=reranker,
        top_n=rerank_top_n, fetch_k=fetch_k,
    )