"""
V3: Vision LLM 看图 → 结构化文字描述。

yaml：
  vision_llm: openai/gpt-4o
  vision_prompt: "请描述这张图：关键字段、表格内容、图表趋势"
"""
from __future__ import annotations

import base64
from pathlib import Path


def _to_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif"}.get(suffix, "image/png")
    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def describe_image(
    image_path: Path,
    llm,
    prompt: str = "请描述这张图片：关键字段、表格内容、图表趋势，输出可被检索的文字。",
) -> str:
    try:
        from langchain_core.messages import HumanMessage
        data_url = _to_data_url(image_path)
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ])
        out = llm.invoke([msg])
        return getattr(out, "content", str(out)).strip()
    except Exception as e:                                  # noqa: BLE001
        print(f"[vision] failed on {image_path}: {e}")
        return ""