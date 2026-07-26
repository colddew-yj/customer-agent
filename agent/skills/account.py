"""Realtime-data handler: 调外部工具（业务 API）取实时数据 → LLM 生成回答。

通用型：业务方在 agent.yaml `intents:` 把这个 handler 命名（如 account / lookup / query_xxx），
endpoint 在 `tools:` 段配。回答什么完全由业务方的工具决定。
"""
from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState


SYSTEM = """你是 {brand} 的 {assistant}。用户问的问题需要实时数据才能回答。

下面是刚刚从外部接口拉取的实时数据（JSON）。

规则：
1. 基于 JSON 回答，不编造数字或字段
2. 用用户语言回答，不超过 200 字
3. success=false 时告诉用户接口暂时拿不到数据，让其稍后再试
4. 不暴露 token / user_id / 接口 URL"""


def build(ctx):
    llm = ctx["llm"]
    tools = ctx["tools"]
    tool_names = ctx["intent_cfg"].uses_tools
    brand = ctx["config"].brand_name
    assistant = ctx["config"].assistant_name
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM.format(brand=brand, assistant=assistant)),
        ("human", "用户问题：{question}\n\n实时数据（JSON）：\n{realtime_data}\n\n回答："),
    ])
    chain = prompt | llm

    def node(state: GraphState) -> dict:
        ctx_inv = {
            "user_token": state.get("user_token", ""),
            "user_id": state.get("user_id", ""),
            "question": state["question"],
        }
        results = []
        for name in tool_names:
            if not tools.has(name):
                continue
            results.append({"tool": name, "result": tools.invoke(name, ctx_inv)})

        ok = all(r["result"].get("success") for r in results) if results else False
        realtime_data = {"success": ok, "results": results}

        if not ok:
            return {
                "realtime_data": realtime_data,
                "answer": "暂时拿不到实时数据，请稍后再试。",
            }

        out = chain.invoke({
            "question": state["question"],
            "realtime_data": json.dumps(realtime_data, ensure_ascii=False, indent=2),
        })
        return {
            "realtime_data": realtime_data,
            "answer": getattr(out, "content", out),
        }

    return node