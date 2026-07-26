"""V2: 自定义 handler 扫描。"""
from pathlib import Path

import pytest

from agent.skills.loader import discover_all_in_dir, discover_from_path


def _write_handler(directory: Path, name: str, fn_name: str = "build") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / f"{name}.py"
    p.write_text(
        f"def {fn_name}(ctx):\n"
        f"    def node(state):\n"
        f"        return {{'answer': 'handled by {name}'}}\n"
        f"    return node\n",
        encoding="utf-8",
    )
    return p


def test_discover_from_path_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_handler(tmp_path / "handlers", "order")

    fn = discover_from_path("order")
    out = fn({})({"question": "q"})
    assert out["answer"] == "handled by order"


def test_discover_from_path_explicit_file(tmp_path):
    _write_handler(tmp_path, "refund")
    fn = discover_from_path(f"{tmp_path}/refund.py:build")
    out = fn({})({"question": "q"})
    assert out["answer"] == "handled by refund"


def test_discover_from_path_missing_fn(tmp_path):
    (tmp_path / "bad.py").write_text("def not_build(c): return None\n", encoding="utf-8")
    with pytest.raises(AttributeError, match="没有 build 函数"):
        discover_from_path(f"{tmp_path}/bad.py:build")


def test_discover_all_in_dir(tmp_path):
    d = tmp_path / "handlers"
    d.mkdir()
    _write_handler(d, "order")
    _write_handler(d, "refund")
    (d / "_skip.py").write_text("# private\n", encoding="utf-8")

    found = discover_all_in_dir(d)
    assert "order" in found and "refund" in found
    assert "_skip" not in found


def test_discover_from_path_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        discover_from_path("nonexistent")