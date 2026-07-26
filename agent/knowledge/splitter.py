"""
P3: 可配置 splitter。

按 source 的 chunk_size / chunk_overlap 切分。
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    docs: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.split_documents(docs)


def _stable_id(doc: Document, source_name: str) -> str:
    """稳定 ID：同源文件同 chunk 位置永远同 id，rerun 不重复入库。"""
    return f"{source_name}#{doc.metadata.get('chunk_index', '0')}"