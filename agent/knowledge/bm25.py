"""
P3: BM25 关键词检索。

tokenizer 可换：jieba（中文）/ whitespace（英文）/ custom callable。
"""
from __future__ import annotations

from langchain_core.retrievers import BaseRetriever


def build_bm25_retriever(chunks: list, k: int = 5, tokenizer: str = "jieba") -> BaseRetriever:
    from langchain_community.retrievers import BM25Retriever
    preprocess = _resolve_tokenizer(tokenizer)
    if not chunks:
        return _EmptyRetriever(k=k)
    return BM25Retriever.from_documents(chunks, k=k, preprocess_func=preprocess)


def _resolve_tokenizer(name: str):
    if name == "jieba":
        import jieba
        def t(text: str) -> list[str]:
            return [w for w in jieba.cut(text) if w.strip() and len(w.strip()) > 1]
        return t
    if name == "whitespace":
        return lambda text: text.split()
    if callable(name):
        return name
    raise ValueError(f"未实现的 BM25 tokenizer: {name}（支持 jieba / whitespace / callable）")


class _EmptyRetriever(BaseRetriever):
    """空兜底，避免 from_documents([]) 抛 ValueError。"""
    k: int = 5

    def _get_relevant_documents(self, query, *, run_manager=None):
        return []

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        return []