"""Chat handler: 闲聊 / 自我介绍。"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState


SYSTEM = """你是 {brand} 的 {assistant}。用户在闲聊或询问你自身。

规则：
1. 简短自我介绍（你能回答业务问题）
2. 引导用户提业务问题
3. 用用户语言回答，不超过 80 字"""


def build(ctx):
    llm = ctx["llm"]
    brand = ctx["config"].brand_name
    assistant = ctx["config"].assistant_name
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM.format(brand=brand, assistant=assistant)),
        ("human", "{question}\n\n回复："),
    ])
    chain = prompt | llm

    def node(state: GraphState) -> dict:
        out = chain.invoke({"question": state["question"]})
        return {"answer": getattr(out, "content", out)}

    return node