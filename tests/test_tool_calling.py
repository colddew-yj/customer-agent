from types import SimpleNamespace
from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from agent.graph import _build_tool_loop
from agent.tools.loader import load_toolset, register_toolset


class ScriptedModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        return self.responses.pop(0)


@tool
def lookup_order(
    order_id: str,
    state: Annotated[dict, InjectedState],
) -> dict:
    """查询当前用户订单状态。"""
    return {
        "order_id": order_id,
        "user_id": state["user_id"],
        "status": "已发货",
    }


def test_toolset_loader_returns_registered_tools():
    register_toolset("test-orders", [lookup_order])

    assert load_toolset("test-orders") == [lookup_order]


def test_standard_tool_loop_executes_tool_and_returns_final_answer():
    model = ScriptedModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup_order",
                        "args": {"order_id": "1001"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="订单 1001 已发货。"),
        ]
    )
    cfg = SimpleNamespace(brand_name="Demo", assistant_name="客服助理")
    intent = SimpleNamespace(description="订单查询")
    graph = _build_tool_loop(model, [lookup_order], cfg, intent)

    output = graph.invoke(
        {
            "messages": [HumanMessage(content="查订单 1001")],
            "user_id": "user-1",
            "user_token": "secret-token",
        }
    )

    assert output["answer"] == "订单 1001 已发货。"
    assert any(
        isinstance(message, ToolMessage)
        and '"user_id": "user-1"' in message.content
        for message in output["messages"]
    )
    assert len(output["messages"]) == 4
