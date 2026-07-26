# customer-agent

通用客服 agent。基于 LangGraph + FastAPI，支持自定义 LLM provider、知识库、业务工具。

## 特性

- **配置驱动**：通过 `agent.yaml` 切换 LLM、知识源、意图、工具，无需改代码
- **多格式知识源**：md / txt / pdf / html / csv / json
- **混合检索**：向量 + BM25 + reranker（可选）
- **多 LLM**：OpenAI / DeepSeek / Anthropic / Ollama
- **真实用户上下文**：HTTP header 透传 `Authorization` + `X-User-Id`
- **流式响应**：SSE token 级输出

## 30 分钟接入

见 [docs/30min-quickstart.md](docs/30min-quickstart.md)。

## 许可证

MIT