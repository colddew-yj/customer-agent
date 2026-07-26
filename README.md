# customer-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.3.34-orange.svg)](https://langchain-ai.github.io/langgraph/)

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## English

A **general-purpose customer service agent** — one binary that adapts to many scenarios through configuration, not code changes.

### Use cases

The same agent serves any customer service domain by swapping its `agent.yaml`:

- **Retail / e-commerce** — FAQ on returns, refunds, shipping, inventory
- **SaaS tech support** — API errors, SDK usage, rate-limit troubleshooting
- **Banking / insurance** — account queries, policy lookup, complaint triage (all through your own APIs)
- **Education / training** — curriculum Q&A, assignment help, scheduling
- **Internal IT / HR** — leave policies, ticket routing, password resets
- **Custom domains** — drop your knowledge files in, wire your APIs to `tools:`, define your intents

The configuration is the product:

| Concern | How to swap | Where |
|---|---|---|
| LLM provider | `llm.provider` (openai / anthropic / deepseek / ollama / azure) | `agent.yaml` |
| Embedding model | `embedding.provider` + `embedding.model` | `agent.yaml` |
| Knowledge sources | `connector: local / s3 / git / notion` per source | `agent.yaml` `knowledge.sources:` |
| Document formats | `format: md / pdf / docx / xlsx / pdf_advanced / ...` per source | `agent.yaml` |
| Retrieval strategy | `retriever.strategy: vector / hybrid / multiquery / hyde` | `agent.yaml` |
| Intents (FAQ / account / complaint / ...) | `intents:` list with `builtin:*` or custom handler paths | `agent.yaml` |
| Business APIs | `tools:` list with endpoint + auth + templates | `agent.yaml` |
| Custom Python behavior | drop a `.py` file in `~/.customer-agent/handlers/` | filesystem |
| Observability | `langsmith.enabled: true` + `LANGSMITH_API_KEY` | `agent.yaml` + env |

No code changes. No rebuild. Edit YAML, restart, done.

### Features

- **Config-driven** — switch LLM / knowledge / intents / tools through `agent.yaml`
- **Multiple knowledge sources** — local files, S3, Git repos, Notion databases
- **Multi-format documents** — md / txt / pdf / html / csv / json / jsonl / docx / xlsx
- **OCR + Vision fallback** — scanned PDFs and image-only content still get indexed
- **Hybrid retrieval** — vector + BM25, optional reranker, RRF fusion
- **Multiple LLM providers** — OpenAI / Anthropic / DeepSeek / Ollama / Azure OpenAI
- **Real user context** — HTTP headers (`Authorization` + `X-User-Id`) forwarded to tool calls
- **Token-level streaming** — SSE output, frontend displays character by character
- **LangSmith observability** — trace + evaluation + feedback
- **Custom intent handlers** — drop a Python file into `~/.customer-agent/handlers/`, no fork needed
- **Drop-in chat widget** — React + Tailwind component, ready to copy-paste
- **Plug-and-play BFF examples** — Next.js / Express / FastAPI templates

### 30-second quick start

```bash
docker compose up -d
curl -X POST http://localhost:8000/ingest | jq
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"How do I recharge?"}'
```

### Install

**Docker (recommended)**

```bash
git clone https://github.com/colddew-yj/customer-agent
cd customer-agent
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env       # fill in your OPENAI_API_KEY
docker compose up -d
curl -X POST http://localhost:8000/ingest
```

**Bare Python (local dev)**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env
customer-agent                       # listens on 0.0.0.0:8000
```

### 30-minute integration guide

Full walk-through: [docs/30min-quickstart.md](docs/30min-quickstart.md)

Six steps:
1. Prepare your knowledge documents
2. Edit `agent.yaml` (LLM / knowledge sources / intents / tools)
3. Configure `.env` (API keys)
4. `docker compose up -d` + `POST /ingest`
5. Write your BFF (see `examples/bff/nextjs/route.ts`)
6. Verify with `curl`

### Knowledge sources

`agent.yaml` supports four connectors out of the box — local files, S3-compatible storage, Git repositories, and Notion databases:

```yaml
knowledge:
  sources:
    - name: faq-local                       # local directory
      path: ./knowledge/faq
      format: md

    - name: wiki-s3                         # S3 / R2 / MinIO / Aliyun OSS
      connector: s3
      connector_config:
        bucket: company-wiki
        prefix: docs/
        endpoint_url: https://s3.amazonaws.com
        aws_key_env: AWS_ACCESS_KEY_ID
        aws_secret_env: AWS_SECRET_ACCESS_KEY

    - name: kb-git                          # Git repo
      connector: git
      connector_config:
        repo_url: https://github.com/me/kb.git
        branch: main
        path_filter: "docs/*.md"

    - name: faq-notion                      # Notion database
      connector: notion
      connector_config:
        api_key_env: NOTION_API_KEY
        database_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Document formats

| Format | Loader | Notes |
|---|---|---|
| md / txt | TextLoader | default |
| pdf | PyMuPDFLoader | falls back to PyPDFLoader; double-column friendly |
| html / htm | BSHTMLLoader | |
| csv | CSVLoader | one row per Document |
| json / jsonl | JSONLoader | jq schema `.` |
| docx | custom (python-docx) | paragraphs + tables |
| xlsx | custom (openpyxl) | one row per Document |

OCR (tesseract) + Vision LLM fallback handles scanned PDFs and image-only content via `pdf_advanced`.

### Retrieval strategies

Choose `strategy` in `agent.yaml`:

- `vector` — pure vector retrieval
- `hybrid` — vector + BM25 with RRF fusion (default)
- `multiquery` — LangChain MultiQueryRetriever (LLM generates query variants)
- `hyde` — Hypothetical Document Embeddings

### Built-in intents

| Intent | Handler | Description |
|---|---|---|
| `faq` | `builtin:faq` | Knowledge-base Q&A (RAG) |
| `account` | `builtin:account` | Realtime data (tool call) |
| `complaint` | `builtin:complaint` | User complaints (no retrieval) |
| `chat` | `builtin:chat` | Small talk (no retrieval) |
| `refuse` | `builtin:refuse` | Out-of-scope (preset reply) |

Add or remove intents in `agent.yaml`'s `intents:` list. Drop custom handlers in `~/.customer-agent/handlers/<name>.py` — no need to fork the repo.

### Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER / FRONTEND                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  chat-widget (examples/chat-widget/)                                │  │
│  │  • ChatWidget.tsx — drop-in React component                          │  │
│  │  • useChatStream.ts — SSE consumer hook (independently usable)       │  │
│  │  • storage.ts — localStorage (session id + history)                  │  │
│  │  • styles.css (ca-cw-* prefix, CSS-overridable)                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │  POST /api/agent/chat  (SSE: data: {"type":"token","content":"..."})
              │  Headers: Authorization (user token) + X-User-Id
              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS BFF  (your code)                            │
│  examples/bff/nextjs/route.ts  (template)                                  │
│  • Reads your app's session cookie                                          │
│  • Forwards Authorization + X-User-Id + X-Thread-Id to agent                │
│  • Streams agent SSE back to browser (no buffering)                          │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │  HTTP
              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    customer-agent  (FastAPI :8000)                         │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                      FastAPI  (server.py)                      │    │
│   │  POST /chat    → SSE stream                                   │    │
│   │  POST /ingest  → re-index knowledge                          │    │
│   │  POST /feedback → push user score to LangSmith run           │    │
│   │  GET  /health   → liveness probe                             │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                     LangGraph  (graph.py)                      │    │
│   │  classify_node  (LLM picks intent)                            │    │
│   │       │                                                        │    │
│   │       ▼                                                        │    │
│   │  ┌───────────────────────────────────────────────────────┐    │    │
│   │  │ Intent Handlers (skills/ — 5 builtin + custom)        │    │    │
│   │  │  faq        — RAG → answer                             │    │    │
│   │  │  account    — ToolRegistry.invoke(...) → answer         │    │    │
│   │  │  complaint  — LLM direct (empathy prompt)             │    │    │
│   │  │  chat       — LLM direct (small-talk prompt)           │    │    │
│   │  │  refuse     — preset reply (no LLM)                    │    │    │
│   │  └───────────────────────────────────────────────────────┘    │    │
│   │       │  custom:  ~/.customer-agent/handlers/<name>.py:build    │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                   Retrieval Layer                              │    │
│   │  RetrieverConfig.strategy: vector | hybrid | multiquery | hyde  │    │
│   │                                                                │    │
│   │  ┌────────────── Knowledge Pipeline ──────────────────────┐    │    │
│   │  │ Connector (local / s3 / git / notion)                  │    │    │
│   │  │   ↓  sync()                                            │    │    │
│   │  │ Loader (md / pdf / html / csv / json / docx / xlsx /    │    │    │
│   │  │        pdf_advanced=PDF+OCR+Vision fallback)            │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Splitter (RecursiveCharacterTextSplitter)              │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Embedding (openai / huggingface / ollama / fake)       │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Vector Store (chroma / in-memory) + BM25 chunks (pkl) │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Retriever:  vector + BM25 → RRF / weighted              │    │    │
│   │  │            multiquery / hyde (LLM-generated variants)   │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Reranker (FlagEmbedding cross-encoder, default-on)     │    │    │
│   │  └─────────────────────────────────────────────────────────┘    │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  ToolRegistry  (tools/registry.py)             │    │
│   │  • HTTP call with bearer / header:X-Name / none auth          │    │
│   │  • Template rendering ({{user_token}} / {{user_id}} / ...)      │    │
│   │  • Response path extraction (e.g. data.balance)                │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  Observability  (observability.py)             │    │
│   │  • LangChainTracer → LangSmith SaaS (when enabled + key set)   │    │
│   │  • Local JSONL trace fallback                                  │    │
│   │  • push_feedback(run_id, score) → LangSmith Client            │    │
│   │  • Trace run-on-dataset eval (agent.eval.runner)              │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  Configuration  (config.py)                    │    │
│   │  AgentConfig (pydantic) — single source of truth                │    │
│   │  • llm / embedding / vector_store                              │    │
│   │  • retriever (strategy / fusion / rerank)                      │    │
│   │  • knowledge.sources[].connector / format / ocr / vision_llm   │    │
│   │  • tools[] (endpoint / auth / request_template)                │    │
│   │  • intents[].handler (builtin:xxx | path.py:build)             │    │
│   │  • server (cors / heartbeat)                                   │    │
│   │  • langsmith.evaluation (dataset_name / evaluators)             │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                                                            │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌──────────────────────────┐   ┌────────────────────────────────────────────┐
│   LLM Providers (业务方) │   │   Observability (optional)                  │
│   • OpenAI                │   │   • LangSmith SaaS (client + dataset)     │
│   • Anthropic             │   │   • Local JSONL trace                      │
│   • DeepSeek              │   │   • LLM-as-judge evaluator                 │
│   • Ollama (local)        │   └────────────────────────────────────────────┘
│   • Azure OpenAI          │
│   业务方自己 key / 自己付 │    ┌────────────────────────────────────────────┐
└──────────────────────────┘   │   Storage (per agent instance)              │
                              │   • ./data/chroma (vector store)            │
                              │   • ./data/bm25_chunks.pkl (BM25 chunks)     │
                              │   • ./data/checkpoints.db (multi-turn)     │
                              │   • ./data/cache/<source>/ (remote cache)   │
                              └────────────────────────────────────────────┘
```

**Request flow** (one `/chat` request):

```
Browser → ChatWidget
   └─ fetch /api/agent/chat (SSE)
        └─ BFF (cookie → access token)
             └─ POST /chat (Authorization + X-User-Id + X-Thread-Id)
                  └─ agent/server.py
                       └─ runner.astream_tokens(graph, cfg, ...)
                            ├─ graph = StateGraph(classify → intent handler)
                            │    └─ retriever / tool registry
                            │         └─ LangSmith tracer
                            └─ SSE 事件流：sources / token / done
```

### Quick demo

```bash
# health
curl -fsS http://localhost:8000/health

# Q&A (no login required)
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"套餐多少钱？"}'

# realtime data (requires user token)
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <user-token>' \
  -H 'X-User-Id: 123' \
  -d '{"message":"我的余额是多少？"}'

# Feedback (writes back to LangSmith run)
curl -X POST http://localhost:8000/feedback \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"abc","score":1,"comment":"good"}'
```

### Drop-in chat widget

React + Tailwind component lives in [`examples/chat-widget/`](examples/chat-widget/). Three usage modes:

```tsx
// 1. Default component
import { ChatWidget } from "./chat-widget";
<ChatWidget endpoint="/api/agent/chat" userId={session.userId} onClose={...} />

// 2. Override styles via CSS specificity
.ca-cw-header { background-color: #ff6b6b; }

// 3. Replace UI entirely, reuse SSE hook
import { useChatStream } from "./chat-widget";
const { messages, send, isTyping } = useChatStream({ endpoint, userId, threadId });
```

### Documentation

- [30-minute quick start](docs/30min-quickstart.md)
- [Knowledge sources & connectors](docs/knowledge-sources.md)
- [Tool configuration](docs/tools.md)
- [LLM providers](docs/llm-providers.md)
- [Contributing](CONTRIBUTING.md)

**License**

[MIT](LICENSE)

---

<a name="中文"></a>

## 中文

通用客服 agent —— 同一份代码，靠配置适配各种客服场景。

### 适用场景

agent 本身不绑死任何业务领域，只提供可配置的 LLM + RAG + 工具调用框架。不同场景换 `agent.yaml` 即可：

- **电商客服** — 退换货 / 物流 / 库存 FAQ
- **SaaS 技术支持** — API 报错 / SDK 用法 / 限流排查
- **银行 / 保险** — 账户查询 / 保单检索 / 投诉分流（接自家 API）
- **教育 / 培训** — 课程答疑 / 作业辅助
- **企业内部 IT / HR** — 请假政策 / 工单路由 / 密码重置
- **自定义场景** — 丢文档、配工具、定义意图就行

配置即产品：

| 维度 | 怎么换 | 位置 |
|---|---|---|
| LLM provider | `llm.provider` (openai / anthropic / deepseek / ollama / azure) | `agent.yaml` |
| Embedding 模型 | `embedding.provider` + `embedding.model` | `agent.yaml` |
| 知识源 | `connector: local / s3 / git / notion` 每条独立配 | `agent.yaml` `knowledge.sources:` |
| 文档格式 | `format: md / pdf / docx / xlsx / pdf_advanced / ...` | `agent.yaml` |
| 检索策略 | `retriever.strategy: vector / hybrid / multiquery / hyde` | `agent.yaml` |
| 意图 | `intents:` 列表（`builtin:*` 或自定义 handler 路径） | `agent.yaml` |
| 业务 API | `tools:` 列表（endpoint + auth + 模板） | `agent.yaml` |
| 自定义 Python 逻辑 | 把 `.py` 丢进 `~/.customer-agent/handlers/` | 文件系统 |
| 可观测 | `langsmith.enabled: true` + `LANGSMITH_API_KEY` | `agent.yaml` + env |

不改代码，不重新构建。改 yaml、重启、完成。

### 特性

- **配置驱动**：通过 `agent.yaml` 切换 LLM / 知识源 / 意图 / 工具，无需改代码
- **多知识源**：本地目录、S3 兼容存储、Git 仓库、Notion database
- **多格式文档**：md / txt / pdf / html / csv / json / jsonl / docx / xlsx
- **OCR + Vision 兜底**：扫描件 PDF / 图片内容也能入库
- **混合检索**：向量 + BM25，可选 reranker，RRF 融合
- **多 LLM**：OpenAI / Anthropic / DeepSeek / Ollama / Azure OpenAI
- **真实用户上下文**：HTTP header 透传 `Authorization` + `X-User-Id` 给 tool 调用
- **Token 级流式**：SSE 输出，前端逐字显示
- **LangSmith 可观测**：trace + 评估 + 反馈
- **自定义 handler 插件**：业务方把 .py 丢到 `~/.customer-agent/handlers/` 即可，无需 fork
- **开箱即用 chat-widget**：React + Tailwind 组件，可直接 copy 走
- **BFF 示例**：Next.js / Express / FastAPI 模板

### 30 秒跑通

```bash
docker compose up -d
curl -X POST http://localhost:8000/ingest | jq
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"怎么充值"}'
```

### 安装

**Docker（推荐）**

```bash
git clone https://github.com/colddew-yj/customer-agent
cd customer-agent
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env       # 填 OPENAI_API_KEY
docker compose up -d
curl -X POST http://localhost:8000/ingest
```

**裸 Python（本地 dev）**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env
customer-agent                       # 默认 0.0.0.0:8000
```

### 30 分钟接入指南

完整步骤：[docs/30min-quickstart.md](docs/30min-quickstart.md)

核心 6 步：
1. 准备知识文档
2. 改 `agent.yaml`（LLM / 知识源 / 意图 / 工具）
3. 配 `.env`（API key）
4. `docker compose up -d` + `POST /ingest`
5. 写业务 BFF（参考 `examples/bff/nextjs/route.ts`）
6. curl 验证

### 知识源

`agent.yaml` `knowledge.sources:` 内置 4 种 connector：本地目录、S3 兼容存储、Git 仓库、Notion database：

```yaml
knowledge:
  sources:
    - name: faq-local                       # 本地目录
      path: ./knowledge/faq
      format: md

    - name: wiki-s3                         # S3 / R2 / MinIO / 阿里云 OSS
      connector: s3
      connector_config:
        bucket: company-wiki
        prefix: docs/
        endpoint_url: https://s3.amazonaws.com
        aws_key_env: AWS_ACCESS_KEY_ID
        aws_secret_env: AWS_SECRET_ACCESS_KEY

    - name: kb-git                          # Git 仓库
      connector: git
      connector_config:
        repo_url: https://github.com/me/kb.git
        branch: main
        path_filter: "docs/*.md"

    - name: faq-notion                      # Notion database
      connector: notion
      connector_config:
        api_key_env: NOTION_API_KEY
        database_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 文档格式

| 格式 | Loader | 备注 |
|---|---|---|
| md / txt | TextLoader | 默认 |
| pdf | PyMuPDFLoader | fallback PyPDFLoader；双栏 PDF 友好 |
| html / htm | BSHTMLLoader | |
| csv | CSVLoader | 每行一个 Document |
| json / jsonl | JSONLoader | jq schema `.` |
| docx | 自定义（python-docx） | 段落 + 表格 |
| xlsx | 自定义（openpyxl） | 每行一个 Document |

OCR（tesseract）+ Vision LLM 兜底（`pdf_advanced`）处理扫描件 PDF 与图片内容。

### 检索策略

`agent.yaml` `retriever.strategy` 选：

- `vector` — 纯向量
- `hybrid` — 向量 + BM25，RRF 融合（默认）
- `multiquery` — langchain MultiQueryRetriever（LLM 自动生成 query 变体）
- `hyde` — Hypothetical Document Embeddings

### 内置意图

| 意图 | handler | 说明 |
|---|---|---|
| `faq` | `builtin:faq` | 业务问答（RAG） |
| `account` | `builtin:account` | 实时数据（调工具） |
| `complaint` | `builtin:complaint` | 用户不满（不检索） |
| `chat` | `builtin:chat` | 闲聊（不检索） |
| `refuse` | `builtin:refuse` | 无关问题（预设话术） |

业务方在 `agent.yaml` `intents:` 增删改。自定义 handler 丢到 `~/.customer-agent/handlers/<name>.py` 即可，无需 fork 仓。

### 架构

```
浏览器 / 前端
       │
       ▼  POST /chat (SSE)
Next.js BFF（透传 Authorization + X-User-Id）
       │
       ▼  HTTP
customer-agent (FastAPI)
       │
       ├─ LangGraph：classify → {faq | account | complaint | chat | refuse}
       │
       ├─ 知识：connector → loader → splitter → embedding → Chroma → hybrid retriever
       │
       └─ 工具：调业务 API（订单 / 余额 / 工单）
```

### 快速 demo

```bash
# 健康检查
curl -fsS http://localhost:8000/health

# 业务问答（无需登录）
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"套餐多少钱？"}'

# 实时数据（需业务 token）
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <user-token>' \
  -H 'X-User-Id: 123' \
  -d '{"message":"我的余额是多少？"}'

# 反馈（写回 LangSmith run）
curl -X POST http://localhost:8000/feedback \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"abc","score":1,"comment":"good"}'
```

### 开箱即用 chat-widget

React + Tailwind 组件在 [`examples/chat-widget/`](examples/chat-widget/)。3 种用法：

```tsx
// 1. 默认组件
import { ChatWidget } from "./chat-widget";
<ChatWidget endpoint="/api/agent/chat" userId={session.userId} onClose={...} />

// 2. CSS specificity 覆盖样式
.ca-cw-header { background-color: #ff6b6b; }

// 3. 复用 SSE hook 自写 UI
import { useChatStream } from "./chat-widget";
const { messages, send, isTyping } = useChatStream({ endpoint, userId, threadId });
```

### 文档

- [30 分钟接入指南](docs/30min-quickstart.md)
- [知识源配置](docs/knowledge-sources.md)
- [工具配置](docs/tools.md)
- [LLM providers](docs/llm-providers.md)
- [贡献指南](CONTRIBUTING.md)

### 技术架构

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              浏览器 / 前端                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  chat-widget（examples/chat-widget/）                              │  │
│  │  • ChatWidget.tsx — 开箱即用 React 组件                            │  │
│  │  • useChatStream.ts — SSE 消费 hook（可独立用）                    │  │
│  │  • storage.ts — localStorage（session id + 历史）                   │  │
│  │  • styles.css（ca-cw-* 前缀，可覆盖）                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │  POST /api/agent/chat  (SSE: data: {"type":"token","content":"..."})
              │  Headers: Authorization（用户 token）+ X-User-Id
              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        业务方 BFF（自家代码）                              │
│  examples/bff/nextjs/route.ts（模板）                                    │
│  • 读自家 cookie / session                                              │
│  • 透传 Authorization + X-User-Id + X-Thread-Id 到 agent                  │
│  • SSE 流透传给浏览器（不缓冲）                                          │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │  HTTP
              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    customer-agent（FastAPI :8000）                       │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                      FastAPI（server.py）                     │    │
│   │  POST /chat    → SSE 流                                      │    │
│   │  POST /ingest  → 重新入库                                    │    │
│   │  POST /feedback → 用户评分写回 LangSmith run                  │    │
│   │  GET  /health   → 健康检查                                   │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                     LangGraph（graph.py）                     │    │
│   │  classify_node（LLM 选意图）                                  │    │
│   │       │                                                        │    │
│   │       ▼                                                        │    │
│   │  ┌───────────────────────────────────────────────────────┐    │    │
│   │  │ Intent Handlers（skills/ — 5 内置 + 自定义）         │    │    │
│   │  │  faq        — RAG → 回答                              │    │    │
│   │  │  account    — ToolRegistry.invoke() → 回答            │    │    │
│   │  │  complaint  — LLM 直答（共情 prompt）                 │    │    │
│   │  │  chat       — LLM 直答（闲聊 prompt）                   │    │    │
│   │  │  refuse     — 预设话术（不调 LLM）                     │    │    │
│   │  └───────────────────────────────────────────────────────┘    │    │
│   │       │  自定义：~/.customer-agent/handlers/<name>.py:build     │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                     检索层                                     │    │
│   │  RetrieverConfig.strategy: vector | hybrid | multiquery | hyde │    │
│   │                                                                │    │
│   │  ┌────────────────────── 知识管线 ──────────────────────┐    │    │
│   │  │ Connector（local / s3 / git / notion）                  │    │    │
│   │  │   ↓  sync()                                            │    │    │
│   │  │ Loader（md / pdf / html / csv / json / docx / xlsx / │    │    │
│   │  │        pdf_advanced=PDF+OCR+Vision 兜底）              │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Splitter（RecursiveCharacterTextSplitter）              │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Embedding（openai / huggingface / ollama / fake）       │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Vector Store（chroma / in-memory）+ BM25 chunks（pkl） │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Retriever：vector + BM25 → RRF / weighted               │    │    │
│   │  │            multiquery / hyde（LLM 生成变体）             │    │    │
│   │  │   ↓                                                     │    │    │
│   │  │ Reranker（FlagEmbedding cross-encoder，默认开）         │    │    │
│   │  └─────────────────────────────────────────────────────────┘    │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  ToolRegistry（tools/registry.py）             │    │
│   │  • HTTP 调用（bearer / header:X-Name / none 鉴权）         │    │
│   │  • 模板渲染（{{user_token}} / {{user_id}} / ...）              │    │
│   │  • 响应字段提取（如 data.balance）                              │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                              │                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  Observability（observability.py）             │    │
│   │  • LangChainTracer → LangSmith SaaS（启用 + 设 key 时）        │    │
│   │  • 本地 JSONL trace fallback                                    │    │
│   │  • push_feedback(run_id, score) → LangSmith Client             │    │
│   │  • 跑评估集 trace（agent.eval.runner）                        │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                  配置（config.py）                              │    │
│   │  AgentConfig（pydantic）— 单一事实来源                          │    │
│   │  • llm / embedding / vector_store                              │    │
│   │  • retriever（strategy / fusion / rerank）                    │    │
│   │  • knowledge.sources[].connector / format / ocr / vision_llm   │    │
│   │  • tools[]（endpoint / auth / request_template）               │    │
│   │  • intents[].handler（builtin:xxx | path.py:build）           │    │
│   │  • server（cors / heartbeat）                                 │    │
│   │  • langsmith.evaluation（dataset_name / evaluators）           │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                                                            │
└─────────────┬──────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌──────────────────────────┐   ┌────────────────────────────────────────────┐
│   LLM Providers（业务方） │   │   可观测（可选）                          │
│   • OpenAI                │   │   • LangSmith SaaS（client + dataset）     │
│   • Anthropic             │   │   • 本地 JSONL trace                      │
│   • DeepSeek              │   │   • LLM-as-judge evaluator                 │
│   • Ollama（本地）        │   └────────────────────────────────────────────┘
│   • Azure OpenAI          │
│   业务方自己 key / 自己付 │    ┌────────────────────────────────────────────┐
└──────────────────────────┘   │   存储（每个 agent 实例）                  │
                              │   • ./data/chroma（向量库）                 │
                              │   • ./data/bm25_chunks.pkl（BM25 chunks）    │
                              │   • ./data/checkpoints.db（多轮历史）        │
                              │   • ./data/cache/<source>/（远程缓存）       │
                              └────────────────────────────────────────────┘
```

**单次请求流**（一次 `/chat` 调用）：

```
浏览器 → ChatWidget
   └─ fetch /api/agent/chat（SSE）
        └─ BFF（cookie → access token）
             └─ POST /chat（Authorization + X-User-Id + X-Thread-Id）
                  └─ agent/server.py
                       └─ runner.astream_tokens(graph, cfg, ...)
                            ├─ graph = StateGraph(classify → intent handler)
                            │    └─ retriever / tool registry
                            │         └─ LangSmith tracer
                            └─ SSE 事件流：sources / token / done
```

### 许可证

[MIT](LICENSE)