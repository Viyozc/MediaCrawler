# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""MCP resources — URI-addressable data exposed to MCP clients.

Useful for clients that prefer reading a stable URI rather than calling
a tool. All return JSON strings.

NOTE: NOT using `from __future__ import annotations` — see tools.py.
"""

import json

from mcp_server.server import mcp
from mcp_server.data_access import (
    list_tasks as _list_tasks,
    get_task as _get_task,
    get_task_data as _get_task_data,
)


def _to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


@mcp.resource("mediacrawler://tasks")
def tasks_resource() -> str:
    """All task records as JSON (newest first, up to 100)."""
    return _to_json({"tasks": _list_tasks(limit=100)})


@mcp.resource("mediacrawler://tasks/{task_id}")
def task_resource(task_id: str) -> str:
    """Single task record as JSON."""
    task = _get_task(task_id)
    if not task:
        return f"Task not found: {task_id}"
    return _to_json(task)


@mcp.resource("mediacrawler://tasks/{task_id}/data")
def task_data_resource(task_id: str) -> str:
    """All output data for a task as JSON (truncated to 50 rows per file).

    For more control, use the `get_task_data` tool with limit/file_type.
    """
    task = _get_task(task_id)
    if not task:
        return f"Task not found: {task_id}"
    files = task.get("output_files") or []
    out = {}
    for f in files:
        path = f.get("path")
        if not path:
            continue
        out[path] = _get_task_data(task_id, file_type=path.rsplit("/", 1)[-1].split("_")[1] if "_" in path else None, limit=50)
    return _to_json({"task_id": task_id, "files": out})
