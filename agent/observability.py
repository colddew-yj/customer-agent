"""
可观测性：LangSmith callback + 本地 trace fallback。

从 agent.yaml `langsmith:` 段读配置：
  enabled: bool
  api_key_env: str（env 名，默认 LANGSMITH_API_KEY）
  project: str
  local_trace_path: str | null

行为：
- enabled + 有 API key → 装 LangSmith tracer，上传 trace
- 其它情况 → 走本地 JSONL，零依赖
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def langsmith_callbacks(cfg) -> list:
    """返回 LangChain 兼容 callback handlers（空 list = 不上传）。"""
    ls = cfg.langsmith
    api_key = os.environ.get(ls.api_key_env, "").strip()
    if not ls.enabled or not api_key:
        return []

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = ls.project

    try:
        from langchain_core.tracers import LangChainTracer
        return [LangChainTracer(project_name=ls.project)]
    except ImportError:
        return []


def _local_trace_path(cfg) -> Path | None:
    p = getattr(cfg.langsmith, "local_trace_path", None) if cfg else None
    if not p:
        return None
    path = Path(p)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_local_trace(cfg, record: dict[str, Any]) -> None:
    """追加一条 JSONL。失败仅打印不抛。"""
    path = _local_trace_path(cfg)
    if path is None:
        return
    try:
        record.setdefault("ts", time.time())
        record.setdefault("project", cfg.langsmith.project)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:                              # noqa: BLE001
        print(f"[trace] failed to write: {e}")


@contextmanager
def trace_run(cfg, run_name: str, **fields: Any) -> Iterator[dict]:
    """同步计时 context manager。失败不抛。

    用法：
        with trace_run(cfg, "graph_astream_tokens", thread_id=...):
            ...
    """
    start = time.perf_counter()
    record: dict[str, Any] = {"run_name": run_name, **fields}
    try:
        yield record
        record["status"] = "ok"
    except Exception as e:                              # noqa: BLE001
        record["status"] = "error"
        record["error"] = repr(e)
    finally:
        record["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        append_local_trace(cfg, record)


# ─────────────────────────────────────────────────────────────────
# V2: LangSmith Client + Feedback
# ─────────────────────────────────────────────────────────────────

def langsmith_client(cfg):
    """返回 langsmith.Client（lazy import，缺包返 None）。"""
    ls = cfg.langsmith
    api_key = os.environ.get(ls.api_key_env, "").strip()
    if not ls.enabled or not api_key:
        return None
    try:
        from langsmith import Client
        return Client(api_key=api_key, api_url="https://api.smith.langchain.com")
    except ImportError:
        return None


def push_feedback(cfg, run_id: str, score: float, comment: str = "") -> bool:
    """业务方 /feedback 端点用：把用户评分写回 LangSmith run。

    返回 True 表示成功，False 表示 LangSmith 未启用 / 缺包 / 异常。
    """
    client = langsmith_client(cfg)
    if client is None:
        return False
    try:
        client.create_feedback(run_id=run_id, key="user_score", score=score, comment=comment)
        return True
    except Exception as e:                              # noqa: BLE001
        print(f"[langsmith feedback] failed: {e}")
        return False