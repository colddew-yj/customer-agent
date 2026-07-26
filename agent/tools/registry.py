"""
P5: 工具调用注册表。

业务方在 agent.yaml `tools:` 声明端点 + auth + 模板，
agent 运行时拼 HTTP header / body，调用业务 API。

WHY 模板化：不写代码就能接业务 API。
  - auth: bearer / header:X-Name / none
  - request_template: 用 {{user_token}} {{user_id}} {{question}} 占位
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import ToolConfig


class ToolRegistry:
    def __init__(self, tools: list[ToolConfig]):
        self._tools = {t.name: t for t in tools}

    def has(self, name: str) -> bool:
        return name in self._tools

    def invoke(self, name: str, ctx: dict) -> dict:
        """调工具，ctx 含 user_token / user_id / question 等模板变量。"""
        t = self._tools.get(name)
        if not t:
            return {"success": False, "error": f"unknown tool: {name}"}

        try:
            return _call(t, ctx)
        except Exception as e:                              # noqa: BLE001
            return {"success": False, "error": str(e), "tool": name}


def _call(t: ToolConfig, ctx: dict) -> dict:
    headers: dict[str, str] = {}
    if t.auth == "bearer":
        headers[t.auth_header] = f"Bearer {ctx.get('user_token', '')}"
    elif t.auth.startswith("header:"):
        header_name = t.auth.split(":", 1)[1]
        headers[header_name] = str(ctx.get("user_id", ""))

    if t.method == "GET":
        params = _render(t.request_template or {}, ctx)
        r = httpx.get(t.endpoint, headers=headers, params=params, timeout=15.0)
    else:
        body = _render(t.request_template or {}, ctx)
        r = httpx.request(t.method, t.endpoint, headers=headers, json=body, timeout=15.0)

    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
    if t.response_path:
        for k in t.response_path.split("."):
            if isinstance(data, dict):
                data = data.get(k, {})
    return {"success": True, "data": data}


def _render(template: Any, ctx: dict) -> Any:
    if isinstance(template, str):
        for k, v in ctx.items():
            template = template.replace("{{" + k + "}}", str(v))
        return template
    if isinstance(template, dict):
        return {k: _render(v, ctx) for k, v in template.items()}
    if isinstance(template, list):
        return [_render(v, ctx) for v in template]
    return template