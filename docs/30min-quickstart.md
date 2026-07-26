# 30 分钟接入指南

适用：要把 customer-helpmesh-agent 接入自家业务的开发者。

## 第 1 步：准备知识文档（5 min）

按业务域分目录，每个目录一个 source：
```
knowledge/
├── faq/             # FAQ
├── products/        # 产品手册
└── policies/        # 合规
```

支持格式：`.md` `.txt` `.pdf` `.html` `.csv` `.json` `.jsonl`。

## 第 2 步：写 `agent.yaml`（5 min）

```bash
cp examples/agent.yaml.example agent.yaml
```

按业务改：
- `llm.provider` / `model`
- `knowledge.sources`：每个目录加一条
- `intents`：删除不需要的
- `tools`：要查业务 API 就加 endpoint

## 第 3 步：配 `.env`（2 min）

```bash
cp examples/.env.example .env
# 填入 OPENAI_API_KEY
```

## 第 4 步：启动 + 入库（3 min）

```bash
docker compose up -d
curl -X POST http://localhost:8000/ingest | jq
```

## 第 5 步：写 BFF（10 min）

参考 `examples/bff/nextjs/route.ts`：
- 读 cookie → user_token / user_id
- `fetch AGENT_URL/chat`，header 透传 Authorization + X-User-Id
- SSE 流直接 `new NextResponse(upstream.body)`

## 第 6 步：curl 验证（5 min）

```bash
curl -fsS http://localhost:8000/health
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"怎么充值"}'
curl -N -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-test' \
  -H 'X-User-Id: 123' \
  -d '{"message":"我的余额是多少"}'
```

## FAQ

- 文档改了重跑：`POST /ingest`，稳定 ID 跳过未变化 chunk
- 新意图：agent.yaml `intents:` 加一条，handler 仅支持 builtin:faq/account/complaint/chat/refuse
- rerank：`retriever.rerank: true` + `pip install -e ".[rerank]"`
- 不接 Docker：`pip install -r requirements.txt && customer-helpmesh-agent`
- SSO/OAuth：BFF 层做 token 交换，agent 不管 SSO