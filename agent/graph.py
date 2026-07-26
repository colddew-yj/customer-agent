"""
P6: LangGraph graph 动态构建。

从 agent.yaml `intents:` 列表动态：
  - 创建每个 intent 的 node
  - 创建 classify 节点（LLM 判 intent）
  - 条件边 → 路由到对应 intent node

无任何 hardcoded intent。
"""
from __future__ import annotations

import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .config import AgentConfig
from .providers import build_embedding, build_llm, build_vector_store
from .knowledge.retriever import build_hybrid_retriever
from .skills.registry import build_handler
from .skills.state import GraphState
from .tools.registry import ToolRegistry


CLASSIFY_SYSTEM = """你是意图分类器。判断用户问的是哪种意图。

可选意图：
{intent_list}

返回 JSON：{{"intent": "<name>", "confidence": 0.0-1.0}}"""


def _build_classifier(cfg: AgentConfig, llm):
    intents_desc = "\n".join(f"- {it.name}: {it.description}" for it in cfg.intents)
    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFY_SYSTEM.format(intent_list=intents_desc)),
        ("human", "{question}\n\n回答："),
    ])
    chain = prompt | llm | StrOutputParser()

    allowed = {it.name for it in cfg.intents}

    def classify(state: GraphState) -> dict:
        raw = chain.invoke({"question": state["question"]}).strip()
        try:
            raw = raw.strip().strip("`").removeprefix("json").strip()
            data = json.loads(raw)
            intent = data.get("intent", "").lower()
            confidence = float(data.get("confidence", 0.5))
        except Exception:                                # noqa: BLE001
            intent = ""
            confidence = 0.3

        if intent not in allowed:
            intent = "refuse" if "refuse" in allowed else next(iter(allowed))
            confidence = 0.3
        return {"intent": intent, "route": intent, "confidence": confidence}

    return classify


def build_graph(cfg: AgentConfig, checkpointer=None):
    """从 AgentConfig 编译 LangGraph。"""
    llm = build_llm(cfg.llm)
    embedding = build_embedding(cfg.embedding)
    vector_store = build_vector_store(cfg.vector_store, embedding)
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": cfg.retriever.top_k})

    bm25_chunks = []
    retriever = build_hybrid_retriever(vector_retriever, bm25_chunks, cfg.retriever)

    tools = ToolRegistry(cfg.tools)

    builder = StateGraph(GraphState)
    classify_node = _build_classifier(cfg, llm)
    builder.add_node("classify", classify_node)

    for it in cfg.intents:
        ctx = {
            "llm": llm,
            "retriever": retriever,
            "tools": tools,
            "config": cfg,
            "intent_cfg": it,
        }
        builder.add_node(it.name, build_handler(it.handler, ctx))

    builder.add_edge(START, "classify")

    routing = {it.name: it.name for it in cfg.intents}
    builder.add_conditional_edges("classify", lambda s: s.get("route", "refuse"), routing)

    for it in cfg.intents:
        builder.add_edge(it.name, END)

    cp = checkpointer or MemorySaver()
    return builder.compile(checkpointer=cp)