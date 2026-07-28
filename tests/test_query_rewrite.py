from langchain_community.chat_models import FakeListChatModel
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from agent.knowledge.query_rewrite import QueryRewriteRetriever


class _StubRetriever(BaseRetriever):
    calls: list[str] = Field(default_factory=list)

    def _get_relevant_documents(self, query, *, run_manager=None):
        self.calls.append(query)
        return [
            Document(page_content="API 接入步骤", metadata={"stable_id": "api"})
        ] if query != "原问题" else []


def test_query_rewrite_keeps_original_and_deduplicates():
    base = _StubRetriever(calls=[])
    retriever = QueryRewriteRetriever(
        base=base,
        llm=FakeListChatModel(responses=['["改写问题", "改写问题"]']),
        max_rewrites=2,
    )

    docs = retriever.invoke("原问题")

    assert base.calls == ["原问题", "改写问题"]
    assert len(docs) == 1


def test_query_rewrite_falls_back_to_original_on_invalid_output():
    base = _StubRetriever(calls=[])
    retriever = QueryRewriteRetriever(
        base=base,
        llm=FakeListChatModel(responses=["not json"]),
        max_rewrites=2,
    )

    retriever.invoke("原问题")

    assert base.calls == ["原问题"]
