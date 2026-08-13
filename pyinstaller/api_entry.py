# -*- coding: utf-8 -*-
"""PyInstaller 入口：启动 FastAPI + uvicorn。

Usage:
    ./mediacrawler-api --port 8081 [--host 127.0.0.1]
"""
from __future__ import annotations

# 必须放在所有应用 import 之前，让运行时补丁先生效
import pyinstaller.runtime_patches  # noqa: F401

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="MediaCrawler API server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    # 延迟 import：--help 时不加载整个 app
    import uvicorn
    from api.main import app

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=False,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
