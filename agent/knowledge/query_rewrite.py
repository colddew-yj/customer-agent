"""受约束的 query rewrite：原 query 保留，改写只用于补召回。"""
from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "你是搜索查询改写器。把用户问题改写成最多 {max_rewrites} 个等价搜索 query。\n"
            "规则：不改变原意；不扩展问题范围；保留产品名、API 名和专有名词；"
            "只调整口语表达和句式；只输出 JSON 字符串数组。"
        ),
    ),
    ("human", "用户问题：{question}"),
])


class QueryRewriteRetriever(BaseRetriever):
    """多 query 召回并去重；由外层 reranker 对合并结果统一精排。"""

    base: BaseRetriever
    llm: BaseChatModel
    max_rewrites: int = 2

    def _rewrite(self, question: str) -> list[str]:
        chain = _PROMPT | self.llm | StrOutputParser()
        try:
            raw = chain.invoke({
                "question": question,
                "max_rewrites": self.max_rewrites,
            }).strip()
            if raw.startswith("```"):
                raw = raw.strip("`").removeprefix("json").strip()
            values = json.loads(raw)
        except Exception:  # noqa: BLE001
            return []
        if not isinstance(values, list):
            return []
        out: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            value = value.strip()
            if value and value != question and value not in out:
                out.append(value)
            if len(out) >= self.max_rewrites:
                break
        return out

    @staticmethod
    def _key(doc) -> tuple:
        metadata = doc.metadata or {}
        return (
            metadata.get("stable_id")
            or metadata.get("source_name")
            or metadata.get("source", ""),
            doc.page_content,
        )

    def _retrieve(self, queries: list[str], *, invoke) -> list:
        docs = []
        seen: set[tuple] = set()
        for query in queries:
            for doc in invoke(query):
                key = self._key(doc)
                if key in seen:
                    continue
                seen.add(key)
                docs.append(doc)
        return docs

    def _get_relevant_documents(self, query, *, run_manager=None):
        queries = [query, *self._rewrite(query)]
        return self._retrieve(queries, invoke=self.base.invoke)

    async def _aget_relevant_documents(self, query, *, run_manager=None):
        chain = _PROMPT | self.llm | StrOutputParser()
        try:
            raw = await chain.ainvoke({
                "question": query,
                "max_rewrites": self.max_rewrites,
            })
            if raw.startswith("```"):
                raw = raw.strip("`").removeprefix("json").strip()
            values = json.loads(raw)
        except Exception:  # noqa: BLE001
            values = []
        rewrites = []
        if isinstance(values, list):
            for value in values:
                if (
                    isinstance(value, str)
                    and value.strip()
                    and value.strip() != query
                    and value.strip() not in rewrites
                ):
                    rewrites.append(value.strip())
                if len(rewrites) >= self.max_rewrites:
                    break

        docs = []
        seen: set[tuple] = set()
        for search_query in [query, *rewrites]:
            for doc in await self.base.ainvoke(search_query):
                key = self._key(doc)
                if key in seen:
                    continue
                seen.add(key)
                docs.append(doc)
        return docs
