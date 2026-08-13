# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Task history schemas.

A TaskRecord captures one crawl invocation: the config used, when it ran,
what files it produced, and where its full log lives.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .crawler import CrawlerStartRequest


class TaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TaskConfigSnapshot(BaseModel):
    """Frozen copy of CrawlerStartRequest at task creation time.

    Stored as primitive strings/bools so it survives enum class changes
    across binary rebuilds.
    """
    platform: str
    login_type: str
    crawler_type: str
    keywords: str = ""
    specified_ids: str = ""
    creator_ids: str = ""
    start_page: int = 1
    enable_comments: bool = True
    enable_sub_comments: bool = False
    save_option: str = "jsonl"
    cookies: str = ""  # NOTE: stored in plaintext locally; acceptable for desktop
    headless: bool = False
    max_notes_count: Optional[int] = None
    max_comments_count: Optional[int] = None

    @classmethod
    def from_request(cls, req: CrawlerStartRequest) -> "TaskConfigSnapshot":
        return cls(
            platform=req.platform.value,
            login_type=req.login_type.value,
            crawler_type=req.crawler_type.value,
            keywords=req.keywords or "",
            specified_ids=req.specified_ids or "",
            creator_ids=req.creator_ids or "",
            start_page=req.start_page,
            enable_comments=req.enable_comments,
            enable_sub_comments=req.enable_sub_comments,
            save_option=req.save_option.value,
            cookies=req.cookies or "",
            headless=req.headless,
            max_notes_count=req.max_notes_count,
            max_comments_count=req.max_comments_count,
        )


class OutputFile(BaseModel):
    """A file produced by a task. Path is relative to <data_dir>/data/."""
    path: str
    size: int
    record_count: Optional[int] = None
    file_type: str  # json, csv, xlsx, etc.


class TaskRecord(BaseModel):
    id: str  # task_<timestamp_ms>
    status: TaskStatus
    platform: str
    crawler_type: str
    config: TaskConfigSnapshot
    started_at: str  # ISO 8601
    ended_at: Optional[str] = None  # ISO 8601
    exit_code: Optional[int] = None
    output_files: List[OutputFile] = []
    record_counts: Dict[str, int] = {}  # {"comments": 150, "contents": 20}
    log_path: Optional[str] = None  # relative to <data_dir>/tasks/
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskRecord]
    total: int
