"""
V3.7: 安全的 prompt helper。

langchain ChatPromptTemplate 在 system 文本里扫 {...} 当 input 变量，
跟 langchain string.Formatter 一样。模板里出现 {<name>} 字面量（哪怕是 JSON 示例）
会触发 KeyError。

safe_messages() 绕过：直接拼 [SystemMessage, HumanMessage] + RunnableLambda，
跟 agent/graph.py 之前修的 classifier 一致。给后续 handler / intent prompt 复用。
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableLambda


def safe_messages(system_text: str) -> Runnable:
    """返回 Runnable: input dict → [SystemMessage, HumanMessage]。

    用法：chain = safe_messages(SYS) | llm | StrOutputParser()
         chain.invoke({"question": "..."})   # input dict 必须含 question 字段
    """
    def _to_msgs(inp: dict) -> list:
        question = inp.get("question", "")
        return [
            SystemMessage(content=system_text),
            HumanMessage(content=question),
        ]
    return RunnableLambda(_to_msgs)