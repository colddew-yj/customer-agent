"""
LLM factory。

按 provider 名实例化 chat model，业务方改 yaml 不改代码。
"""
from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

from ..config import LLMConfig


def build_llm(cfg: LLMConfig) -> BaseChatModel:
    api_key = os.environ.get(cfg.api_key_env, "") or os.environ.get("_LLM_KEY", "")
    common = dict(
        model=cfg.model,
        temperature=cfg.temperature,
        streaming=True,
    )

    if cfg.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=api_key,
            base_url=cfg.base_url,
            **common,
        )
    if cfg.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=api_key,
            **common,
        )
    if cfg.provider == "deepseek":
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            api_key=api_key,
            base_url=cfg.base_url or "https://api.deepseek.com",
            **common,
        )
    if cfg.provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=cfg.base_url or "http://localhost:11434",
            **common,
        )
    raise ValueError(
        f"未实现的 LLM provider: {cfg.provider}\n"
        f"可选: openai | anthropic | deepseek | ollama"
    )