"""
P4: skills registry。

V2 加 custom_handlers：
- builtin: faq / account / complaint / chat / refuse
- custom: 业务方在 agent.yaml `intents[].handler` 写路径

handler 字符串取值：
  builtin:faq / builtin:account / builtin:complaint / builtin:chat / builtin:refuse
  /abs/path/to/handler.py:build
  handlers/order.py:build       (相对 cwd)
  order                         (从 ~/.customer-agent/handlers/ 找)
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

# V2: 运行时填充
CUSTOM_HANDLERS: dict[str, Callable[..., Callable[[GraphState], dict]]] = {}


def register_custom(name: str, factory: Callable) -> None:
    CUSTOM_HANDLERS[name] = factory


def all_handlers() -> dict[str, Callable]:
    merged = dict(BUILTIN_HANDLERS)
    merged.update(CUSTOM_HANDLERS)
    return merged


def build_handler(handler_str: str, ctx: Any) -> Callable[[GraphState], dict]:
    if handler_str.startswith("builtin:"):
        name = handler_str.removeprefix("builtin:")
        if name not in BUILTIN_HANDLERS:
            raise ValueError(
                f"未知 builtin handler: {handler_str}\n"
                f"可选: {list(BUILTIN_HANDLERS.keys())}"
            )
        return BUILTIN_HANDLERS[name](ctx)

    from .loader import discover_from_path
    factory = discover_from_path(handler_str)
    name = handler_str.split(":")[0].split("/")[-1].replace(".py", "")
    register_custom(name, factory)
    return factory(ctx)