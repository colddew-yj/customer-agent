"""
P7: 本地 trace 落盘（LangSmith 的零依赖替代）。

WHY:
  - LangSmith SaaS 需 API key，开发期不一定有
  - 即使有 API key，trace 上传也是异步、不一定能实时看
  - 本地 JSONL 落盘 = 零依赖、可 grep、可永久回放
  - 真上线时换成 LangSmithCallbackHandler（interface 一致）

WHAT 记录：
  - timestamp / thread_id / intent / route / latency_ms
  - 各节点耗时（classify / retrieve / generate / query_account / generate_query_account）
  - retrieval 召回的 chunk 文件名 + 相似度
  - LLM 调用次数 + token 数（从 LangChain callback 取）
  - 最终答案
"""
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .config import settings


def _ensure_trace_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def append_trace(record: dict[str, Any]) -> None:
    """追加一条 trace 到 JSONL。失败不抛（trace 不能影响主流程）。"""
    try:
        _ensure_trace_dir(settings.LOCAL_TRACE_PATH)
        record.setdefault("ts", time.time())
        record.setdefault("project", settings.LANGSMITH_PROJECT)
        with open(settings.LOCAL_TRACE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:  # pragma: no cover
        # trace 失败只打印，不抛——业务不受影响
        print(f"[trace] failed to write: {e}")


@contextmanager
def trace_run(run_name: str, **fields: Any):
    """同步计时 context manager。包住一段代码，记录耗时 + 任意 fields。

    用法：
        with trace_run("graph_invoke", question=..., thread_id=...):
            result = graph.invoke(...)
    """
    start = time.perf_counter()
    record: dict[str, Any] = {"run_name": run_name, **fields}
    try:
        yield record  # 让内部代码往 record 写更多字段
        record["status"] = "ok"
    except Exception as e:
        record["status"] = "error"
        record["error"] = repr(e)
        raise
    finally:
        record["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        append_trace(record)


def langsmith_callbacks() -> list:
    """返回 LangChain 兼容的 callback 列表。

    - LANGSMITH_TRACING=true 且有 API key → 用 LangSmith 的 LangChainTracer
    - 否则 → 空列表（不开 trace 上传，但本地 JSONL 仍然记录）
    """
    if not settings.LANGSMITH_TRACING or not settings.LANGSMITH_API_KEY:
        return []
    # 延迟导入避免没装 langsmith 时 import 失败
    from langchain_core.tracers import LangChainTracer
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGSMITH_PROJECT)
    return [LangChainTracer(project_name=settings.LANGSMITH_PROJECT)]