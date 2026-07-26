"""Tests for knowledge loaders."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def test_load_dir_md(tmp_path):
    (tmp_path / "a.md").write_text("# A\nhello world", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\nfoo bar", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")

    from agent.knowledge.loader import load_dir
    docs = load_dir(tmp_path, glob="**/*.md")
    assert len(docs) == 2


def test_load_file_auto(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("# title\ncontent", encoding="utf-8")
    from agent.knowledge.loader import load_file
    docs = load_file(p, fmt="auto")
    assert len(docs) >= 1


def test_splitter_basic():
    from langchain_core.documents import Document
    from agent.knowledge.splitter import split_documents
    long_text = "A" * 1000
    docs = [Document(page_content=long_text, metadata={"file_name": "x.md"})]
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=50)
    assert len(chunks) >= 4