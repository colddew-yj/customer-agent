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
    if cfg.provider == "fake":
        # 测试 / dev：固定回复。classifier JSON 也走同一 LLM（每次 invoke 循环 responses）
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage
        return FakeMessagesListChatModel(responses=[
            AIMessage(content='{"intent": "faq", "confidence": 0.9}'),
            AIMessage(content="这是一个 fake 测试回复。"),
            AIMessage(content="这是第二条 fake 回复。"),
        ])
    raise ValueError(
        f"未实现的 LLM provider: {cfg.provider}\n"
        f"可选: openai | anthropic | deepseek | ollama | fake"
    )