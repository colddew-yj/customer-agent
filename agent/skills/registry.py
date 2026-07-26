"""
P4: skills registry。

5 个内置 handler: faq / account / complaint / chat / refuse。
每个 handler 接受 ctx（retriever / tools / llm / agent_config），返回 node(state)。
"""
from __future__ import annotations

from typing import Any, Callable

from . import faq, account, complaint, chat, refuse
from .state import GraphState


BUILTIN_HANDLERS: dict[str, Callable[..., Callable[[GraphState], dict]]] = {
    "faq": faq.build,
    "account": account.build,
    "complaint": complaint.build,
    "chat": chat.build,
    "refuse": refuse.build,
}


def build_handler(handler_str: str, ctx: Any) -> Callable[[GraphState], dict]:
    """
    handler_str: "faq" / "account" / "complaint" / "chat" / "refuse"。
    ctx: ctx dict，含 retriever / tools / llm / config。
    返回一个 LangGraph node 函数。
    """
    name = handler_str.removeprefix("builtin:")
    if name not in BUILTIN_HANDLERS:
        raise ValueError(
            f"未知 handler: {handler_str}\n"
            f"内置可选: {list(BUILTIN_HANDLERS.keys())}"
        )
    return BUILTIN_HANDLERS[name](ctx)