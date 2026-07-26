"""
P6: FastAPI 服务。

端点：
  POST /chat    SSE 流式对话
  POST /ingest  重新入库知识
  GET  /health  健康检查
  GET  /        服务信息
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import AgentConfig, load as load_config
from .graph import build_graph
from .knowledge.ingest import run as run_ingest
from .runner import astream_tokens


_graph = None
_cfg: AgentConfig | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _graph, _cfg
    _cfg = load_config()
    _graph = build_graph(_cfg)
    yield


app = FastAPI(title="customer-helpmesh-agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    user_id: str | None = None


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _heartbeat(stop: asyncio.Event, queue: asyncio.Queue) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=15)
            break
        except asyncio.TimeoutError:
            await queue.put({"type": "ping"})


@app.post("/chat")
async def chat(
    req: ChatRequest,
    authorization: str = Header(default="", alias="Authorization"),
    x_user_id: str = Header(default="", alias="X-User-Id"),
    x_thread_id: str = Header(default="default", alias="X-Thread-Id"),
):
    user_token = authorization.removeprefix("Bearer ").strip()
    user_id = x_user_id or (req.user_id or "")
    thread_id = x_thread_id or "default"

    queue: asyncio.Queue = asyncio.Queue()
    stop = asyncio.Event()

    async def drain():
        try:
            async for event in astream_tokens(
                graph=_graph,
                cfg=_cfg,
                question=req.message,
                user_token=user_token,
                user_id=user_id,
                thread_id=thread_id,
            ):
                await queue.put(event)
        finally:
            stop.set()
            await queue.put({"type": "_sentinel"})

    gen_task = asyncio.create_task(drain())
    hb_task = asyncio.create_task(_heartbeat(stop, queue))

    async def stream():
        try:
            while True:
                event = await queue.get()
                if event.get("type") == "_sentinel":
                    break
                yield _sse(event)
        finally:
            stop.set()
            gen_task.cancel()
            hb_task.cancel()
            await asyncio.gather(gen_task, hb_task, return_exceptions=True)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/ingest")
async def ingest() -> dict:
    stats = run_ingest(_cfg, Path(".").resolve())
    return stats


class FeedbackRequest(BaseModel):
    run_id: str
    score: float = Field(..., ge=0, le=1)
    comment: str = ""


@app.post("/feedback")
async def feedback(req: FeedbackRequest) -> dict:
    """V2: 业务方把用户评分 / 反馈透传到 LangSmith run。"""
    from .observability import push_feedback
    ok = push_feedback(_cfg, req.run_id, req.score, req.comment)
    return {"pushed": ok, "run_id": req.run_id}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict:
    return {
        "service": "customer-helpmesh-agent",
        "version": "0.1.0",
        "intents": [it.name for it in (_cfg.intents if _cfg else [])],
    }