"""
Dataset：业务方定义 {"q": "...", "expect_intent": "...", "expect_keywords": [...]} 列表，
推到 / 拉 LangSmith Dataset。无 LangSmith 时回退本地 JSONL。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _local_dataset_path(name: str) -> Path:
    return Path(f"./data/datasets/{name}.jsonl")


def push_examples(name: str, examples: list[dict[str, Any]]) -> int:
    """推 LangSmith Dataset（无 client 则落本地 JSONL）。返回写入条数。"""
    from ..observability import langsmith_client
    from ..config import load

    try:
        cfg = load()
        client = langsmith_client(cfg)
    except Exception:                                 # noqa: BLE001
        client = None

    if client is not None:
        try:
            ds = client.create_dataset(dataset_name=name, description="customer-helpmesh-agent eval set")
            for ex in examples:
                client.create_example(
                    inputs={"question": ex["q"]},
                    outputs={
                        "intent": ex.get("expect_intent", ""),
                        "keywords": ex.get("expect_keywords", []),
                        "tools": ex.get("expect_tools", []),
                    },
                    dataset_id=ds.id,
                )
            return len(examples)
        except Exception as e:                          # noqa: BLE001
            print(f"[dataset] langsmith push failed, fall back to local: {e}")

    p = _local_dataset_path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return len(examples)


def fetch_examples(name: str) -> list[dict[str, Any]]:
    """拉 LangSmith Dataset，失败回退本地 JSONL。"""
    from ..observability import langsmith_client
    from ..config import load

    try:
        cfg = load()
        client = langsmith_client(cfg)
    except Exception:                                 # noqa: BLE001
        client = None

    if client is not None:
        try:
            examples = list(client.list_examples(dataset_name=name))
            out = []
            for ex in examples:
                out.append({
                    "q": ex.inputs.get("question", ""),
                    "expect_intent": ex.outputs.get("intent", ""),
                    "expect_keywords": ex.outputs.get("keywords", []),
                    "expect_tools": ex.outputs.get("tools", []),
                })
            if out:
                return out
        except Exception as e:                          # noqa: BLE001
            print(f"[dataset] langsmith fetch failed, fall back to local: {e}")

    p = _local_dataset_path(name)
    if not p.is_file():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]