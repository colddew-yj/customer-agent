# LLM providers

改 `agent.yaml` 切换 LLM provider，无代码改动。

## OpenAI
```yaml
llm: { provider: openai, model: gpt-4o-mini, api_key_env: OPENAI_API_KEY }
embedding: { provider: openai, model: text-embedding-3-small, api_key_env: OPENAI_API_KEY }
```

## DeepSeek
```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  base_url: https://api.deepseek.com
  api_key_env: DEEPSEEK_API_KEY
embedding: { provider: openai, model: text-embedding-3-small, api_key_env: OPENAI_API_KEY }
```

## Anthropic
```yaml
llm: { provider: anthropic, model: claude-3-5-sonnet-20241022, api_key_env: ANTHROPIC_API_KEY }
embedding: { provider: openai, model: text-embedding-3-small, api_key_env: OPENAI_API_KEY }
```

## Ollama
```yaml
llm:
  provider: ollama
  model: llama3.1
  base_url: http://ollama:11434
  api_key_env: _NONE_
embedding:
  provider: ollama
  model: nomic-embed-text
  base_url: http://ollama:11434
  api_key_env: _NONE_
```

## Azure OpenAI
```yaml
llm:
  provider: openai
  model: gpt-4o
  base_url: https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOY
  api_key_env: AZURE_OPENAI_API_KEY
```

## 第三方代理
任意 OpenAI 协议代理：设 `base_url` + `api_key_env`。

## 故障
- 401：env var 名不匹配
- 404：model 名拼写错
- 429：换 key / 配 backoff