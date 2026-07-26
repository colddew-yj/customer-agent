"""V2: /feedback 端点（直接测端点，不触发 lifespan）。"""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def _test_yaml(tmp_path):
    cfg_path = tmp_path / "agent.yaml"
    cfg_path.write_text(
        """
llm:
  provider: fake
  model: fake
  api_key_env: _NONE_
embedding:
  provider: fake
  model: fake
  api_key_env: _NONE_
vector_store: { provider: in-memory }
intents:
  - name: refuse
    handler: builtin:refuse
    description: 拒答
""",
        encoding="utf-8",
    )
    return cfg_path


def test_feedback_endpoint_no_langsmith(monkeypatch, tmp_path):
    """无 LANGSMITH_API_KEY 时 push 返回 False，/feedback 仍 200。"""
    cfg_path = _test_yaml(tmp_path)
    monkeypatch.setenv("AGENT_CONFIG_PATH", str(cfg_path))
    monkeypatch.setenv("AGENT_ENV_PATH", "/dev/null")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    from agent import server
    server._cfg = MagicMock(langsmith=MagicMock(enabled=False, api_key_env="LANGSMITH_API_KEY"))
    server._graph = MagicMock()

    client = TestClient(server.app)
    r = client.post("/feedback", json={"run_id": "r1", "score": 1.0, "comment": "ok"})
    assert r.status_code == 200
    body = r.json()
    assert body["pushed"] is False
    assert body["run_id"] == "r1"


def test_feedback_score_out_of_range():
    """score 必须在 [0, 1]。"""
    from agent import server
    client = TestClient(server.app)
    r = client.post("/feedback", json={"run_id": "r1", "score": 1.5})
    assert r.status_code == 422