# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""MCP tools — callable functions exposed to MCP clients.

All return strings (formatted summaries or JSON), suitable for direct
inclusion in an LLM tool-call result.

NOTE: deliberately NOT using `from __future__ import annotations` here,
because the FastMCP Tool.from_function introspects type hints at runtime
and stringified annotations break its `get_origin`/`issubclass` checks.
"""

import json

from mcp_server.server import mcp
from mcp_server.data_access import (
    list_tasks as _list_tasks,
    get_task as _get_task,
    get_task_data as _get_task_data,
    get_task_stats as _get_task_stats,
    read_data_file as _read_data_file,
    search_in_data_file as _search_in_data_file,
    list_platforms as _list_platforms,
)


def _to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def list_tasks(
    status: str | None = None,
    platform: str | None = None,
    limit: int = 20,
) -> str:
    """List crawl task records. Optionally filter by status or platform.

    Args:
        status: Filter by task status. One of: running, completed, failed, stopped.
        platform: Filter by platform code (xhs, dy, ks, bili, wb, tieba, zhihu).
        limit: Max number of tasks to return (default 20).

    Returns JSON with task summaries (id, status, platform, crawler_type,
    started_at, ended_at, record_counts).
    """
    tasks = _list_tasks(status=status, platform=platform, limit=limit)
    summary = [
        {
            "id": t.get("id"),
            "status": t.get("status"),
            "platform": t.get("platform"),
            "crawler_type": t.get("crawler_type"),
            "started_at": t.get("started_at"),
            "ended_at": t.get("ended_at"),
            "record_counts": t.get("record_counts", {}),
            "output_files": [f.get("path") for f in (t.get("output_files") or [])],
        }
        for t in tasks
    ]
    return _to_json({"tasks": summary, "count": len(summary)})


@mcp.tool()
def get_task(task_id: str) -> str:
    """Get full details of a specific task.

    Includes config snapshot, output files, record counts, log path.

    Args:
        task_id: Task identifier (e.g., "task_1719820800000").
    """
    task = _get_task(task_id)
    if not task:
        return f"Task not found: {task_id}"
    return _to_json(task)


@mcp.tool()
def get_task_data(
    task_id: str,
    file_type: str | None = None,
    limit: int = 50,
) -> str:
    """Get data from a task's output files.

    Args:
        task_id: Task identifier.
        file_type: Optional substring filter on file name
                   (e.g., 'comments', 'contents', 'creators').
                   If omitted, returns data from the first output file.
        limit: Max rows to return (default 50).

    Returns JSON with `data` (list of row dicts) and `total`.
    """
    result = _get_task_data(task_id, file_type=file_type, limit=limit)
    return _to_json(result)


@mcp.tool()
def get_task_stats(task_id: str) -> str:
    """Get aggregated statistics for a task.

    Returns per-file record counts, sizes, and overall record_counts
    (grouped by content/comments/creators when inferred from filename).
    """
    return _to_json(_get_task_stats(task_id))


@mcp.tool()
def search_records(
    task_id: str,
    query: str,
    file_type: str | None = None,
    limit: int = 20,
) -> str:
    """Search for records containing the query string (case-insensitive).

    Searches across all string fields in the task's output file.

    Args:
        task_id: Task identifier.
        query: Substring to search for.
        file_type: Optional file name filter ('comments', 'contents', etc.).
        limit: Max matches (default 20).
    """
    task = _get_task(task_id)
    if not task:
        return f"Task not found: {task_id}"
    files = task.get("output_files") or []
    candidates = files
    if file_type:
        candidates = [f for f in files if file_type.lower() in f.get("path", "").lower()]
    if not candidates:
        return f"No files match file_type='{file_type}' for task {task_id}"

    target = candidates[0]["path"]
    return _to_json(_search_in_data_file(target, query, limit=limit))


@mcp.tool()
def list_platforms() -> str:
    """List all platform codes that have crawled data on disk."""
    return _to_json({"platforms": _list_platforms()})
