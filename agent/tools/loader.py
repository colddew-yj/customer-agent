"""LangChain Toolset loader.

Toolset 表示一个业务领域可用的能力集合，不绑定某个用户问题。
具体 Tool 由业务代码用 @tool 定义；本模块负责发现和按名称加载集合。
"""
from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path

from langchain_core.tools import BaseTool

TOOLSETS: dict[str, list[BaseTool]] = {}
TOOL_DIR = Path(__file__).parent
_INTERNAL_MODULES = {"loader.py", "registry.py"}


def _validate_tools(name: str, tools: Sequence[BaseTool], seen: dict[str, str]) -> list[BaseTool]:
    validated = list(tools)
    if not validated:
        raise ValueError(f"toolset '{name}' 没有可用 Tool")

    for tool in validated:
        if not isinstance(tool, BaseTool):
            raise TypeError(f"toolset '{name}' 包含非 LangChain BaseTool: {tool!r}")
        if not tool.name:
            raise ValueError(f"toolset '{name}' 包含空 Tool 名称")
        if not (tool.description or "").strip():
            raise ValueError(f"Tool '{tool.name}' 必须有非空 description")
        previous = seen.get(tool.name)
        if previous:
            raise ValueError(f"重复 Tool 名称 '{tool.name}': {previous} 和 {name}")
        seen[tool.name] = name
    return validated


def _import_tool_module(path: Path):
    module_name = f"_customer_agent_tool_{path.stem}"
    cached = sys.modules.get(module_name)
    cached_path = getattr(cached, "__file__", None) if cached else None
    if cached is not None and cached_path and Path(cached_path).resolve() == path:
        return cached
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法导入 Tool 模块: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def register_toolset(name: str, tools: Sequence[BaseTool]) -> None:
    """注册一个领域 Toolset，供 graph 构建时加载。"""
    if not name:
        raise ValueError("toolset name 不能为空")
    TOOLSETS[name] = _validate_tools(name, tools, {})


def discover_toolsets() -> dict[str, list[BaseTool]]:
    """从固定的受信目录发现只读 Toolset。

    运行时不接受外部目录；新增 Tool 属于部署代码变更，重启后生效。
    """
    root = TOOL_DIR.resolve()
    discovered: dict[str, list[BaseTool]] = {}
    seen = {
        tool.name: toolset
        for toolset, tools in TOOLSETS.items()
        for tool in tools
    }

    for path in sorted(root.glob("*.py")):
        if path.name.startswith("_") or path.name in _INTERNAL_MODULES:
            continue
        existing = TOOLSETS.get(path.stem)
        if existing is not None:
            for tool in existing:
                seen.pop(tool.name, None)
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as e:
            raise ValueError(f"Tool 文件不能离开受信目录: {path}") from e

        try:
            module = _import_tool_module(resolved)
        except Exception as e:
            raise RuntimeError(f"加载 Tool 模块失败 '{path}': {e}") from e

        if not hasattr(module, "TOOLS"):
            raise ValueError(f"Tool 模块 '{path}' 必须导出 TOOLS")
        if getattr(module, "READ_ONLY", False) is not True:
            raise ValueError(f"Tool 模块 '{path}' 必须声明 READ_ONLY = True")

        tools = _validate_tools(path.stem, module.TOOLS, seen)
        if existing is not None and existing != tools:
            raise ValueError(f"重复 Toolset 名称 '{path.stem}'")
        discovered[path.stem] = tools

    TOOLSETS.update(discovered)
    return discovered


def load_toolset(name: str) -> list[BaseTool]:
    """加载领域 Toolset；未知集合在启动时快速失败。"""
    try:
        tools = TOOLSETS[name]
    except KeyError as e:
        raise ValueError(
            f"未知 toolset: {name}；已注册: {sorted(TOOLSETS)}"
        ) from e
    if not tools:
        raise ValueError(f"toolset '{name}' 没有可用 Tool")
    return list(tools)
