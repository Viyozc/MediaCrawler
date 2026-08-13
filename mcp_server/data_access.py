# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Shared read-only data access for MCP tools and resources.

Reads from the live filesystem (registry.json + data files), so callers
always see current state. No write path — the api server owns writes.

Does NOT import any api/* modules to avoid pulling FastAPI/uvicorn into
the standalone MCP binary.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Optional


def resolve_data_dir() -> Path:
    """Same logic as api/routers/data.py:_resolve_data_dir.

    Returns the *base* data dir (parent of `data/`).
    """
    env_data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    # When run from a checkout, default to project root.
    return Path(__file__).resolve().parent.parent


def data_root() -> Path:
    return resolve_data_dir() / "data"


def tasks_dir() -> Path:
    return resolve_data_dir() / "tasks"


def registry_path() -> Path:
    return tasks_dir() / "registry.json"


def load_registry() -> dict:
    """Read registry.json. Empty dict on missing/corrupt."""
    p = registry_path()
    if not p.exists():
        return {"tasks": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": []}


def get_task(task_id: str) -> Optional[dict]:
    """Look up a single task by id."""
    data = load_registry()
    for t in data.get("tasks", []):
        if t.get("id") == task_id:
            return t
    return None


def list_tasks(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Return tasks, newest first, optionally filtered."""
    data = load_registry()
    items = list(data.get("tasks", []))
    if status:
        items = [t for t in items if t.get("status") == status]
    if platform:
        items = [t for t in items if t.get("platform") == platform]
    items.sort(key=lambda t: t.get("started_at", ""), reverse=True)
    return items[:limit]


def read_data_file(rel_path: str, limit: int = 100) -> dict:
    """Read & parse a data file. Returns dict with `data` and `total`.

    Supported: .json, .jsonl, .csv. Others return an error dict.
    """
    full = data_root() / rel_path
    if not full.exists() or not full.is_file():
        return {"error": f"File not found: {rel_path}"}

    # Security: keep within data_root
    try:
        full.resolve().relative_to(data_root().resolve())
    except ValueError:
        return {"error": "Access denied"}

    suffix = full.suffix.lower()
    try:
        if suffix == ".jsonl":
            rows = []
            with open(full, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return {
                "data": rows[:limit],
                "total": len(rows),
                "file_type": "jsonl",
                "path": rel_path,
            }
        if suffix == ".json":
            with open(full, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, list):
                return {"data": payload[:limit], "total": len(payload),
                        "file_type": "json", "path": rel_path}
            return {"data": [payload], "total": 1,
                    "file_type": "json", "path": rel_path}
        if suffix == ".csv":
            with open(full, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = []
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    rows.append(row)
            # Cheap total count
            with open(full, "r", encoding="utf-8") as f:
                total = sum(1 for _ in f) - 1
            return {"data": rows, "total": max(total, 0),
                    "file_type": "csv", "path": rel_path,
                    "columns": list(rows[0].keys()) if rows else []}
    except Exception as e:
        return {"error": f"Read failed: {e}", "path": rel_path}

    return {"error": f"Unsupported file type: {suffix}", "path": rel_path}


def search_in_data_file(rel_path: str, query: str, limit: int = 20) -> dict:
    """Substring search across all string fields in a data file."""
    result = read_data_file(rel_path, limit=10_000)
    if "error" in result:
        return result
    rows = result.get("data", [])
    q = query.lower()
    matches = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for v in row.values():
            if isinstance(v, str) and q in v.lower():
                matches.append(row)
                break
        if len(matches) >= limit:
            break
    return {"matches": matches, "total": len(matches), "query": query,
            "path": rel_path}


def list_platforms() -> list[str]:
    """Platforms that have any data on disk."""
    root = data_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def get_task_data(task_id: str, file_type: Optional[str] = None,
                  limit: int = 50) -> dict:
    """Get data from a task's output files.

    file_type filters by substring in the filename (e.g., 'comments',
    'contents', 'creators'). If None, returns data from the first
    output file.
    """
    task = get_task(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}
    output_files = task.get("output_files") or []
    if not output_files:
        return {"error": "Task has no output files", "task_id": task_id}

    candidates = output_files
    if file_type:
        candidates = [f for f in output_files if file_type.lower() in f.get("path", "").lower()]
        if not candidates:
            return {"error": f"No output file matches '{file_type}'",
                    "task_id": task_id,
                    "available": [f["path"] for f in output_files]}

    target = candidates[0]
    return read_data_file(target["path"], limit=limit)


def get_task_stats(task_id: str) -> dict:
    """Aggregate stats for a task: record counts per file, sizes, schema."""
    task = get_task(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}
    files = task.get("output_files") or []
    stats = {
        "task_id": task_id,
        "status": task.get("status"),
        "platform": task.get("platform"),
        "crawler_type": task.get("crawler_type"),
        "record_counts": task.get("record_counts", {}),
        "files": [
            {"path": f.get("path"), "size": f.get("size"),
             "record_count": f.get("record_count"),
             "file_type": f.get("file_type")}
            for f in files
        ],
    }
    return stats
