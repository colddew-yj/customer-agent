"""
P6: Token 级 SSE 流。

astream_events(version="v2") 监听 on_chat_model_stream，
放行 GENERATE_NODES 中的 token，过滤 classify 的 JSON 误推。
"""
from __future__ import annotations

from typing import AsyncIterator

from langchain_core.messages import HumanMessage


GENERATE_NODES = {"faq", "account", "complaint", "chat"}


async def astream_tokens(
    graph,
    cfg,
    question: str,
    user_token: str,
    user_id: str,
    thread_id: str,
) -> AsyncIterator[dict]:
    """yield 事件: sources / token / done"""
    initial = {
        "question": question,
        "user_token": user_token,
        "user_id": user_id,
        "messages": [HumanMessage(content=question)],
    }
    config = {"configurable": {"thread_id": thread_id}}
    sources_emitted = False

    async for event in graph.astream_events(initial, config=config, version="v2"):
        kind = event.get("event")
        if not sources_emitted and kind == "on_chain_end":
            output = event.get("data", {}).get("output", {})
            if isinstance(output, dict) and output.get("sources"):
                sources_emitted = True
                docs = output["sources"] or []
                yield {
                    "type": "sources",
                    "sources": [
                        {
                            "file_name": d.metadata.get("source_name", "unknown"),
                            "chunk_index": d.metadata.get("chunk_index"),
                            "snippet": d.page_content[:100].replace("\n", " "),
                        }
                        for d in docs
                    ],
                }
                continue

        if kind == "on_chat_model_stream":
            meta = event.get("metadata", {}) or {}
            node = meta.get("langgraph_node") or ""
            if node not in GENERATE_NODES:
                continue
            chunk = event.get("data", {}).get("chunk")
            content = getattr(chunk, "content", "")
            if content:
                yield {"type": "token", "content": content}

        if kind == "on_chain_end":
            output = event.get("data", {}).get("output", {})
            meta = event.get("metadata", {}) or {}
            node = meta.get("langgraph_node") or ""
            if node == "refuse" and isinstance(output, dict) and output.get("answer"):
                yield {"type": "token", "content": output["answer"]}

    yield {"type": "done"}