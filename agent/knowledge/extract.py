"""
V3: 三层文本提取 fallback 协调器。

  ① 原生 loader（pdf/docx/xlsx/md...）
  ② OCR（pdf 扫描件 / 图片内文字）
  ③ Vision LLM（OCR 仍失败时看图）
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from ..providers import build_llm
from . import ocr, vision


def primary_text(docs: list[Document]) -> str:
    return "\n\n".join(d.page_content for d in docs if d.page_content)


def needs_fallback(text: str, threshold: int) -> bool:
    return len(text.strip()) < threshold


def maybe_ocr(file_path: Path, ocr_kind: str = "none", ocr_lang: str = "chi_sim+eng") -> str:
    """对文件跑 OCR。pdf 转图再 OCR；图片直接 OCR。"""
    if ocr_kind == "none" or not ocr_kind:
        return ""
    if file_path.suffix.lower() == ".pdf":
        return ocr.ocr_pdf_pages(file_path, lang=ocr_lang)
    return ocr.ocr_image(file_path, lang=ocr_lang)


def maybe_vision(file_path: Path, vision_llm_pair: str | None, prompt: str) -> str:
    """对文件跑 Vision LLM。vision_llm_pair: 'openai/gpt-4o'。"""
    if not vision_llm_pair or "/" not in vision_llm_pair:
        return ""
    provider, model = vision_llm_pair.split("/", 1)
    try:
        from ..config import LLMConfig
        llm = build_llm(LLMConfig(provider=provider, model=model))
    except Exception as e:                                  # noqa: BLE001
        print(f"[vision] failed to build llm: {e}")
        return ""
    return vision.describe_image(file_path, llm, prompt=prompt)