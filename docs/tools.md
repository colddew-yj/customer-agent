# 工具（业务 API 接入）

agent 调业务自家 API 拿真实数据（余额、订单、用量），不写代码——在 `agent.yaml` `tools:` 配。

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 工具名 |
| `endpoint` | str | 完整 URL |
| `method` | str | GET / POST / PUT，默认 GET |
| `auth` | str | bearer / header:X-Name / none |
| `auth_header` | str | 默认 Authorization |
| `request_template` | dict | URL 参数或 body 模板，`{{var}}` 占位 |
| `response_path` | str | 取响应嵌套字段，如 `data.balance` |

## 鉴权

- `bearer`：自动用前端 BFF 透传的 `Authorization: Bearer <token>`
- `header:X-Name`：用 `X-User-Id` 值
- `none`：不附加鉴权头

## 占位

`{{user_token}}` / `{{user_id}}` / `{{question}}`。

## 示例：查询余额

```yaml
tools:
  - name: query_balance
    endpoint: https://api.example.com/v1/users/me/balance
    method: GET
    auth: bearer
    response_path: data.balance
```

## 示例：创建工单

```yaml
tools:
  - name: create_ticket
    endpoint: https://api.example.com/v1/tickets
    method: POST
    auth: bearer
    request_template:
      title: "{{question}}"
      user_id: "{{user_id}}"
    response_path: ticket.id
```

## 错误

工具失败 → `{"success": false, "error": "..."}`，agent 不抛 500。
Account handler 看到 `success=false` → "暂时无法获取，请稍后再试"。

## V1 不支持

- OAuth2 client_credentials
- GraphQL
- multipart 文件上传

BFF 层做 token 交换，agent 只接 standard Bearer。