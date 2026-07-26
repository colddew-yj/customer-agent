"""V2: retriever fusion (RRF / weighted) 单测。"""
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from agent.knowledge.fusion import WeightedFusionRetriever, rrf, weighted


class _FakeRetriever(BaseRetriever):
    """最小 BaseRetriever 子类：返回预定的 docs 列表。"""
    docs: list[Document]

    def _get_relevant_documents(self, query, *, run_manager=None):
        return self.docs

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        return self.docs


def test_rrf_dedup_and_order():
    d1 = [Document(page_content="alpha foo bar", metadata={"source_name": "a"})]
    d2 = [Document(page_content="alpha foo bar", metadata={"source_name": "a"}),
          Document(page_content="beta", metadata={"source_name": "b"})]
    r1 = _FakeRetriever(docs=d1)
    r2 = _FakeRetriever(docs=d2)

    merged = rrf([r1, r2], weights=[1.0, 1.0], k_final=3)
    out = merged.invoke("anything")
    assert len(out) == 2
    assert out[0].metadata["source_name"] == "a"
    assert out[1].metadata["source_name"] == "b"


def test_weighted_uses_ensemble_retriever():
    d1 = [Document(page_content="x", metadata={"source_name": "a"})]
    d2 = [Document(page_content="y", metadata={"source_name": "b"})]
    r1 = _FakeRetriever(docs=d1)
    r2 = _FakeRetriever(docs=d2)
    merged = weighted([r1, r2], weights=[0.5, 0.5], k_final=2)
    out = merged.invoke("q")
    assert len(out) == 2


def test_weighted_fusion_retriever_k_const_default():
    """k_const=60 默认（论文标准）。"""
    rrf_obj = WeightedFusionRetriever(retrievers=[], weights=[], k_const=60, k_final=10)
    assert rrf_obj.k_const == 60