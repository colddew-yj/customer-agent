"""LangGraph state。节点间共享消息和请求上下文。"""
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict, total=False):
    """所有意图 handler 共享 state。"""
    question: str
    intent: str
    route: str
    context: str            # RAG 检索拼好的字符串
    sources: list           # Document 列表
    answer: str
    user_token: str         # 透传真用户 token
    user_id: str
    account_data: dict      # tool 调用结果
    tool_results: list
    messages: Annotated[list[AnyMessage], add_messages]
    confidence: float
    refused_reason: str
