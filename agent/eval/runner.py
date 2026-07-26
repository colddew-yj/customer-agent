"""
Eval runner：拉 dataset → 对每个 example 跑 agent → 跑 evaluators → 汇总。

CLI: customer-helpmesh-agent eval --dataset <name>
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from typing import Any

from ..config import AgentConfig, load as load_config
from ..graph import build_graph
from ..runner import astream_tokens
from .dataset import fetch_examples
from .evaluators import heuristic, similarity


def _build_evaluators(names: list[str], cfg: AgentConfig, embedding) -> list[tuple[str, Any]]:
    out = []
    for name in names:
        if name == "heuristic":
            out.append(("heuristic", heuristic))
        elif name == "similarity":
            out.append(("similarity", similarity(embedding, expected_answer="")))
        elif name == "llm_judge":
            from ..providers import build_llm
            try:
                llm = build_llm(cfg.llm)
                from .evaluators import llm_judge
                out.append(("llm_judge", llm_judge(llm)))
            except Exception:                         # noqa: BLE001
                pass
    return out


async def _run_one(graph, cfg: AgentConfig, q: str, thread_id: str) -> dict:
    output: dict[str, Any] = {"answer": "", "intent": "", "tool_results": [], "sources": []}
    async for event in astream_tokens(
        graph=graph, cfg=cfg,
        question=q, user_token="", user_id="", thread_id=thread_id,
    ):
        kind = event.get("type")
        if kind == "token":
            output["answer"] += event.get("content", "")
    return output


def run_eval(dataset_name: str, evaluator_names: list[str] | None = None) -> dict:
    cfg = load_config()
    evaluator_names = evaluator_names or cfg.langsmith.evaluation.evaluators

    examples = fetch_examples(dataset_name)
    if not examples:
        return {"dataset": dataset_name, "example_count": 0, "score_avg": {}, "per_example": []}

    from ..providers import build_embedding
    embedding = build_embedding(cfg.embedding)
    graph = build_graph(cfg)
    evaluators = _build_evaluators(evaluator_names, cfg, embedding)

    score_sums: dict[str, float] = defaultdict(float)
    score_counts: dict[str, int] = defaultdict(int)
    per_example: list[dict] = []

    for idx, ex in enumerate(examples):
        thread_id = f"eval-{dataset_name}-{idx}"
        output = asyncio.run(_run_one(graph, cfg, ex["q"], thread_id))
        agg: dict[str, Any] = {"q": ex["q"], "scores": {}}
        for ev_name, ev in evaluators:
            scores = ev(ex, output)
            for k, v in scores.items():
                agg["scores"][k] = v["score"]
                score_sums[k] += v["score"]
                score_counts[k] += 1
        per_example.append(agg)

    return {
        "dataset": dataset_name,
        "example_count": len(examples),
        "evaluators": [n for n, _ in evaluators],
        "score_avg": {k: (score_sums[k] / score_counts[k]) for k in score_sums},
        "per_example": per_example,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="customer-helpmesh-agent eval")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", default="./agent.yaml")
    args = parser.parse_args(argv)

    import os
    os.environ["AGENT_CONFIG_PATH"] = args.config

    result = run_eval(args.dataset)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())