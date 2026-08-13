# -*- coding: utf-8 -*-
"""PyInstaller 打包后的运行时补丁。

必须在 api_entry.py / cli_entry.py 的最顶部 import，确保 Playwright
能找到内嵌的 Chromium、config 能解析到打包内的 docs/ 资源。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _meipass() -> Path:
    """PyInstaller 打包后 sys._MEIPASS 指向 onedir 的 _internal/ 或 onefile 临时解压目录；
    开发模式下回退到项目根目录。"""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def setup_playwright_browsers_path() -> None:
    """让 playwright 使用打包内的 Chromium 而不是 ~/Library/Caches/ms-playwright/。"""
    chromium_dir = _meipass() / "playwright_driver"
    if chromium_dir.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(chromium_dir))


def setup_project_cwd() -> None:
    """桌面模式下 data/ 输出目录写到用户可写位置。

    优先用 ELECTRON_APP_DATA_DIR 环境变量（由 Electron 主进程注入）；
    否则不强制改变 cwd，保持开发模式行为。
    """
    data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
    if data_dir:
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        os.chdir(data_dir)


# 模块导入时立即生效
setup_playwright_browsers_path()
setup_project_cwd()
