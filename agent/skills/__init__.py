"""Skills 子包：5 个内置意图 + 注册表。"""
from .registry import build_handler, BUILTIN_HANDLERS

__all__ = ["build_handler", "BUILTIN_HANDLERS"]