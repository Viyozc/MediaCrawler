# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""FastMCP server entrypoint.

Run as: `python -m mcp_server.server` or via the PyInstaller-built
`mediacrawler-mcp` binary. Transport: stdio.

NOTE: do NOT import tools/resources at module top-level here. When this
file runs as `__main__` (e.g., via `python -m mcp_server.server`), a
top-level `from mcp_server import tools` would cause Python to re-import
this module under its canonical name `mcp_server.server`, creating a
*second* FastMCP instance. Importing inside main() ensures both paths
reach the same singleton.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mediacrawler")


def main() -> None:
    # Register tools/resources. When this module runs as __main__ (via
    # `python -m mcp_server.server`), Python executes the file body twice:
    # once as canonical `mcp_server.server` (creating mcp instance A) and
    # once as `__main__` (creating instance B in this frame). tools.py /
    # resources.py do `from mcp_server.server import mcp`, so their
    # decorators register on instance A. To run the populated server we
    # must call instance A's `.run()`, not the local `mcp` (which is B).
    import mcp_server.server as canonical
    from mcp_server import tools  # noqa: F401
    from mcp_server import resources  # noqa: F401
    canonical.mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
