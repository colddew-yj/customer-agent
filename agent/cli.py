"""CLI 入口：运行 uvicorn。"""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="customer-agent server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", default=None, type=int)
    args = parser.parse_args(argv)

    import os
    host = args.host or os.environ.get("AGENT_HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("AGENT_PORT", "8000"))

    import uvicorn
    uvicorn.run("agent.server:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())