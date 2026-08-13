# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Scan crawler output files by mtime window.

Non-invasive: relies on filesystem mtime, requires no changes to the CLI
binary or file naming conventions. Same-day runs that collide will both
match; this is acceptable for MVP.

Future enhancement: inject task_id into filenames via CLI arg +
_get_file_path modification (requires a cli binary rebuild).
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..schemas import OutputFile
from .task_registry import _resolve_data_dir

SUPPORTED_EXTENSIONS = {".json", ".jsonl", ".csv", ".xlsx", ".xls"}

# API PlatformEnum values → on-disk store directory names used by
# AsyncFileWriter / store/*_store_impl. Codes that already match the
# directory name are omitted (identity).
_PLATFORM_STORE_DIRS: dict[str, str] = {
    "dy": "douyin",
    "ks": "kuaishou",
    "wb": "weibo",
}


def _data_root() -> Path:
    """Same as api/routers/data.py:DATA_DIR."""
    return _resolve_data_dir() / "data"


def platform_store_dir(platform: str) -> str:
    """Map task/API platform code to the filesystem directory under data/."""
    code = (platform or "").strip().lower()
    return _PLATFORM_STORE_DIRS.get(code, code)


def _count_records(file_path: Path) -> Optional[int]:
    """Reuse logic from api/routers/data.py:get_file_info."""
    try:
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return len(data)
                return None
        if suffix == ".jsonl":
            count = 0
            with open(file_path, "r", encoding="utf-8") as f:
                for _ in f:
                    line = _.strip()
                    if line:
                        count += 1
            return count
        if suffix == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f) - 1
    except Exception:
        return None
    return None


def scan_output_files_sync(
    platform: str,
    started_at: datetime,
    ended_at: datetime,
    grace_seconds: float = 30.0,
) -> List[OutputFile]:
    """Walk data/<platform>/ for files with mtime in [started_at, ended_at + grace]."""
    data_root = _data_root()
    platform_dir = data_root / platform_store_dir(platform)
    if not platform_dir.exists():
        return []

    window_start = started_at.timestamp()
    window_end = (ended_at.timestamp() + grace_seconds)

    results: List[OutputFile] = []
    for root, _dirs, filenames in os.walk(platform_dir):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue
            if stat.st_mtime < window_start or stat.st_mtime > window_end:
                continue
            try:
                rel = file_path.relative_to(data_root)
            except ValueError:
                continue
            results.append(OutputFile(
                path=str(rel),
                size=stat.st_size,
                record_count=_count_records(file_path),
                file_type=file_path.suffix[1:].lower(),
            ))

    results.sort(key=lambda f: f.path)
    return results


async def scan_output_files(
    platform: str,
    started_at: datetime,
    ended_at: datetime,
    grace_seconds: float = 30.0,
) -> List[OutputFile]:
    """Async wrapper. Runs the blocking walk in a thread."""
    import asyncio
    return await asyncio.to_thread(
        scan_output_files_sync, platform, started_at, ended_at, grace_seconds
    )


def scan_all_for_platform_sync(platform: str) -> List[OutputFile]:
    """Fallback: pick up every supported file under data/<platform>/.

    Used when the mtime-window scan returns nothing (e.g. task ran before
    the cwd fix, or clock skew, or files copied in out-of-band). Ignores
    mtime entirely.
    """
    data_root = _data_root()
    platform_dir = data_root / platform_store_dir(platform)
    if not platform_dir.exists():
        return []
    results: List[OutputFile] = []
    for root, _dirs, filenames in os.walk(platform_dir):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue
            try:
                rel = file_path.relative_to(data_root)
            except ValueError:
                continue
            results.append(OutputFile(
                path=str(rel),
                size=stat.st_size,
                record_count=_count_records(file_path),
                file_type=file_path.suffix[1:].lower(),
            ))
    results.sort(key=lambda f: f.path)
    return results


async def scan_all_for_platform(platform: str) -> List[OutputFile]:
    import asyncio
    return await asyncio.to_thread(scan_all_for_platform_sync, platform)


def infer_record_counts(files: List[OutputFile]) -> dict:
    """Aggregate record counts by file category (comments/contents/creators)."""
    counts: dict[str, int] = {}
    for f in files:
        name = f.path.lower()
        for cat in ("comments", "contents", "creators"):
            if cat in name:
                if f.record_count is not None:
                    counts[cat] = counts.get(cat, 0) + f.record_count
                break
    return counts
