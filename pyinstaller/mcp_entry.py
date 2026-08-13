# -*- coding: utf-8 -*-
"""PyInstaller entry for the standalone MCP server binary.

Run: ./dist/mediacrawler-mcp/mediacrawler-mcp
Transport: stdio (compatible with Claude Desktop / Cursor MCP config).
"""
from __future__ import annotations

import os
import sys


def _bootstrap_paths() -> None:
    """Make resource paths resolve correctly under PyInstaller _MEIPASS.

    The MCP server doesn't need jieba/wordcloud/fonts — it only reads
    data files from MEDIACRAWLER_DATA_DIR. So we don't need runtime_patches.
    Just ensure project root is on sys.path when running from source.
    """
    if getattr(sys, "frozen", False):
        # Under PyInstaller: project modules bundled into _MEIPASS.
        return
    # Dev mode: add project root so `mcp_server` package is importable.
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if root not in sys.path:
        sys.path.insert(0, root)


_bootstrap_paths()

from mcp_server.server import main  # noqa: E402

if __name__ == "__main__":
    main()
