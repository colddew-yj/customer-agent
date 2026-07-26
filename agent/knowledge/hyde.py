"""
HyDE：LLM 先生成"假设答案"，再用它检索。

适用：query 抽象 / 口语化。
trade-off：每 query +1 次 LLM 调用（p95 +300-500ms）。
"""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore


_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "假设你正在回答下面用户的问题。输出一段（50-150 字）可能的参考资料片段。只输出这段内容，不要其他。"),
    ("human", "{question}"),
])


class HydeRetriever(BaseRetriever):
    llm: BaseChatModel
    vector_store: VectorStore
    top_k: int = 5

    def _generate_hypothetical(self, question: str) -> str:
        chain = _PROMPT | self.llm | StrOutputParser()
        return chain.invoke({"question": question})

    def _get_relevant_documents(self, query, *, run_manager=None):
        hypothetical = self._generate_hypothetical(query)
        return self.vector_store.similarity_search(hypothetical, k=self.top_k)

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        hypothetical = self._generate_hypothetical(query)
        return await self.vector_store.asimilarity_search(hypothetical, k=self.top_k)