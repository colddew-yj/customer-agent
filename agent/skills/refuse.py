"""Refuse handler: 预设话术拒答，不调 LLM。"""
from __future__ import annotations

from .state import GraphState


DEFAULT_REFUSE = "这个问题我暂时帮不上忙。建议你换个角度描述问题，或联系人工客服。"


def build(ctx):
    cfg = ctx["config"]
    brand = cfg.brand_name
    msg = DEFAULT_REFUSE
    custom = getattr(cfg, "refuse_message", None)
    if custom:
        msg = custom
    final = msg.format(brand=brand)

    def node(state: GraphState) -> dict:
        return {"answer": final}

    return node