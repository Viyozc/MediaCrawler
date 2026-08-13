# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Build task data context for AI chat.

Strategy:
1. Start with task metadata (platform, crawler_type, config, record_counts).
2. For each output file: include file name, type, record count, schema,
   and N sample rows.
3. Truncate to char_budget. If exceeded, reduce sample sizes; if still
   over, keep only metadata + schema + 1 sample row.

Heuristic: 1 token ~= 2 chars (conservative for mixed Chinese/English).
50k chars ~= 25k tokens, leaving room for system prompt + conversation
within typical 32k-128k context windows.
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any, Optional

from ..schemas import TaskRecord
from .ai_settings import _resolve_data_dir


def _data_root() -> Path:
    return _resolve_data_dir() / "data"


def _read_rows_sync(path: Path, limit: int) -> tuple[list[dict], int]:
    """Return (sample_rows, total_count). Reads up to limit rows for the sample."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        sample: list[dict] = []
        total = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                if len(sample) < limit:
                    try:
                        sample.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return sample, total
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[:limit], len(data)
        if isinstance(data, dict):
            return [data][:limit], 1
        return [], 0
    if suffix == ".csv":
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)
            # Cheap total count: re-read and count
            f.seek(0)
            total = sum(1 for _ in f) - 1
        return rows, max(total, 0)
    return [], 0


def _truncate_for_budget(
    text: str, char_budget: int, marker: str = "[truncated]"
) -> str:
    if len(text) <= char_budget:
        return text
    return text[: char_budget - len(marker) - 10] + f"\n{marker}"


async def build_task_context(
    task: TaskRecord,
    include_full_data: bool = False,
    sample_size: int = 20,
    char_budget: int = 50000,
) -> str:
    """Construct a context string for the LLM from the task's output files."""
    data_root = _data_root()

    lines: list[str] = []
    lines.append(f"# Task {task.id}")
    lines.append(f"- platform: {task.platform}")
    lines.append(f"- crawler_type: {task.crawler_type}")
    lines.append(f"- status: {task.status.value if hasattr(task.status, 'value') else task.status}")
    if task.record_counts:
        rc = ", ".join(f"{k}={v}" for k, v in task.record_counts.items())
        lines.append(f"- record_counts: {rc}")
    # Selected config (not cookies)
    cfg = task.config
    config_bits = []
    if cfg.keywords:
        config_bits.append(f"keywords={cfg.keywords!r}")
    if cfg.specified_ids:
        config_bits.append(f"specified_ids={cfg.specified_ids!r}")
    if cfg.creator_ids:
        config_bits.append(f"creator_ids={cfg.creator_ids!r}")
    config_bits.append(f"save_option={cfg.save_option}")
    if cfg.max_notes_count:
        config_bits.append(f"max_notes={cfg.max_notes_count}")
    lines.append(f"- config: {', '.join(config_bits)}")
    lines.append("")

    if not task.output_files:
        lines.append("(no output files)")
        return "\n".join(lines)

    effective_sample = sample_size if not include_full_data else 1000
    # Reserve ~2k chars for metadata above
    file_budget = max(char_budget - 2000, 4000)
    per_file_budget = file_budget // len(task.output_files)

    lines.append("# Output Files")
    for f in task.output_files:
        full = data_root / f.path
        if not full.exists():
            lines.append(f"\n## {f.path} (missing)")
            continue
        try:
            sample_rows, total = await asyncio.to_thread(_read_rows_sync, full, effective_sample)
        except Exception as e:
            lines.append(f"\n## {f.path}\n(read error: {e})")
            continue

        section_lines: list[str] = []
        section_lines.append(f"\n## {f.path}")
        section_lines.append(f"type={f.file_type}, total_rows={total}, size={f.size}B")
        if sample_rows:
            # Schema: keys of first row
            schema = list(sample_rows[0].keys())[:30]
            section_lines.append(f"columns: {schema}")
            # Render sample rows as JSON for consistency
            section_lines.append("sample:")
            for row in sample_rows:
                # Strip very long field values
                trimmed = {
                    k: (v[:200] + "..." if isinstance(v, str) and len(v) > 200 else v)
                    for k, v in list(row.items())[:20]
                }
                section_lines.append(json.dumps(trimmed, ensure_ascii=False, default=str))
        section_text = "\n".join(section_lines)
        lines.append(_truncate_for_budget(section_text, per_file_budget))

    full_text = "\n".join(lines)
    return _truncate_for_budget(full_text, char_budget)
