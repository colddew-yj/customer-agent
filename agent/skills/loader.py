"""
V2: 自定义 handler 扫描。

业务方写 `~/.customer-helpmesh-agent/handlers/order.py`，每个文件必须有 `build(ctx)` 函数，
agent 启动时自动注册到 `CUSTOM_HANDLERS` 字典。

agent.yaml 配置：
  intents:
    - name: order
      handler: handlers/order.py            # 相对 agent.yaml 的路径
      # 或绝对路径：
      # handler: /opt/biz/handlers/order.py
      # 或文件名（自动从 ~/.customer-helpmesh-agent/handlers/ 找）：
      # handler: order
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Callable


def _default_search_paths() -> list[Path]:
    paths: list[Path] = []
    home = os.environ.get("HOME")
    if home:
        paths.append(Path(home) / ".customer-helpmesh-agent" / "handlers")
    paths.append(Path.cwd() / "handlers")
    return paths


def _import_handler_module(file_path: Path):
    spec = importlib.util.spec_from_file_location(f"_custom_handler_{file_path.stem}", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法 import handler: {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def discover_from_path(handler_ref: str) -> Callable:
    """3 种引用形式：
      1. `module_path:callable`  如 `handlers/order.py:build`
      2. 文件路径（含 :build）   如 `/abs/path/order.py:build`
      3. 纯文件名（如 `order`） → 走默认 plugin 目录
    """
    if ":" in handler_ref:
        file_part, _, fn_name = handler_ref.partition(":")
        file_path = Path(file_part)
        if not file_path.is_absolute():
            file_path = (Path.cwd() / file_part).resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"handler 文件不存在: {file_path}")
        module = _import_handler_module(file_path)
        fn = getattr(module, fn_name, None)
        if fn is None:
            raise AttributeError(f"{file_path} 没有 {fn_name} 函数")
        return fn

    name = handler_ref
    for d in _default_search_paths():
        candidate = d / f"{name}.py"
        if candidate.is_file():
            module = _import_handler_module(candidate)
            fn = getattr(module, "build", None)
            if fn is None:
                raise AttributeError(f"{candidate} 没有 build 函数")
            return fn
    raise FileNotFoundError(
        f"找不到 handler {name!r}。已搜索：{[str(p) for p in _default_search_paths()]}"
    )


def discover_all_in_dir(directory: Path) -> dict[str, Callable]:
    out: dict[str, Callable] = {}
    if not directory.is_dir():
        return out
    for py in sorted(directory.glob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            module = _import_handler_module(py)
            fn = getattr(module, "build", None)
            if fn is not None:
                out[py.stem] = fn
        except Exception as e:                          # noqa: BLE001
            print(f"[custom-handler] skip {py.name}: {e}")
    return out