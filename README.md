# customer-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3.34-orange.svg)](https://langchain-ai.github.io/langgraph/)

通用客服 agent。基于 LangGraph + FastAPI，支持自定义 LLM provider、知识库、业务工具。

## 30 秒跑通

```bash
docker compose up -d
curl -X POST http://localhost:8000/ingest | jq
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"怎么充值"}'
```

## 特性

- **配置驱动**：通过 `agent.yaml` 切换 LLM、知识源、意图、工具，无需改代码
- **多格式知识源**：md / txt / pdf / html / csv / json / jsonl
- **混合检索**：向量 + BM25（jieba / whitespace tokenizer）+ 可选 reranker
- **多 LLM**：OpenAI / Anthropic / DeepSeek / Ollama / Azure OpenAI
- **真实用户上下文**：HTTP header 透传 `Authorization` + `X-User-Id`
- **流式响应**：SSE token 级输出，前端逐字显示
- **可观测**：LangSmith trace + 本地 fallback

## 截图

> 待补：聊天面板 / RAG 检索流程 / LangSmith trace / SSE 流

<!-- TODO: 加 `docs/screenshots/chat.png`、`docs/screenshots/ingest.png`、`docs/screenshots/langsmith.png`，引用方式 ![chat](docs/screenshots/chat.png) -->

## 安装

### Docker（推荐）

```bash
git clone https://github.com/<org>/customer-agent
cd customer-agent
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env       # 填 OPENAI_API_KEY
docker compose up -d
curl -X POST http://localhost:8000/ingest
```

### 裸 Python（dev / 本地）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env
customer-agent                       # 默认 0.0.0.0:8000
```

## 30 分钟接入指南

完整步骤：[docs/30min-quickstart.md](docs/30min-quickstart.md)

核心 6 步：
1. 准备知识文档目录
2. 改 `agent.yaml`（LLM / 知识源 / 意图 / 工具）
3. 配 `.env`（API key）
4. `docker compose up -d` + `POST /ingest`
5. 写业务 BFF（参考 `examples/bff/nextjs/route.ts`）
6. curl 验证

## 文档

- [30 分钟接入指南](docs/30min-quickstart.md)
- [知识源配置](docs/knowledge-sources.md)
- [工具配置](docs/tools.md)
- [LLM providers](docs/llm-providers.md)
- [贡献指南](CONTRIBUTING.md)

## 架构

```
Browser / Frontend
       │
       ▼  POST /chat (SSE)
Next.js BFF (透传 Authorization + X-User-Id)
       │
       ▼  HTTP
customer-agent (FastAPI)
       │
       ├─ LangGraph: classify → {faq | account | complaint | chat | refuse}
       │
       ├─ RAG pipeline: loader → splitter → embedding → Chroma → hybrid retriever
       │
       └─ Tool registry: 调业务 API（余额 / 订单 / 工单）
```

## 5 个内置意图

| 意图 | handler | 说明 |
|---|---|---|
| `faq` | `builtin:faq` | 业务问答（RAG） |
| `account` | `builtin:account` | 实时数据（工具调用） |
| `complaint` | `builtin:complaint` | 用户不满（不检索） |
| `chat` | `builtin:chat` | 闲聊（不检索） |
| `refuse` | `builtin:refuse` | 跟业务无关（预设话术） |

业务方在 `agent.yaml` `intents:` 列表删改；增新 handler 见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 快速 demo

```bash
# 健康检查
curl -fsS http://localhost:8000/health

# 业务问答（不需登录）
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"套餐多少钱？"}'

# 实时数据（需业务 token）
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <user-token>' \
  -H 'X-User-Id: 123' \
  -d '{"message":"我的余额是多少？"}'
```

## 路线图

V1（当前）：配置驱动 + 5 builtin intent + 多格式 RAG + 多 LLM + 工具调用 + SSE 流

V2 计划：
- 远程知识源（Notion / S3 / Confluence）
- Rerank 默认开
- 自定义 intent handler 插件目录（`~/.customer-agent/handlers/`）
- 评估集 + few-shot 自动选择
- 多租户 collection 隔离

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE)