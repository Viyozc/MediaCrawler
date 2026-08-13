# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Persistent task registry backed by JSON.

Location: <data_dir>/tasks/registry.json
Where <data_dir> = $MEDIACRAWLER_DATA_DIR or project root.

All mutations go through asyncio.Lock. The API server is single-process
uvicorn, so there is no cross-process contention. The file is rewritten in
full on each mutation (small N, infrequent writes) via temp file + atomic
os.replace.

Load strategy: lazy on first read; corrupt file falls back to empty state
with a logged warning (so a bad registry never blocks crawls).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..schemas import CrawlerStartRequest, TaskStatus, TaskConfigSnapshot, OutputFile, TaskRecord

logger = logging.getLogger(__name__)


def _resolve_data_dir() -> Path:
    """Mirror api/routers/data.py:_resolve_data_dir logic.

    Returns the *base* data dir (parent of `data/`). Task files live under
    <data_dir>/tasks/, sibling to the crawler's `data/` output directory.
    """
    env_data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    return Path(__file__).parent.parent.parent


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class TaskRegistry:
    """Singleton task registry."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._tasks: Dict[str, dict] = {}  # id -> TaskRecord dict
        self._loaded = False

    # ----- disk helpers -----

    @property
    def _tasks_dir(self) -> Path:
        return _resolve_data_dir() / "tasks"

    @property
    def _registry_path(self) -> Path:
        return self._tasks_dir / "registry.json"

    def _ensure_dirs(self) -> None:
        self._tasks_dir.mkdir(parents=True, exist_ok=True)

    async def _load_locked(self) -> None:
        """Read registry.json from disk. On corruption, start empty."""
        if self._loaded:
            return
        path = self._registry_path
        if not path.exists():
            self._loaded = True
            return
        try:
            raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict) and isinstance(data.get("tasks"), list):
                self._tasks = {t["id"]: t for t in data["tasks"] if isinstance(t, dict) and "id" in t}
            else:
                logger.warning("registry.json has unexpected shape; starting empty")
        except Exception as e:
            logger.warning("Failed to load task registry (%s); starting empty", e)
        self._loaded = True

    async def _flush_locked(self) -> None:
        """Write full registry atomically."""
        self._ensure_dirs()
        payload = {
            "version": 1,
            "tasks": list(self._tasks.values()),
        }
        tmp = self._registry_path.with_suffix(".json.tmp")
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        await asyncio.to_thread(_atomic_write_text, self._registry_path, tmp, text)

    # ----- public API -----

    async def create_task(self, config: CrawlerStartRequest) -> str:
        """Create a running task. Returns task_id."""
        async with self._lock:
            await self._load_locked()
            task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
            snapshot = TaskConfigSnapshot.from_request(config)
            record = TaskRecord(
                id=task_id,
                status=TaskStatus.RUNNING,
                platform=snapshot.platform,
                crawler_type=snapshot.crawler_type,
                config=snapshot,
                started_at=_now_iso(),
                log_path=f"{task_id}.log",
            )
            self._tasks[task_id] = record.model_dump(mode="json")
            await self._flush_locked()
            return task_id

    async def finalize_task(
        self,
        task_id: str,
        *,
        status: TaskStatus,
        exit_code: Optional[int] = None,
        output_files: Optional[List[OutputFile]] = None,
        record_counts: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Set terminal status. No-op if task missing."""
        async with self._lock:
            await self._load_locked()
            rec = self._tasks.get(task_id)
            if not rec:
                logger.warning("finalize_task: unknown task_id %s", task_id)
                return
            rec["status"] = status.value if isinstance(status, TaskStatus) else status
            rec["ended_at"] = _now_iso()
            if exit_code is not None:
                rec["exit_code"] = exit_code
            if output_files is not None:
                rec["output_files"] = [
                    of.model_dump(mode="json") if isinstance(of, OutputFile) else of
                    for of in output_files
                ]
            if record_counts is not None:
                rec["record_counts"] = record_counts
            if error is not None:
                rec["error"] = error
            await self._flush_locked()

    async def get_task(self, task_id: str) -> Optional[dict]:
        async with self._lock:
            await self._load_locked()
            rec = self._tasks.get(task_id)
            return dict(rec) if rec else None

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        platform: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[dict], int]:
        """Return (tasks, total), newest started_at first."""
        async with self._lock:
            await self._load_locked()
            items = list(self._tasks.values())
        # filter
        if status:
            status_val = status.value if isinstance(status, TaskStatus) else status
            items = [t for t in items if t.get("status") == status_val]
        if platform:
            items = [t for t in items if t.get("platform") == platform]
        # sort newest first by started_at (ISO string compares correctly)
        items.sort(key=lambda t: t.get("started_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return [dict(t) for t in items[start:end]], total

    async def delete_task(self, task_id: str, *, delete_log: bool = True) -> bool:
        """Remove task from registry. Optionally delete its log file.
        Does NOT delete output data files.
        """
        async with self._lock:
            await self._load_locked()
            rec = self._tasks.pop(task_id, None)
            if not rec:
                return False
            await self._flush_locked()
        if delete_log and rec.get("log_path"):
            log_file = self._tasks_dir / rec["log_path"]
            try:
                await asyncio.to_thread(log_file.unlink, True)
            except Exception as e:
                logger.warning("Failed to delete log %s: %s", log_file, e)
        return True

    async def log_path_for(self, task_id: str) -> Optional[Path]:
        """Absolute path to the task's log file, or None if task/log_path missing."""
        async with self._lock:
            await self._load_locked()
            rec = self._tasks.get(task_id)
            if not rec or not rec.get("log_path"):
                return None
            return self._tasks_dir / rec["log_path"]

    async def update_output_files(
        self,
        task_id: str,
        output_files: list,
        record_counts: Optional[dict] = None,
    ) -> Optional[dict]:
        """Overwrite output_files (and optionally record_counts) on a task.

        Used by the rescan endpoint and the AI chat fallback path.
        Returns the updated record dict, or None if task missing.
        """
        async with self._lock:
            await self._load_locked()
            rec = self._tasks.get(task_id)
            if not rec:
                return None
            rec["output_files"] = [
                of.model_dump(mode="json") if hasattr(of, "model_dump") else of
                for of in output_files
            ]
            if record_counts is not None:
                rec["record_counts"] = record_counts
            await self._flush_locked()
            return dict(rec)


def _atomic_write_text(target: Path, tmp: Path, text: str) -> None:
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


# Global singleton
task_registry = TaskRegistry()
