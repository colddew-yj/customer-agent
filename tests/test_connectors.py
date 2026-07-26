"""V3: connector 单测（local / git 用真路径）。"""
import subprocess
from pathlib import Path

from agent.knowledge.connectors.factory import build_connector
from agent.knowledge.connectors.git_repo import GitConnector
from agent.knowledge.connectors.local import LocalConnector


def test_local_connector_returns_path(tmp_path):
    d = tmp_path / "kb"
    d.mkdir()
    (d / "a.md").write_text("# A\nhello", encoding="utf-8")
    c = LocalConnector("test", {"path": "kb"}, tmp_path, tmp_path / "cache")
    out = c.sync()
    assert out.resolve() == d.resolve()
    files = c.list_files()
    assert any(f.name == "a.md" for f in files)


def test_local_connector_missing_path(tmp_path):
    try:
        LocalConnector("test", {}, tmp_path, tmp_path / "cache")
    except ValueError as e:
        assert "缺少 path" in str(e)
    else:
        raise AssertionError("expected ValueError")


def _init_tmp_git_repo(work: Path):
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(work.parent / "origin.git")], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(work.parent / "origin.git"), str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@t"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True, capture_output=True)


def test_git_connector_clone_and_pull(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    _init_tmp_git_repo(work)
    (work / "README.md").write_text("# v1", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "push", "-u", "origin", "main"], check=True, capture_output=True)

    cache = tmp_path / "cache"
    c = GitConnector("test", {"repo_url": str(work.parent / "origin.git"), "branch": "main"}, tmp_path, cache)
    out = c.sync()
    assert (out / "README.md").exists()

    c2 = GitConnector("test", {"repo_url": str(work.parent / "origin.git"), "branch": "main"}, tmp_path, cache)
    out2 = c2.sync()
    assert (out2 / "README.md").exists()


def test_git_connector_path_filter(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    _init_tmp_git_repo(work)
    (work / "docs").mkdir()
    (work / "docs" / "a.md").write_text("doc a", encoding="utf-8")
    (work / "b.md").write_text("not doc", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "push", "-u", "origin", "main"], check=True, capture_output=True)

    cache = tmp_path / "cache"
    c = GitConnector("test", {
        "repo_url": str(work.parent / "origin.git"),
        "branch": "main",
        "path_filter": "docs/*.md",
    }, tmp_path, cache)
    out = c.sync()
    files = c.list_files()
    rel = [f.relative_to(out) for f in files]
    assert any("docs/a.md" in str(r) for r in rel)
    assert all("b.md" not in str(r) for r in rel)


def test_factory_unknown_connector(tmp_path):
    try:
        build_connector("test", {}, tmp_path, connector_type="nonsense")
    except ValueError as e:
        assert "未知 connector" in str(e)
    else:
        raise AssertionError("expected ValueError")
