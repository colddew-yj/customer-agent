"""CLI 入口：serve / ingest / eval。"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="customer-helpmesh-agent CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_serve = sub.add_parser("serve", help="启动 FastAPI server")
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", default=None, type=int)

    p_ing = sub.add_parser("ingest", help="入库知识文档")
    p_ing.add_argument("--config", default="./agent.yaml")
    p_ing.add_argument("--base", default=".")

    p_eval = sub.add_parser("eval", help="跑评估集")
    p_eval.add_argument("--dataset", required=True)
    p_eval.add_argument("--config", default="./agent.yaml")

    args = parser.parse_args(argv)

    if args.cmd == "serve":
        import os
        host = args.host or os.environ.get("AGENT_HOST", "0.0.0.0")
        port = args.port or int(os.environ.get("AGENT_PORT", "8000"))
        import uvicorn
        uvicorn.run("agent.server:app", host=host, port=port, reload=False)
        return 0

    if args.cmd == "ingest":
        import os
        os.environ["AGENT_CONFIG_PATH"] = args.config
        from .knowledge.ingest import main as ingest_main
        return ingest_main(["--config", args.config, "--base", args.base])

    if args.cmd == "eval":
        import os
        os.environ["AGENT_CONFIG_PATH"] = args.config
        from .eval.runner import main as eval_main
        return eval_main(["--dataset", args.dataset, "--config", args.config])

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())