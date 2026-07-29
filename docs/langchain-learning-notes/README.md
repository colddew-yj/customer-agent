# LangChain / LangGraph 学习笔记索引

> 本目录记录从零搭建 customer service agent 过程中的 LangChain/LangGraph 学习成果。

## 学习路径

### P1 — LangChain RAG

- [P1-01：为什么用 LangChain](./P1-01-why-langchain.md) ✅
- [P1-02 Document Loader](./P1-02-document-loaders.md) ✅
- [P1-03 Text Splitter](./P1-03-text-splitters.md) ✅
- [P1-04 Embeddings & Vector Store](./P1-04-embeddings-vector-stores.md) ✅
- [P1-05 Retriever](./P1-05-retrievers.md) ✅
- [P1-06 Chain & LCEL](./P1-06-chains-lcel.md) ✅
- [P1-09 FastAPI + Pydantic + SSE](./P1-09-fastapi-pydantic-sse.md) ✅

### P2 — LangGraph 状态机

- [P2-01 LangGraph 入门（StateGraph / Node / Edge）](./P2-01-langgraph-intro.md) ✅
- [P2-02 节点设计 & State（3 节点真实图）](./P2-02-nodes-state.md) ✅
- [P2-03 条件边 & 路由](./P2-03-conditional-edges.md) ✅
- [P2-04 服务端切换 + 流式输出 + 用户文档补充](./P2-04-server-stream-user-docs.md) ✅

### P3 — Tool calling 接业务 API

- [P3-01 Tool calling 入门（@tool 装饰器）](./P3-01-tool-calling.md) ✅
- [P3-02 GraphState 扩展 + 鉴权注入](./P3-02-state-auth-injection.md) ✅
- [P3-03 端到端调试（4 个 bug）](./P3-03-debugging-walkthrough.md) ✅
- [P3-04 通用客服 Agent 的标准 Tool Calling](./P3-04-standard-tool-calling.md) ✅

### P4 — 检索质量优化

- [P4-01 检索质量优化（BM25 + 混合 + Reranker + 评估）](./P4-01-retrieval-quality.md) ✅

### P5 — LangGraph Memory

- [P5-01 短期 Memory（多轮对话 + MemorySaver）](./P5-01-short-term-memory.md) ✅

### P6 — LangGraph Studio 可视化 + 调试（已关闭）

> P6 因 langchain-core v0.3 + langgraph v1 + Py 3.14 三方依赖冲突关闭。详见 P7 笔记踩坑记录。

### P7 — 可观测性

- [P7-01 LangSmith + 本地 JSONL 双通道可观测性](./P7-01-langsmith-observability.md) ✅

### P8 — 多 agent 协作

- [P8-01 supervisor + 2 specialist subgraphs（tech / billing）](./P8-01-subgraphs-supervisor.md) ✅

### P9 — Prompt engineering 进阶

- [P9-01 few-shot + JSON 输出 + 拒答阈值 + 置信度](./P9-01-prompt-engineering.md) ✅

### P10 — 流式输出 token 级

- [P10-01 astream_events v2 + token 级 SSE](./P10-01-token-streaming.md) ✅

## 进度

### P1

| 笔记 | 状态 |
|---|---|
| P1-01 为什么用 LangChain | ✅ |
| P1-02 Document Loader | ✅ |
| P1-03 Text Splitter | ✅ |
| P1-04 Embeddings & Vector Store | ✅ |
| P1-05 Retriever | ✅ |
| P1-06 Chain & LCEL | ✅ |
| P1-09 FastAPI + Pydantic + SSE | ✅ |

### P2

| 笔记 | 状态 |
|---|---|
| P2-01 LangGraph 入门 | ✅ |
| P2-02 节点设计 & State | ✅ |
| P2-03 条件边 & 路由 | ✅ |
| P2-04 服务端切换 + 流式 + 用户文档 | ✅ |

### P3

| 笔记 | 状态 |
|---|---|
| P3-01 Tool calling 入门 | ✅ |
| P3-02 GraphState 扩展 + 鉴权注入 | ✅ |
| P3-03 端到端调试 | ✅ |
| P3-04 标准 Tool Calling 改造 | ✅ |

### P4

| 笔记 | 状态 |
|---|---|
| P4-01 检索质量优化（4 子任务综合）| ✅ |

### P5

| 笔记 | 状态 |
|---|---|
| P5-01 短期 Memory（多轮对话 + MemorySaver）| ✅ |

### P6 — 已关闭

| 笔记 | 状态 |
|---|---|
| LangGraph Studio | ⛔ 关闭（依赖冲突） |

### P7

| 笔记 | 状态 |
|---|---|
| P7-01 LangSmith + 本地 JSONL 可观测性 | ✅ |

### P8

| 笔记 | 状态 |
|---|---|
| P8-01 supervisor + 2 specialist subgraphs | ✅ |

### P9

| 笔记 | 状态 |
|---|---|
| P9-01 few-shot + JSON + 拒答阈值 | ✅ |

### P10

| 笔记 | 状态 |
|---|---|
| P10-01 astream_events token 级 SSE | ✅ |

## 写作约定

每篇笔记 6 个部分：

1. **是什么**（概念定义）
2. **为什么需要**（解决什么问题）
3. **代码示例**（最小可运行）
4. **本项目的用法**（具体怎么用）
5. **踩坑记录**（遇到的问题）
6. **下一步**（链接到下一篇）

## 项目目录

- `agent/` — Python 服务（LangChain/LangGraph 跑在这里）
- `agent/graph/` — LangGraph 模块（state / nodes / build / runner）
- `agent/tools/` — P3 业务 API tool 函数
- `agent/knowledge/` — P1 + P4 检索基础设施（vectorstore / bm25 / hybrid / reranker / eval）
- `docs/user-*.md` — 客服 agent 知识库（用户视角文档）
- `app/api/agent/chat/` — Next.js 代理路由
- `components/customer-service/` — 客服 widget
