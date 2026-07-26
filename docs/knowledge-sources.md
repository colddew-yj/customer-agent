# 知识源

`agent.yaml` `knowledge.sources:` 配置每个业务文档域。

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 标识 |
| `path` | str | 相对 agent.yaml 的目录 |
| `glob` | str | 文件匹配，默认 `**/*` |
| `format` | str | md / txt / pdf / html / csv / json / jsonl / auto |
| `chunk_size` | int | 切分块大小 |
| `chunk_overlap` | int | 切分重叠 |
| `retrieval_weight` | float | 检索加权 0~1 |
| `metadata_tags` | dict | 检索时附加元数据 |

## 格式

- md / markdown → UnstructuredMarkdownLoader
- html / htm → BSHTMLLoader
- pdf → PyPDFLoader（按页）
- csv → CSVLoader（每行一 Document）
- json → JSONLoader（jq schema `.`）
- jsonl → JSONLoader（json_lines=True）
- txt → TextLoader
- auto → 按后缀推断

## 多域加权

```yaml
knowledge:
  sources:
    - { name: faq, path: ./knowledge/faq, retrieval_weight: 1.0 }
    - { name: policies, path: ./knowledge/policies, retrieval_weight: 0.5 }
```

V1 `retrieval_weight` 仅记录到 metadata（V2 排序依据）。

## 增量入库

`POST /ingest` 重跑：按 `stable_id = "{source_name}#{chunk_index}"` 判重，Chroma upsert 行为。

## V1 不支持

- `.docx` / `.xlsx`
- `.epub` / `.mobi`
- Notion / 飞书 / Confluence 远程拉取

业务方手动 `rsync` 或 mount volume。