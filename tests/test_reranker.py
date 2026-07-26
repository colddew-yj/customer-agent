"""V3: reranker 行为测试（mock FlagEmbedding）。"""
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from agent.knowledge.reranker import CrossEncoderReranker, maybe_wrap_with_rerank


def _fake_reranker_module():
    fake_mod = MagicMock()

    class FakeFlagReranker:
        def __init__(self, model_name, use_fp16=True):
            self.model_name = model_name

        def compute_score(self, pairs):
            return [10.0 - i for i in range(len(pairs))]

    fake_mod.FlagReranker = FakeFlagReranker
    return fake_mod


def test_reranker_basic_sorting():
    with patch.dict("sys.modules", {"FlagEmbedding": _fake_reranker_module()}):
        r = CrossEncoderReranker(model_name="fake/model")
        docs = [
            Document(page_content="high relevance", metadata={"id": "b"}),
            Document(page_content="medium", metadata={"id": "c"}),
            Document(page_content="low relevance", metadata={"id": "a"}),
        ]
        # fake compute_score 返回 [10.0, 9.0, 8.0] 对应 input 顺序
        # 排序后 b > c > a
        out = r.rerank("query", docs, top_n=3)
        assert [d.metadata["id"] for d in out] == ["b", "c", "a"]


def test_reranker_empty():
    with patch.dict("sys.modules", {"FlagEmbedding": _fake_reranker_module()}):
        r = CrossEncoderReranker()
        assert r.rerank("q", [], top_n=5) == []


def test_reranker_top_n_truncates():
    with patch.dict("sys.modules", {"FlagEmbedding": _fake_reranker_module()}):
        r = CrossEncoderReranker()
        docs = [Document(page_content=f"d{i}") for i in range(10)]
        out = r.rerank("q", docs, top_n=3)
        assert len(out) == 3


def test_maybe_wrap_disabled():
    base = MagicMock()
    out = maybe_wrap_with_rerank(
        base, cfg_rerank_enabled=False,
        rerank_model="x", rerank_top_n=5, fetch_k=20,
    )
    assert out is base


def test_maybe_wrap_enabled_wraps():
    """用真 BaseRetriever 子类（MagicMock 不被 pydantic 接受）。"""
    from langchain_core.retrievers import BaseRetriever

    class _StubRetriever(BaseRetriever):
        docs: list[Document]

        def _get_relevant_documents(self, query, *, run_manager=None):
            return self.docs

    base = _StubRetriever(docs=[
        Document(page_content="x"),
        Document(page_content="y"),
    ])
    with patch.dict("sys.modules", {"FlagEmbedding": _fake_reranker_module()}):
        out = maybe_wrap_with_rerank(
            base, cfg_rerank_enabled=True,
            rerank_model="fake/model", rerank_top_n=1, fetch_k=20,
        )
    result = out.invoke("q")
    assert len(result) == 1


def test_maybe_wrap_missing_deps_falls_back():
    base = MagicMock()
    out = maybe_wrap_with_rerank(
        base, cfg_rerank_enabled=True,
        rerank_model="fake/nonexistent", rerank_top_n=5, fetch_k=20,
    )
    assert out is base