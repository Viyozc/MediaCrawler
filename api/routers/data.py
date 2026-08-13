# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/routers/data.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#
# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import os
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/data", tags=["data"])


def _resolve_data_dir() -> Path:
    """数据目录必须与爬虫写入位置一致。

    爬虫把数据写到 cwd 下的 data/<platform>/...；
    桌面模式下 Electron 注入 MEDIACRAWLER_DATA_DIR 并由 runtime_patches chdir 过去，
    所以数据落在 <MEDIACRAWLER_DATA_DIR>/data/。
    开发模式（未注入该变量）回退到项目根的 data/。
    """
    env_data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir) / "data"
    return Path(__file__).parent.parent.parent / "data"


# Data directory
DATA_DIR = _resolve_data_dir()


def get_file_info(file_path: Path) -> dict:
    """Get file information"""
    stat = file_path.stat()
    record_count = None

    # Try to get record count
    try:
        if file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    record_count = len(data)
        elif file_path.suffix == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                record_count = sum(1 for _ in f) - 1  # Subtract header row
    except Exception:
        pass

    return {
        "name": file_path.name,
        "path": str(file_path.relative_to(DATA_DIR)),
        "size": stat.st_size,
        "modified_at": stat.st_mtime,
        "record_count": record_count,
        "type": file_path.suffix[1:] if file_path.suffix else "unknown"
    }


@router.get("/files")
async def list_data_files(platform: Optional[str] = None, file_type: Optional[str] = None):
    """Get data file list"""
    if not DATA_DIR.exists():
        return {"files": []}

    files = []
    supported_extensions = {".json", ".csv", ".xlsx", ".xls"}

    for root, dirs, filenames in os.walk(DATA_DIR):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in supported_extensions:
                continue

            # Platform filter
            if platform:
                rel_path = str(file_path.relative_to(DATA_DIR))
                if platform.lower() not in rel_path.lower():
                    continue

            # Type filter
            if file_type and file_path.suffix[1:].lower() != file_type.lower():
                continue

            try:
                files.append(get_file_info(file_path))
            except Exception:
                continue

    # Sort by modification time (newest first)
    files.sort(key=lambda x: x["modified_at"], reverse=True)

    return {"files": files}


@router.get("/files/{file_path:path}")
async def get_file_content(file_path: str, preview: bool = True, limit: int = 100):
    """Get file content or preview"""
    full_path = DATA_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Security check: ensure within DATA_DIR
    try:
        full_path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if preview:
        # Return preview data
        try:
            if full_path.suffix == ".json":
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {"data": data[:limit], "total": len(data)}
                    return {"data": data, "total": 1}
            elif full_path.suffix == ".csv":
                import csv
                with open(full_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= limit:
                            break
                        rows.append(row)
                    # Re-read to get total count
                    f.seek(0)
                    total = sum(1 for _ in f) - 1
                    return {"data": rows, "total": total}
            elif full_path.suffix.lower() in (".xlsx", ".xls"):
                import pandas as pd
                # Read first limit rows
                df = pd.read_excel(full_path, nrows=limit)
                # Get total row count (only read first column to save memory)
                df_count = pd.read_excel(full_path, usecols=[0])
                total = len(df_count)
                # Convert to list of dictionaries, handle NaN values
                rows = df.where(pd.notnull(df), None).to_dict(orient='records')
                return {
                    "data": rows,
                    "total": total,
                    "columns": list(df.columns)
                }
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type for preview")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Return file download
        return FileResponse(
            path=full_path,
            filename=full_path.name,
            media_type="application/octet-stream"
        )


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download file"""
    full_path = DATA_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Security check
    try:
        full_path.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream"
    )


@router.get("/stats")
async def get_data_stats():
    """Get data statistics"""
    if not DATA_DIR.exists():
        return {"total_files": 0, "total_size": 0, "by_platform": {}, "by_type": {}}

    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_platform": {},
        "by_type": {}
    }

    supported_extensions = {".json", ".csv", ".xlsx", ".xls"}

    for root, dirs, filenames in os.walk(DATA_DIR):
        root_path = Path(root)
        for filename in filenames:
            file_path = root_path / filename
            if file_path.suffix.lower() not in supported_extensions:
                continue

            try:
                stat = file_path.stat()
                stats["total_files"] += 1
                stats["total_size"] += stat.st_size

                # Statistics by type
                file_type = file_path.suffix[1:].lower()
                stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1

                # Statistics by platform (inferred from path)
                rel_path = str(file_path.relative_to(DATA_DIR))
                for platform in ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]:
                    if platform in rel_path.lower():
                        stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
                        break
            except Exception:
                continue

    return stats


# ============================ Wordcloud ============================


class WordcloudRequest(BaseModel):
    """Generate a wordcloud from a comments file.

    Either file_path (relative to DATA_DIR) or task_id must be provided.
    When task_id is used, the first output file with 'comments' in its
    name is selected.
    """
    file_path: Optional[str] = None
    task_id: Optional[str] = None


def _read_comments_file(full_path: Path) -> list[dict]:
    """Read a comments file (json or jsonl) and normalize to dicts."""
    suffix = full_path.suffix.lower()
    if suffix == ".jsonl":
        rows = []
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows
    if suffix == ".json":
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []
    if suffix == ".csv":
        import csv
        with open(full_path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    raise HTTPException(status_code=400, detail=f"Unsupported file type for wordcloud: {suffix}")


def _filter_comment_content(rows: list[dict]) -> list[dict]:
    """Extract content-like field from each row."""
    filtered = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = row.get("content") or row.get("comment_text") or row.get("text") or ""
        if text:
            filtered.append({"content": text})
    return filtered


@router.post("/wordcloud")
async def generate_wordcloud(req: WordcloudRequest):
    """Generate a wordcloud PNG from a comments file.

    Reuses tools.words.AsyncWordCloudGenerator. Output PNG lands at
    <DATA_DIR>/<platform>/words/<stem>_word_cloud.png alongside a
    <stem>_word_freq.json frequencies file.
    """
    # Resolve target file path
    if req.file_path:
        target = DATA_DIR / req.file_path
    elif req.task_id:
        # Lazy import to avoid circular (task_registry imports from schemas)
        from ..services.task_registry import task_registry
        rec = await task_registry.get_task(req.task_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Task not found")
        output_files = rec.get("output_files") or []
        candidates = [f for f in output_files if "comments" in f.get("path", "").lower()]
        if not candidates:
            raise HTTPException(status_code=404, detail="Task has no comments output file")
        target = DATA_DIR / candidates[0]["path"]
    else:
        raise HTTPException(status_code=400, detail="file_path or task_id is required")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path or target}")

    # Security check: ensure within DATA_DIR
    try:
        target.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    rows = await asyncio.to_thread(_read_comments_file, target)
    filtered = _filter_comment_content(rows)
    if not filtered:
        raise HTTPException(status_code=400, detail="No comment content found in file")

    # Output prefix: <DATA_DIR>/<platform>/words/<crawler_type>_comments_<date>
    # For a path like "bili/jsonl/search_comments_20250731.jsonl" we infer:
    #   platform = first path segment ("bili")
    #   stem = filename without suffix
    rel = target.relative_to(DATA_DIR)
    platform = rel.parts[0] if len(rel.parts) > 1 else "data"
    stem = target.stem  # e.g. search_comments_20250731
    words_dir = DATA_DIR / platform / "words"
    await asyncio.to_thread(lambda: words_dir.mkdir(parents=True, exist_ok=True))
    save_prefix = str(words_dir / stem)

    # Generate (runs jieba + wordcloud + matplotlib — heavy, in thread)
    try:
        from tools.words import AsyncWordCloudGenerator
        generator = AsyncWordCloudGenerator()
        await asyncio.to_thread(
            lambda: None  # ensure module load happens in main thread first
        )
        await generator.generate_word_frequency_and_cloud(filtered, save_prefix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wordcloud generation failed: {e}")

    png_path = f"{save_prefix}_word_cloud.png"
    freq_path = f"{save_prefix}_word_freq.json"
    png_rel = str(Path(png_path).relative_to(DATA_DIR))
    freq_rel = str(Path(freq_path).relative_to(DATA_DIR))

    return {
        # preview=false so /files/{path} returns the raw bytes via FileResponse
        # instead of attempting structured preview (which only handles json/csv/xlsx)
        "image_url": f"/api/data/files/{png_rel}?preview=false",
        "freq_url": f"/api/data/files/{freq_rel}",
        "image_path": png_rel,
        "comment_count": len(filtered),
    }
