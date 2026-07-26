"""Account handler: 调业务 API 查账户 + LLM 生成回答。"""
from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState


SYSTEM = """你是 {brand} 的 {assistant}。用户问账户相关问题。

下面是实时从业务 API 拉取的账户数据（JSON）。

规则：
1. 基于 JSON 回答用户问题，不编造数字
2. 用用户语言回答，不超过 200 字
3. success=false 时告诉用户 API 失败，让其稍后再试
4. 不暴露 token / user_id / API URL"""


def build(ctx):
    llm = ctx["llm"]
    tools = ctx["tools"]
    tool_names = ctx["intent_cfg"].uses_tools
    brand = ctx["config"].brand_name
    assistant = ctx["config"].assistant_name
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM.format(brand=brand, assistant=assistant)),
        ("human", "用户问题：{question}\n\n实时账户数据（JSON）：\n{account_data}\n\n回答："),
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
        account_data = {"success": ok, "results": results}

        if not ok:
            return {"account_data": account_data, "answer": "暂时无法获取你的账户数据，请稍后再试。"}

        out = chain.invoke({
            "question": state["question"],
            "account_data": json.dumps(account_data, ensure_ascii=False, indent=2),
        })
        return {"account_data": account_data, "answer": getattr(out, "content", out)}

    return node