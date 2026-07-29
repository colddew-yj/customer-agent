# P3-04：通用客服 Agent 的标准 Tool Calling

## 1. 先回答核心疑问

当前项目里有两种容易混淆的“配置”：

### 业务 Agent 配置

```text
知识库来源 + 业务文档 + 意图 + Prompt
                         ↓
                 决定 Agent 属于哪类业务
```

例如：

- 电商客服
- SaaS 客服
- 物流客服
- 银行/保险客服

这才是通用客服 Agent 的领域配置。

### API 连接配置

```yaml
tools:
  - name: query_balance
    endpoint: https://example.com/api/balance
```

这只是把一个 HTTP API 接进来。它可以复用，但本身不代表 AI 理解了业务，也不代表 LLM 会自主选择工具。

当前项目的 `ToolRegistry` 属于后一种：它能调用 API，但调用哪个工具由 `uses_tools` 和节点代码固定决定。

标准 Tool Calling 要解决的是另一个问题：

```text
用户说了什么？
应该调用哪个能力？
参数是什么？
是否需要连续调用多个能力？
工具结果回来后是否继续推理？
```

## 2. 为什么普通 API 配置不够

当前实现大致是：

```text
classify
  ↓
account handler
  ↓
for name in uses_tools:
    ToolRegistry.invoke(name)
  ↓
LLM 总结 API 结果
```

这适合一个固定流程，例如“账户问题总是同时查询余额、订单和用量”。

但它不适合开放的通用客服 Agent：

```text
用户问商品库存       → 查库存
用户问订单物流       → 查订单/物流
用户问退货政策       → 查知识库
用户要求申请退款     → 申请人工确认
用户问套餐使用情况   → 查用量
```

标准 Tool Calling 的关键变化是：**工具列表提供给 LLM，单次调用由 LLM 根据工具描述决定**。

## 3. Toolset：领域能力集合

Toolset 不是“一个问题对应一个 API”，而是一个业务领域可以使用的一组能力。

### 电商客服 Toolset

```text
query_product
query_order
query_logistics
create_ticket
request_refund
```

### SaaS 客服 Toolset

```text
query_account
query_usage
query_subscription
rotate_api_key
create_ticket
```

### 物流客服 Toolset

```text
query_waybill
query_delivery_status
query_delivery_exception
create_claim
```

这些 Tool 不一定都在每个 Agent 中启用。启动 Agent 时，根据业务领域加载对应集合：

```python
TOOLSETS = {
    "ecommerce": [
        query_product,
        query_order,
        query_logistics,
        create_ticket,
    ],
    "saas": [
        query_account,
        query_usage,
        query_subscription,
        create_ticket,
    ],
}
```

这里的选择是“这个 Agent 有哪些能力”，不是“这次用户问题必须调用哪些 API”。

## 4. `@tool`：把 Python 能力描述给 LLM

```python
from langchain_core.tools import tool


@tool
def query_order(order_id: str) -> dict:
    """查询当前用户指定订单的状态、物流和售后信息。"""
    return call_order_api(order_id)
```

`@tool` 会让函数成为 LangChain Tool，并生成供模型使用的 schema：

```text
工具名：query_order
工具描述：查询当前用户指定订单的状态、物流和售后信息
参数：order_id，字符串，订单号
```

其中 docstring 会帮助 LLM 判断：

```text
“订单 1001 到哪了？” → query_order
“现在还有多少库存？” → query_product
```

Tool 的真实实现仍然是确定性的 Python/API 调用；AI 的部分在于工具选择、参数提取和后续编排。

## 5. 鉴权信息不能交给 LLM 生成

用户身份和 token 应该来自请求上下文，而不是模型参数：

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool


@tool
def query_order(
    order_id: str,
    state: Annotated[dict, InjectedState],
) -> dict:
    """查询当前用户指定订单的状态、物流和售后信息。"""
    return call_order_api(
        order_id=order_id,
        user_id=state["user_id"],
        user_token=state["user_token"],
    )
```

对 LLM 来说，需要生成的只有：

```json
{"order_id": "1001"}
```

`user_id` 和 `user_token` 由 LangGraph 从 state 注入，不应该让模型生成，也不应该回传给模型。

当前项目已经具备这条鉴权输入链：

```text
FastAPI Header
  ↓
GraphState.user_token / user_id
  ↓
InjectedState
  ↓
Tool 内部调用业务 API
```

## 6. `llm.bind_tools`：把领域能力提供给模型

Agent 启动构图时加载 Toolset：

```python
tools = load_toolset("ecommerce")
llm_with_tools = llm.bind_tools(tools)
```

这一步不会执行工具，只是告诉模型当前 Agent 可以使用哪些能力。

然后每次对话中，LLM 才根据用户问题选择是否调用工具。

## 7. `AIMessage.tool_calls`：模型的工具决策

用户发送：

```text
帮我查一下订单 1001 到哪了？
```

模型可能返回：

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "query_order",
            "args": {"order_id": "1001"},
            "id": "call_123",
        }
    ],
)
```

这表示：

```text
模型决定调用 query_order
模型提取参数 order_id=1001
模型等待 Tool 执行结果
```

这就是当前 `ToolRegistry` 缺少的 AI 决策环节。

## 8. `ToolNode`：执行模型选中的工具

```python
from langgraph.prebuilt import ToolNode

tool_node = ToolNode(tools)
```

`ToolNode` 读取 `AIMessage.tool_calls`，找到对应 Tool 并执行：

```text
AIMessage.tool_calls
  ↓
ToolNode 找到 query_order
  ↓
注入 GraphState
  ↓
执行 Python Tool
  ↓
生成 ToolMessage
  ↓
写回 messages
```

## 9. `tools_condition`：决定是否继续循环

```python
from langgraph.prebuilt import tools_condition

builder.add_conditional_edges(
    "agent",
    tools_condition,
)
```

逻辑是：

```text
最后一条 AIMessage 有 tool_calls？
  ├─ 有 → tools
  └─ 没有 → END
```

完整 Graph：

```python
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
```

运行过程：

```text
HumanMessage
  ↓
agent
  ↓
AIMessage(tool_calls)
  ↓
tools
  ↓
ToolMessage
  ↓
agent
  ↓
AIMessage(最终回答)
```

## 10. 一个完整的业务例子

用户：

```text
帮我查订单 1001 到哪了？
```

### 第一次 Agent 调用

模型看到用户问题和 Tool schema，产生：

```text
query_order(order_id="1001")
```

### ToolNode 调用业务 API

```text
query_order
  ↓
业务订单 API
  ↓
订单状态：已发货，运输中
```

### 第二次 Agent 调用

模型看到 ToolMessage 后生成：

```text
你的订单 1001 已经发货，目前正在运输中。
```

如果用户继续问：

```text
那预计什么时候送到？
```

模型可以继续选择：

```text
query_logistics(order_id="1001")
```

这就是多轮、多 Tool、模型自主编排。

## 11. 当前项目应该如何迁移

当前项目现在是：

```text
START → classify → account
                     ↓
             固定 uses_tools
                     ↓
               ToolRegistry
```

迁移后建议变成：

```text
START → classify → tool-enabled agent
                         ↓
                       tools
                         ↓
                       agent
```

迁移顺序：

1. 保留当前 `classify` 和 FAQ/RAG 流程
2. 先把 `account` 的固定调用改成标准 Tool Calling
3. 为不同业务领域建立 Toolset
4. 让领域 Agent 加载对应 Toolset
5. 再将订单、余额、物流、工单等真实 Tool 加入各领域集合

当前 `uses_tools: [query_balance, query_order]` 的职责将被替换为：

```text
toolset: saas_support
```

它只说明“这个 Agent 能使用哪些能力”，不再规定“每次必须调用哪些工具”。

## 12. 读 Tool 和写 Tool

### 读 Tool

可以自动执行：

```text
query_balance
query_order
query_stock
query_usage
```

### 写 Tool

需要用户确认：

```text
request_refund
cancel_order
create_ticket
change_address
```

推荐流程：

```text
LLM 选择写 Tool
  ↓
LangGraph interrupt
  ↓
用户确认
  ↓
ToolNode 执行
```

Tool Calling 不等于可以无条件执行副作用操作。

## 13. 当前项目与标准方案的差异

| 内容 | 当前实现 | 标准方案 |
|---|---|---|
| Tool 定义 | YAML API 配置 | Python `@tool` |
| 工具选择 | `uses_tools` 固定 | LLM 产生 `tool_calls` |
| 参数生成 | 模板替换 | LLM 结构化生成 |
| 执行节点 | handler 内循环 | LangGraph `ToolNode` |
| 结果传递 | `realtime_data` | `ToolMessage` |
| 多步调用 | 手写逻辑 | Graph 循环 |
| 业务领域 | 知识库/意图配置 | 知识库/意图 + Toolset |

## 14. 当前项目的下一步

第一阶段只验证标准链路：

```text
@tool
  ↓
bind_tools
  ↓
AIMessage.tool_calls
  ↓
ToolNode
  ↓
tools_condition
  ↓
最终回答
```

暂时不写死余额、订单 API，也不伪造业务接口。

等真实业务 API 接入后，只需要把对应业务函数放进正确的 Toolset，不需要重新设计 Agent Graph。

## 15. 当前项目的 Tool 自动发现

当前项目阶段 2 使用固定的受信目录：

```text
agent/tools/
```

新增一个只读业务 Tool：

```python
# agent/tools/logistics.py
from langchain_core.tools import tool

@tool
def query_tracking(tracking_no: str) -> dict:
    """查询物流单号的当前状态。"""
    # 调用真实业务系统
    return {"tracking_no": tracking_no}

TOOLS = [query_tracking]
READ_ONLY = True
```

然后在 `agent.yaml` 中绑定领域：

```yaml
intents:
  - name: logistics
    handler: builtin:chat
    description: 物流、配送、运输轨迹
    toolset: logistics
```

重启 Agent 后，启动阶段会自动：

```text
扫描文件 → 导入模块 → 校验 TOOLS → 注册 Toolset
```

自动发现不是动态执行任意 Python 文件。第一版只扫描项目内固定目录，不扫描用户上传目录；模块导入失败、Tool 名重复、缺少 `TOOLS` 或不是只读 Tool 时，Agent 直接启动失败，不静默跳过。

因此，新增业务概念的最小操作是：

```text
编写 @tool → 导出 TOOLS → 绑定 intent.toolset → 重启服务
```

退款、取消订单、修改地址等写 Tool 暂不通过自动发现启用，需要后续增加 LangGraph 确认/审批节点。

---

**本项目当前状态**：已有 LangGraph 路由、GraphState 鉴权字段、SSE 和标准 LangChain Tool Calling 循环；阶段 2 已支持固定受信目录中的只读 Tool 自动发现。
