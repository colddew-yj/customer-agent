"""
Git connector：git clone（首次）+ git pull（增量）。

yaml 示例：
  connector: git
  connector_config:
    repo_url: https://github.com/me/wiki.git
    branch: main
    path_filter: "docs/*.md"
"""
from __future__ import annotations

import shutil
import subprocess
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


class GitConnector:
    def __init__(self, name: str, config: dict[str, Any], base: Path, cache_dir: Path):
        self.name = name
        self.config = config
        self.base = base
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.repo_url = config.get("repo_url")
        if not self.repo_url:
            raise ValueError(f"git connector '{name}' 缺少 repo_url")
        self.branch = config.get("branch", "main")
        self.path_filter = config.get("path_filter")

    def _run(self, args: list[str], cwd: Path | None = None) -> str:
        result = subprocess.run(
            args, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    def sync(self) -> Path:
        if (self.cache_dir / ".git").is_dir():
            self._run(["git", "-C", str(self.cache_dir), "fetch", "origin", self.branch])
            self._run(["git", "-C", str(self.cache_dir), "reset", "--hard", f"origin/{self.branch}"])
            mode = "pull"
        else:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._run([
                "git", "clone", "--depth", "1", "--branch", self.branch,
                self.repo_url, str(self.cache_dir),
            ])
            mode = "clone"

        print(f"[git:{self.name}] {mode} {self.repo_url}#{self.branch} → {self.cache_dir}")
        return self.cache_dir

    def list_files(self) -> list[Path]:
        cache = self.sync()
        files = [p for p in cache.glob("**/*") if p.is_file()]
        if self.path_filter:
            files = [p for p in files if fnmatch(str(p.relative_to(cache)), self.path_filter)]
        return sorted(files)

    def fetch(self, ref: str) -> bytes:
        return (self.cache_dir / ref).read_bytes()

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)