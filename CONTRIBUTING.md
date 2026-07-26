# Contributing

## 开发

```bash
git clone https://github.com/<org>/customer-helpmesh-agent
cd customer-helpmesh-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp examples/agent.yaml.example agent.yaml
cp examples/.env.example .env  # 填 OPENAI_API_KEY
python -m agent.cli
curl -X POST http://localhost:8000/ingest
pytest
```

## 加新意图 handler

V1 支持 5 个 builtin。新场景：

1. `agent/skills/my_intent.py` 写 `build(ctx)` 返回 node 函数
2. `agent/skills/registry.py` 注册：`BUILTIN_HANDLERS["my_intent"] = my_intent.build`
3. agent.yaml：`handler: my_intent`（无 builtin: 前缀）

## 加新 LLM provider

`agent/providers/llm.py` 加分支。

## 加新 vector store

`agent/providers/vector_store.py` 加分支。

## 加新文档格式

`agent/knowledge/loader.py:_loader_for` 加 if 分支。

## 提交

- 一个 commit 一个改动
- 跑过 pytest
- description 列动机 + 测试步骤

## 排版

- `ruff check agent/ tests/`
- `ruff format agent/ tests/`