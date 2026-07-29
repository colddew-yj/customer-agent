from pathlib import Path

import pytest

from agent.tools import loader


@pytest.fixture(autouse=True)
def clear_toolsets():
    previous = loader.TOOLSETS.copy()
    loader.TOOLSETS.clear()
    yield
    loader.TOOLSETS.clear()
    loader.TOOLSETS.update(previous)


def write_tool_module(directory: Path, name: str, body: str) -> None:
    (directory / f"{name}.py").write_text(body, encoding="utf-8")


def test_discover_toolset_from_trusted_directory(tmp_path, monkeypatch):
    write_tool_module(
        tmp_path,
        "logistics",
        """
from langchain_core.tools import tool

@tool
def query_tracking(tracking_no: str) -> dict:
    \"\"\"查询物流轨迹。\"\"\"
    return {\"tracking_no\": tracking_no}

TOOLS = [query_tracking]
READ_ONLY = True
""",
    )
    monkeypatch.setattr(loader, "TOOL_DIR", tmp_path)

    discovered = loader.discover_toolsets()

    assert list(discovered) == ["logistics"]
    assert loader.load_toolset("logistics")[0].name == "query_tracking"


def test_discovery_rejects_non_read_only_module(tmp_path, monkeypatch):
    write_tool_module(
        tmp_path,
        "orders",
        """
from langchain_core.tools import tool

@tool
def cancel_order(order_id: str) -> str:
    \"\"\"取消订单。\"\"\"
    return order_id

TOOLS = [cancel_order]
READ_ONLY = False
""",
    )
    monkeypatch.setattr(loader, "TOOL_DIR", tmp_path)

    with pytest.raises(ValueError, match="READ_ONLY"):
        loader.discover_toolsets()


def test_discovery_rejects_missing_tools_export(tmp_path, monkeypatch):
    write_tool_module(tmp_path, "broken", "READ_ONLY = True\n")
    monkeypatch.setattr(loader, "TOOL_DIR", tmp_path)

    with pytest.raises(ValueError, match="导出 TOOLS"):
        loader.discover_toolsets()


def test_discovery_rejects_duplicate_tool_names(tmp_path, monkeypatch):
    body = """
from langchain_core.tools import tool

@tool
def query(value: str) -> str:
    \"\"\"查询数据。\"\"\"
    return value

TOOLS = [query]
READ_ONLY = True
"""
    write_tool_module(tmp_path, "account", body)
    write_tool_module(tmp_path, "orders", body)
    monkeypatch.setattr(loader, "TOOL_DIR", tmp_path)

    with pytest.raises(ValueError, match="重复 Tool 名称"):
        loader.discover_toolsets()


def test_discovery_rejects_symlink_outside_trusted_directory(tmp_path, monkeypatch):
    outside = tmp_path / "outside.py"
    outside.write_text("TOOLS = []\nREAD_ONLY = True\n", encoding="utf-8")
    trusted = tmp_path / "trusted"
    trusted.mkdir()
    (trusted / "outside.py").symlink_to(outside)
    monkeypatch.setattr(loader, "TOOL_DIR", trusted)

    with pytest.raises(ValueError, match="不能离开受信目录"):
        loader.discover_toolsets()
