"""
P2: 配置加载。

读取 agent.yaml（项目根）+ 环境变量（覆盖敏感字段）。
启动时校验必需项，缺字段立即报清晰错误。

WHY 双源：业务方希望配置文件可入仓（yaml），密钥不入仓（env）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────
# Pydantic schema: agent.yaml 字段定义
# ──────────────────────────────────────────────────────────────────────

class LLMConfig(BaseModel):
    provider: str = Field(..., description="openai | anthropic | deepseek | ollama")
    model: str
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    temperature: float = 0.3


class EmbeddingConfig(BaseModel):
    provider: str
    model: str
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"


class VectorStoreConfig(BaseModel):
    provider: str = "chroma"               # chroma | in-memory
    persist_dir: str = "./data/chroma"
    collection_name: str = "knowledge"


class MultiQueryConfig(BaseModel):
    n_variants: int = 3


class HydeConfig(BaseModel):
    enabled: bool = False


class QueryRewriteConfig(BaseModel):
    enabled: bool = True
    max_rewrites: int = 2


class RetrieverConfig(BaseModel):
    strategy: str = "hybrid"               # vector | hybrid | multiquery | hyde
    top_k: int = 5
    fetch_k: int = 10
    fusion: str = "rrf"                   # rrf | weighted
    bm25_chunks_path: str = "./data/bm25_chunks.pkl"
    bm25_tokenizer: str = "jieba"         # jieba | whitespace
    rerank: bool = True                   # V3: 默认开（cross-encoder 精排 top_k 候选）
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_top_n: int = 20                # 召回多少候选送 reranker
    multi_query: MultiQueryConfig = MultiQueryConfig()
    hyde: HydeConfig = HydeConfig()
    query_rewrite: QueryRewriteConfig = QueryRewriteConfig()


class KnowledgeSourceConfig(BaseModel):
    name: str
    path: str | None = None               # 本地 connector 用；远程 connector 留 None
    glob: str = "**/*"
    format: str = "auto"                  # md | txt | pdf | html | csv | json | jsonl | docx | xlsx | pdf_advanced | auto
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_weight: float = 1.0
    metadata_tags: dict[str, str] = Field(default_factory=dict)

    # V3: 远程 connector
    connector: str | None = None           # local | s3 | git | notion | None (= local)
    connector_config: dict[str, Any] = Field(default_factory=dict)


class KnowledgeConfig(BaseModel):
    sources: list[KnowledgeSourceConfig] = Field(default_factory=list)


class ToolConfig(BaseModel):
    name: str
    endpoint: str
    method: str = "GET"
    auth: str = "bearer"                   # bearer | header:X-Name | none
    auth_header: str = "Authorization"
    request_template: dict[str, Any] | None = None
    response_path: str | None = None       # json path to extract, e.g. "data.balance"


class IntentConfig(BaseModel):
    name: str
    handler: str                            # builtin:faq / builtin:account / builtin:complaint / builtin:chat / builtin:refuse
    description: str
    prompt_file: str | None = None
    uses_rag: bool = True
    uses_tools: list[str] = Field(default_factory=list)


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    heartbeat_seconds: int = 15


class EvaluationConfig(BaseModel):
    enabled: bool = False
    dataset_name: str | None = None
    evaluators: list[str] = Field(default_factory=lambda: ["heuristic"])
    # 哪些 strategies 对比（vector / hybrid / multiquery / hyde），输出 precision@k
    strategies: list[str] = Field(default_factory=lambda: ["hybrid"])


class LangSmithConfig(BaseModel):
    enabled: bool = False
    api_key_env: str = "LANGSMITH_API_KEY"
    project: str = "customer-helpmesh-agent"
    local_trace_path: str | None = None
    evaluation: EvaluationConfig = EvaluationConfig()


class AgentConfig(BaseModel):
    """完整 agent.yaml schema。"""
    llm: LLMConfig
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig = VectorStoreConfig()
    retriever: RetrieverConfig = RetrieverConfig()
    knowledge: KnowledgeConfig = KnowledgeConfig()
    tools: list[ToolConfig] = Field(default_factory=list)
    intents: list[IntentConfig]
    server: ServerConfig = ServerConfig()
    langsmith: LangSmithConfig = LangSmithConfig()

    # 业务侧系统身份（用于 System prompt 中的"我是 XXX 客服助理"）
    assistant_name: str = "客服助理"
    brand_name: str = "Customer Service"


# ──────────────────────────────────────────────────────────────────────
# 加载器
# ──────────────────────────────────────────────────────────────────────

# 注：路径在 load() 内每次读 env，方便测试切换。
_DEFAULT_CONFIG_PATH = "./agent.yaml"
_DEFAULT_ENV_PATH = "./.env"


def _resolve_yaml(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(
            f"缺少配置文件: {path}\n"
            f"复制 examples/agent.yaml.example 到 {path} 后重试。"
        )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_env() -> None:
    """加载 .env（如果有）。业务方密钥走 env，不入 agent.yaml。"""
    env_path = Path(os.environ.get("AGENT_ENV_PATH", _DEFAULT_ENV_PATH))
    if env_path.is_file():
        load_dotenv(env_path)


def _inject_api_keys(cfg: AgentConfig) -> AgentConfig:
    """把 api_key_env 名（如 OPENAI_API_KEY）解析为真实 key 注入。"""
    if cfg.llm.api_key_env and not os.environ.get("_LLM_KEY"):
        os.environ["_LLM_KEY"] = os.environ.get(cfg.llm.api_key_env, "")
    if cfg.embedding.api_key_env and not os.environ.get("_EMB_KEY"):
        os.environ["_EMB_KEY"] = os.environ.get(cfg.embedding.api_key_env, "")
    if cfg.langsmith.api_key_env:
        os.environ.setdefault("LANGSMITH_API_KEY",
                              os.environ.get(cfg.langsmith.api_key_env, ""))
    return cfg


def _validate(cfg: AgentConfig, cfg_path: Path) -> None:
    """启动校验：缺关键字段报清晰错误。"""
    errors: list[str] = []

    if not cfg.intents:
        errors.append("`intents:` 至少配 1 个，否则 graph 没出口")

    builtin = {"faq", "account", "complaint", "chat", "refuse"}
    for it in cfg.intents:
        prefix, _, name = it.handler.partition(":")
        if prefix == "builtin" and name not in builtin:
            errors.append(f"intent '{it.name}' handler '{it.handler}' 不在 builtin 集合 {builtin}")

    declared_tools = {t.name for t in cfg.tools}
    for it in cfg.intents:
        for tname in it.uses_tools:
            if tname not in declared_tools:
                errors.append(f"intent '{it.name}' uses_tools '{tname}' 未在 tools: 里声明")

    base = cfg_path.parent
    for src in cfg.knowledge.sources:
        # V3: 远程 connector 不要求 path 存在
        if src.connector and src.connector != "local":
            continue
        if src.path is None:
            errors.append(f"knowledge_sources '{src.name}' 必须配 path 或 connector")
            continue
        p = base / src.path
        if not p.exists():
            errors.append(f"knowledge_sources '{src.name}' path '{p}' 不存在")

    if errors:
        raise RuntimeError("agent.yaml 校验失败:\n  - " + "\n  - ".join(errors))


def load() -> AgentConfig:
    """主入口：加载 + 校验 + 注入密钥。"""
    _resolve_env()
    config_path = Path(os.environ.get("AGENT_CONFIG_PATH", _DEFAULT_CONFIG_PATH))
    raw = _resolve_yaml(config_path)
    cfg = AgentConfig(**raw)
    _inject_api_keys(cfg)
    _validate(cfg, config_path)
    return cfg


if __name__ == "__main__":
    import json
    print(json.dumps(load().model_dump(), indent=2, ensure_ascii=False))
