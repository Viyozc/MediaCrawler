# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/api/services/crawler_manager.py
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

import asyncio
import subprocess
import signal
import os
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from ..schemas import CrawlerStartRequest, LogEntry, TaskStatus
from .task_registry import task_registry
from .output_scanner import scan_output_files, infer_record_counts


class CrawlerManager:
    """Crawler process manager"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self.process: Optional[subprocess.Popen] = None
        self.status = "idle"
        self.started_at: Optional[datetime] = None
        self.current_config: Optional[CrawlerStartRequest] = None
        self._log_id = 0
        self._logs: List[LogEntry] = []
        self._read_task: Optional[asyncio.Task] = None
        # Project root directory
        self._project_root = Path(__file__).parent.parent.parent
        # Log queue - for pushing to WebSocket
        self._log_queue: Optional[asyncio.Queue] = None
        # Task history integration
        self._current_task_id: Optional[str] = None
        self._log_file_handle = None

    @property
    def logs(self) -> List[LogEntry]:
        return self._logs

    def get_log_queue(self) -> asyncio.Queue:
        """Get or create log queue"""
        if self._log_queue is None:
            self._log_queue = asyncio.Queue()
        return self._log_queue

    def _create_log_entry(self, message: str, level: str = "info") -> LogEntry:
        """Create log entry"""
        self._log_id += 1
        ts = datetime.now()
        entry = LogEntry(
            id=self._log_id,
            timestamp=ts.strftime("%H:%M:%S"),
            level=level,
            message=message
        )
        self._logs.append(entry)
        # Keep last 500 logs
        if len(self._logs) > 500:
            self._logs = self._logs[-500:]
        # Persist to full log file for task history
        if self._log_file_handle is not None:
            try:
                self._log_file_handle.write(
                    f"{ts.isoformat(timespec='seconds')}\t{level}\t{message}\n"
                )
                self._log_file_handle.flush()
            except Exception:
                pass
        return entry

    def _open_task_log(self, task_id: str) -> None:
        """Open <data_dir>/tasks/<task_id>.log for append."""
        from .task_registry import _resolve_data_dir
        try:
            tasks_dir = _resolve_data_dir() / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            self._log_file_handle = open(tasks_dir / f"{task_id}.log", "a", encoding="utf-8")
        except Exception:
            self._log_file_handle = None

    def _close_task_log(self) -> None:
        if self._log_file_handle is not None:
            try:
                self._log_file_handle.close()
            except Exception:
                pass
            self._log_file_handle = None

    async def _push_log(self, entry: LogEntry):
        """Push log to queue"""
        if self._log_queue is not None:
            try:
                self._log_queue.put_nowait(entry)
            except asyncio.QueueFull:
                pass

    def _parse_log_level(self, line: str) -> str:
        """Parse log level"""
        line_upper = line.upper()
        if "ERROR" in line_upper or "FAILED" in line_upper:
            return "error"
        elif "WARNING" in line_upper or "WARN" in line_upper:
            return "warning"
        elif "SUCCESS" in line_upper or "完成" in line or "成功" in line:
            return "success"
        elif "DEBUG" in line_upper:
            return "debug"
        return "info"

    async def start(self, config: CrawlerStartRequest) -> bool:
        """Start crawler process"""
        async with self._lock:
            if self.process and self.process.poll() is None:
                return False

            # Clear old logs
            self._logs = []
            self._log_id = 0

            # Clear pending queue (don't replace object to avoid WebSocket broadcast coroutine holding old queue reference)
            if self._log_queue is None:
                self._log_queue = asyncio.Queue()
            else:
                try:
                    while True:
                        self._log_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            # Build command line arguments
            cmd = self._build_command(config)

            # Log start information
            entry = self._create_log_entry(f"Starting crawler: {' '.join(cmd)}", "info")
            await self._push_log(entry)

            try:
                # cwd: prefer MEDIACRAWLER_DATA_DIR so the crawler subprocess
                # writes its `data/<platform>/...` tree under the same root that
                # output_scanner and data routers look at. Fall back to project
                # root in dev mode (where _resolve_data_dir also returns it).
                env_data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
                cwd = env_data_dir if env_data_dir else str(self._project_root)
                # Start subprocess
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    bufsize=1,
                    cwd=cwd,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"}
                )

                self.status = "running"
                self.started_at = datetime.now()
                self.current_config = config

                # Create task record (best-effort; never block crawl on history)
                try:
                    self._current_task_id = await task_registry.create_task(config)
                    self._open_task_log(self._current_task_id)
                except Exception as e:
                    self._current_task_id = None

                entry = self._create_log_entry(
                    f"Crawler started on platform: {config.platform.value}, type: {config.crawler_type.value}",
                    "success"
                )
                await self._push_log(entry)

                # Start log reading task
                self._read_task = asyncio.create_task(self._read_output())

                return True
            except Exception as e:
                self.status = "error"
                entry = self._create_log_entry(f"Failed to start crawler: {str(e)}", "error")
                await self._push_log(entry)
                return False

    async def stop(self) -> bool:
        """Stop crawler process"""
        async with self._lock:
            if not self.process or self.process.poll() is not None:
                return False

            self.status = "stopping"
            entry = self._create_log_entry("Sending SIGTERM to crawler process...", "warning")
            await self._push_log(entry)

            try:
                self.process.send_signal(signal.SIGTERM)

                # Wait for graceful exit (up to 15 seconds)
                for _ in range(30):
                    if self.process.poll() is not None:
                        break
                    await asyncio.sleep(0.5)

                # If still not exited, force kill
                if self.process.poll() is None:
                    entry = self._create_log_entry("Process not responding, sending SIGKILL...", "warning")
                    await self._push_log(entry)
                    self.process.kill()

                entry = self._create_log_entry("Crawler process terminated", "info")
                await self._push_log(entry)

            except Exception as e:
                entry = self._create_log_entry(f"Error stopping crawler: {str(e)}", "error")
                await self._push_log(entry)

            self.status = "idle"
            await self._finalize_current_task(status=TaskStatus.STOPPED, exit_code=-1)
            self.current_config = None

            # Cancel log reading task
            if self._read_task:
                self._read_task.cancel()
                self._read_task = None

            return True

    def get_status(self) -> dict:
        """Get current status"""
        return {
            "status": self.status,
            "platform": self.current_config.platform.value if self.current_config else None,
            "crawler_type": self.current_config.crawler_type.value if self.current_config else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "error_message": None
        }

    def _build_command(self, config: CrawlerStartRequest) -> list:
        """Build main.py command line arguments.

        优先用 MEDIACRAWLER_CLI 环境变量指向的打包二进制（桌面模式），
        否则 fallback 到 `uv run python main.py`（开发模式）。
        """
        cli = os.environ.get("MEDIACRAWLER_CLI")
        if cli and os.path.isfile(cli):
            cmd = [cli]
        else:
            cmd = ["uv", "run", "python", "main.py"]

        cmd.extend(["--platform", config.platform.value])
        cmd.extend(["--lt", config.login_type.value])
        cmd.extend(["--type", config.crawler_type.value])
        cmd.extend(["--save_data_option", config.save_option.value])

        # Pass different arguments based on crawler type
        if config.crawler_type.value == "search" and config.keywords:
            cmd.extend(["--keywords", config.keywords])
        elif config.crawler_type.value == "detail" and config.specified_ids:
            cmd.extend(["--specified_id", config.specified_ids])
        elif config.crawler_type.value == "creator" and config.creator_ids:
            cmd.extend(["--creator_id", config.creator_ids])

        if config.start_page != 1:
            cmd.extend(["--start", str(config.start_page)])

        cmd.extend(["--get_comment", "true" if config.enable_comments else "false"])
        cmd.extend(["--get_sub_comment", "true" if config.enable_sub_comments else "false"])

        if config.max_notes_count is not None:
            cmd.extend(["--crawler_max_notes_count", str(config.max_notes_count)])

        if config.max_comments_count is not None:
            cmd.extend(["--max_comments_count_singlenotes", str(config.max_comments_count)])

        if config.cookies:
            cmd.extend(["--cookies", config.cookies])

        cmd.extend(["--headless", "true" if config.headless else "false"])

        return cmd

    async def _read_output(self):
        """Asynchronously read process output"""
        loop = asyncio.get_event_loop()

        try:
            while self.process and self.process.poll() is None:
                # Read a line in thread pool
                line = await loop.run_in_executor(
                    None, self.process.stdout.readline
                )
                if line:
                    line = line.strip()
                    if line:
                        level = self._parse_log_level(line)
                        entry = self._create_log_entry(line, level)
                        await self._push_log(entry)

            # Read remaining output
            if self.process and self.process.stdout:
                remaining = await loop.run_in_executor(
                    None, self.process.stdout.read
                )
                if remaining:
                    for line in remaining.strip().split('\n'):
                        if line.strip():
                            level = self._parse_log_level(line)
                            entry = self._create_log_entry(line.strip(), level)
                            await self._push_log(entry)

            # Process ended
            if self.status == "running":
                exit_code = self.process.returncode if self.process else -1
                if exit_code == 0:
                    entry = self._create_log_entry("Crawler completed successfully", "success")
                else:
                    entry = self._create_log_entry(f"Crawler exited with code: {exit_code}", "warning")
                await self._push_log(entry)
                self.status = "idle"
                await self._finalize_current_task(
                    status=TaskStatus.COMPLETED if exit_code == 0 else TaskStatus.FAILED,
                    exit_code=exit_code,
                )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            entry = self._create_log_entry(f"Error reading output: {str(e)}", "error")
            await self._push_log(entry)
            await self._finalize_current_task(status=TaskStatus.FAILED, error=str(e))

    async def _finalize_current_task(
        self,
        status: TaskStatus,
        exit_code: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Scan output files and finalize the task record. Best-effort."""
        task_id = self._current_task_id
        started = self.started_at
        cfg = self.current_config
        self._current_task_id = None
        self._close_task_log()
        if not task_id or started is None or cfg is None:
            return
        try:
            ended = datetime.now()
            output_files = await scan_output_files(
                platform=cfg.platform.value,
                started_at=started,
                ended_at=ended,
            )
            record_counts = infer_record_counts(output_files)
            await task_registry.finalize_task(
                task_id,
                status=status,
                exit_code=exit_code,
                output_files=output_files,
                record_counts=record_counts,
                error=error,
            )
        except Exception as e:
            # Don't let history failure surface to UI as a crawl failure
            entry = self._create_log_entry(f"Task history finalize failed: {e}", "warning")
            await self._push_log(entry)


# Global singleton
crawler_manager = CrawlerManager()
