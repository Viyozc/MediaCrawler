# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Task history endpoints.

GET    /api/tasks              list tasks (filter by status/platform, paginate)
GET    /api/tasks/{id}         task detail
DELETE /api/tasks/{id}         remove from registry (+ log file)
GET    /api/tasks/{id}/logs    full log text
POST   /api/tasks/{id}/rescan  re-scan data dir for output files, persist, return task
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..schemas import TaskStatus, TaskRecord, TaskListResponse
from ..services.task_registry import task_registry
from ..services.output_scanner import scan_all_for_platform, infer_record_counts

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _parse_status(s: Optional[str]) -> Optional[TaskStatus]:
    if not s:
        return None
    try:
        return TaskStatus(s)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {s}")


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items, total = await task_registry.list_tasks(
        status=_parse_status(status),
        platform=platform,
        page=page,
        page_size=page_size,
    )
    return {"tasks": items, "total": total}


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str):
    rec = await task_registry.get_task(task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    return rec


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    ok = await task_registry.delete_task(task_id, delete_log=True)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "task_id": task_id}


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Return the full log file content as text. 404 if task or log missing."""
    rec = await task_registry.get_task(task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    log_path = await task_registry.log_path_for(task_id)
    if log_path is None or not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    try:
        text = await asyncio.to_thread(log_path.read_text, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log: {e}")
    return {"logs": text, "path": rec.get("log_path")}


@router.post("/{task_id}/rescan", response_model=TaskRecord)
async def rescan_task(task_id: str):
    """Re-scan data/<platform>/ for output files and persist to the task record.

    Recovery path for tasks that ran before the cwd fix, or where the
    mtime-window scan missed files for any reason.
    """
    rec = await task_registry.get_task(task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    platform = rec.get("platform")
    if not platform:
        raise HTTPException(status_code=400, detail="Task has no platform field")
    files = await scan_all_for_platform(platform)
    counts = infer_record_counts(files)
    updated = await task_registry.update_output_files(task_id, files, counts)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated
