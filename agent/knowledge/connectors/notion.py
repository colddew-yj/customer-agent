"""
Notion connector：拉 Notion database pages → markdown → cache。

yaml 示例：
  connector: notion
  connector_config:
    api_key_env: NOTION_API_KEY
    database_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    title_property: Name
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any


def _blocks_to_markdown(blocks: list[dict]) -> str:
    """Notion blocks → markdown。简化版：支持常见 8 种 block。"""
    out: list[str] = []
    for b in blocks:
        btype = b.get("type", "")
        bdata = b.get(btype, {})
        rich = bdata.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich)
        if btype == "heading_1":
            out.append(f"# {text}\n")
        elif btype == "heading_2":
            out.append(f"## {text}\n")
        elif btype == "heading_3":
            out.append(f"### {text}\n")
        elif btype == "paragraph":
            out.append(f"{text}\n")
        elif btype == "bulleted_list_item":
            out.append(f"- {text}")
        elif btype == "numbered_list_item":
            out.append(f"1. {text}")
        elif btype == "code":
            lang = bdata.get("language", "")
            out.append(f"```{lang}\n{text}\n```\n")
        elif btype == "quote":
            out.append(f"> {text}\n")
        elif text:
            out.append(text)
    return "\n".join(out)


class NotionConnector:
    def __init__(self, name: str, config: dict[str, Any], base: Path, cache_dir: Path):
        self.name = name
        self.config = config
        self.base = base
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = os.environ.get(config.get("api_key_env", "NOTION_API_KEY"), "")
        if not self.api_key:
            raise RuntimeError(
                f"notion connector '{name}': env {config.get('api_key_env', 'NOTION_API_KEY')} 未设"
            )
        self.database_id = config.get("database_id")
        if not self.database_id:
            raise ValueError(f"notion connector '{name}' 缺少 database_id")
        self.title_property = config.get("title_property", "Name")

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        import httpx
        r = httpx.request(
            method,
            f"https://api.notion.com/v1{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json=body or {},
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()

    def sync(self) -> Path:
        pages: list[dict] = []
        cursor = None
        while True:
            body: dict[str, Any] = {"database_id": self.database_id, "page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            data = self._request("POST", "/databases/query", body)
            pages.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        saved = 0
        for page in pages:
            title = self._extract_title(page)
            slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", title).strip("_") or page["id"]
            blocks = self._fetch_blocks(page["id"])
            md = f"# {title}\n\n{_blocks_to_markdown(blocks)}\n"
            target = self.cache_dir / f"{slug}.md"
            target.write_text(md, encoding="utf-8")
            saved += 1

        print(f"[notion:{self.name}] saved {saved} pages → {self.cache_dir}")
        return self.cache_dir

    def _extract_title(self, page: dict) -> str:
        props = page.get("properties", {})
        title_prop = props.get(self.title_property, props.get("title", {}))
        rich = title_prop.get("title", []) if isinstance(title_prop, dict) else []
        return "".join(rt.get("plain_text", "") for rt in rich) or page["id"]

    def _fetch_blocks(self, page_id: str) -> list[dict]:
        blocks: list[dict] = []
        cursor = None
        while True:
            path = f"/blocks/{page_id}/children"
            if cursor:
                path += f"?start_cursor={cursor}"
            data = self._request("GET", path)
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return blocks

    def list_files(self) -> list[Path]:
        return sorted(p for p in self.cache_dir.glob("**/*.md") if p.is_file())

    def fetch(self, ref: str) -> bytes:
        return (self.cache_dir / ref).read_bytes()

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)