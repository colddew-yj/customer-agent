"""Smoke tests for config + providers factories (no LLM calls)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest


def test_config_load_minimal(tmp_path):
    cfg_path = tmp_path / "agent.yaml"
    cfg_path.write_text(
        """
llm:
  provider: openai
  model: gpt-4o-mini
  api_key_env: OPENAI_API_KEY
embedding:
  provider: openai
  model: text-embedding-3-small
  api_key_env: OPENAI_API_KEY
intents:
  - name: chat
    handler: builtin:chat
    description: 闲聊
  - name: refuse
    handler: builtin:refuse
    description: 拒答
""",
        encoding="utf-8",
    )
    os.environ["AGENT_CONFIG_PATH"] = str(cfg_path)
    os.environ["AGENT_ENV_PATH"] = "/dev/null"
    os.environ["OPENAI_API_KEY"] = "test-key"

    from agent.config import load
    cfg = load()
    assert cfg.llm.model == "gpt-4o-mini"
    assert len(cfg.intents) == 2


def test_config_validation_unknown_handler(tmp_path):
    cfg_path = tmp_path / "agent.yaml"
    cfg_path.write_text(
        """
llm: { provider: openai, model: gpt-4o-mini }
embedding: { provider: openai, model: text-embedding-3-small }
intents:
  - name: weird
    handler: builtin:nonsense
    description: x
""",
        encoding="utf-8",
    )
    os.environ["AGENT_CONFIG_PATH"] = str(cfg_path)
    os.environ["AGENT_ENV_PATH"] = "/dev/null"

    from agent.config import load
    with pytest.raises(RuntimeError, match="agent.yaml 校验失败"):
        load()


def test_provider_factory_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    from agent.config import LLMConfig
    from agent.providers import build_llm
    llm = build_llm(LLMConfig(provider="openai", model="gpt-4o-mini", api_key_env="OPENAI_API_KEY"))
    assert llm.model_name == "gpt-4o-mini"


def test_provider_factory_unknown():
    from agent.config import LLMConfig
    from agent.providers import build_llm
    with pytest.raises(ValueError, match="未实现的 LLM provider"):
        build_llm(LLMConfig(provider="nonsense", model="x", api_key_env="_NONE_"))