"""Complaint handler: 共情 + 转人工话术。"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from .state import GraphState


SYSTEM = """你是 {brand} 的 {assistant}。用户表达不满或投诉。

规则：
1. 先共情：承认用户不满，不急着辩解
2. 简短说明你会怎么协助（建议转人工、提供订单号查询等）
3. 引导用户提供具体信息（订单号、错误截图、复现步骤）
4. 不承诺具体退款金额或补偿
5. 用用户语言回答，不超过 150 字"""


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