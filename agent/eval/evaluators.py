"""
3 种 evaluator：
  heuristic   不调 LLM，纯规则（intent / keywords / tools）
  similarity  embedding cosine（answer vs expected）
  llm_judge   LLM 评 "answer 是否含 expect_keywords"
"""
from __future__ import annotations

from typing import Any, Callable

from langchain_core.embeddings import Embeddings


def heuristic(example: dict, output: dict) -> dict[str, Any]:
    scores: dict[str, Any] = {}

    expect_intent = example.get("expect_intent", "")
    actual_intent = output.get("intent", "")
    scores["intent"] = {
        "score": 1.0 if expect_intent == actual_intent else 0.0,
        "comment": f"expect={expect_intent} actual={actual_intent}",
    }

    answer = output.get("answer", "") or ""
    keywords = example.get("expect_keywords", []) or []
    if keywords:
        hits = sum(1 for k in keywords if k in answer)
        scores["keywords"] = {
            "score": hits / len(keywords),
            "comment": f"hits={hits}/{len(keywords)} keywords={keywords}",
        }
    else:
        scores["keywords"] = {"score": 1.0, "comment": "no keywords specified"}

    tools_used = output.get("tool_results", []) or []
    tools_expected = example.get("expect_tools", []) or []
    if tools_expected:
        used = {t.get("tool") for t in tools_used}
        hits = sum(1 for t in tools_expected if t in used)
        scores["tools"] = {
            "score": hits / len(tools_expected),
            "comment": f"hits={hits}/{len(tools_expected)} expected={tools_expected}",
        }
    else:
        scores["tools"] = {"score": 1.0, "comment": "no tools expected"}

    return scores


def similarity(embedding: Embeddings, expected_answer: str) -> Callable:
    def _eval(example: dict, output: dict) -> dict[str, Any]:
        answer = output.get("answer", "") or ""
        if not answer or not expected_answer:
            return {"similarity": {"score": 0.0, "comment": "empty answer"}}
        try:
            a, b = embedding.embed_documents([answer, expected_answer])
            import numpy as np
            va, vb = np.array(a), np.array(b)
            cos = float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))
            return {"similarity": {"score": cos, "comment": f"cosine={cos:.3f}"}}
        except Exception as e:                          # noqa: BLE001
            return {"similarity": {"score": 0.0, "comment": f"embed failed: {e}"}}
    return _eval


def llm_judge(llm, prompt_template: str | None = None) -> Callable:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    tmpl = prompt_template or (
        "评估下面客服回复是否合格。\n"
        "期望要点：{keywords}\n"
        "实际回复：{answer}\n"
        "回答 YES 或 NO，并简短说明。"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是评估员。"),
        ("human", tmpl),
    ])
    chain = prompt | llm | StrOutputParser()

    def _eval(example: dict, output: dict) -> dict[str, Any]:
        answer = output.get("answer", "") or ""
        keywords = example.get("expect_keywords", []) or []
        try:
            verdict = chain.invoke({"keywords": ", ".join(keywords), "answer": answer})
            score = 1.0 if "YES" in verdict.upper() else 0.0
            return {"llm_judge": {"score": score, "comment": verdict.strip()[:200]}}
        except Exception as e:                          # noqa: BLE001
            return {"llm_judge": {"score": 0.0, "comment": f"llm call failed: {e}"}}
    return _eval