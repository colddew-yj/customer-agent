"""
Retriever fusion strategies: weighted (EnsembleRetriever) 与 RRF。

RRF = Reciprocal Rank Fusion：按排名而非分数融合，对量纲不敏感，比 weighted 更稳。
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class WeightedFusionRetriever(BaseRetriever):
    """加权融合。

    k_const > 0（默认 60）：Reciprocal Rank Fusion，rank 而非 score 融合。
    k_const = 0：纯加权，score = weight / (rank + 1)。

    按 score 降序取 k_final，去重（page_content 前 100 字符 + source_name）。
    """
    retrievers: list[BaseRetriever]
    weights: list[float]
    k_const: int = 60
    k_final: int = 5

    def _get_relevant_documents(self, query, *, run_manager=None):
        scored: list[tuple[float, Document]] = []
        for retriever, weight in zip(self.retrievers, self.weights):
            docs = retriever.invoke(query)
            for rank, d in enumerate(docs):
                scored.append((weight / (self.k_const + rank + 1), d))
        scored.sort(key=lambda x: x[0], reverse=True)
        seen: set[tuple] = set()
        out: list[Document] = []
        for _, d in scored:
            key = (d.page_content[:100], str(d.metadata.get("source_name", "")))
            if key in seen:
                continue
            seen.add(key)
            out.append(d)
            if len(out) >= self.k_final:
                break
        return out

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        return self._get_relevant_documents(query, run_manager=run_manager)


def rrf(retrievers: list[BaseRetriever], weights: list[float], k_final: int = 5) -> BaseRetriever:
    """RRF 融合（论文标准 k=60）。"""
    return WeightedFusionRetriever(retrievers=retrievers, weights=weights, k_final=k_final)


def weighted(retrievers: list[BaseRetriever], weights: list[float], k_final: int = 5) -> BaseRetriever:
    """线性加权：直接按 weight × retriever 自带分（V1 行为）。

    V2 实现：复用 RRF，weight 仅作权重相对值（k_const=0 时退化为加权求和）。
    注：原计划走 langchain.EnsembleRetriever，但 Python 3.14 + pydantic 2.13 上有兼容问题，
    改用自家 WeightedFusionRetriever（k_const=0 即为纯加权）。
    """
    return WeightedFusionRetriever(
        retrievers=retrievers, weights=weights, k_const=0, k_final=k_final
    )