#!/usr/bin/env python3
"""本地启动 AI_Find_Customer Sidecar 适配层（无 Docker 时用）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT / "deploy" / "examples" / "ai-find-customer-sidecar"
if str(ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(ADAPTER_DIR))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8092)
    args = parser.parse_args()
    uvicorn.run("main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
