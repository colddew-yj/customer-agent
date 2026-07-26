"""Tests for tool registry template rendering + invocation."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from agent.config import ToolConfig
from agent.tools.registry import ToolRegistry, _render


def test_template_render_string():
    out = _render("Bearer {{user_token}}", {"user_token": "abc"})
    assert out == "Bearer abc"


def test_template_render_dict():
    out = _render({"x": "{{user_id}}", "y": 1}, {"user_id": "42"})
    assert out == {"x": "42", "y": 1}


def test_unknown_tool_returns_error():
    reg = ToolRegistry([])
    out = reg.invoke("nope", {})
    assert out["success"] is False


def test_invoke_real_endpoint(monkeypatch):
    import httpx

    class FakeResp:
        headers = {"content-type": "application/json"}
        def json(self):
            return {"data": {"balance": 100}}

    called = {}

    def fake_get(url, headers, params, timeout):
        called["url"] = url
        called["headers"] = headers
        called["params"] = params
        return FakeResp()

    monkeypatch.setattr(httpx, "get", fake_get)

    reg = ToolRegistry([
        ToolConfig(
            name="balance",
            endpoint="https://api.example.com/balance",
            method="GET",
            auth="bearer",
            response_path="data.balance",
        )
    ])
    out = reg.invoke("balance", {"user_token": "tok-1", "user_id": "1"})
    assert out["success"] is True
    assert out["data"] == 100
    assert called["headers"]["Authorization"] == "Bearer tok-1"