# -*- coding: utf-8 -*-
"""资源路径解析工具。

PyInstaller 打包后，源码目录里的 docs/、media_platform/ 等数据文件
被解压到 sys._MEIPASS（onedir 模式是 dist/<name>/_internal/）。
开发模式下回退到项目根目录。

任何模块都可通过 `from config._paths import resource_path` 使用。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _project_root() -> Path:
    """开发模式下的项目根目录。

    本文件位于 <root>/config/_paths.py，所以爷爷目录就是项目根。
    """
    return Path(__file__).resolve().parent.parent


def resource_path(rel: str) -> str:
    """把项目相对路径解析为绝对路径。

    - 打包模式（frozen）：基于 sys._MEIPASS
    - 开发模式：基于项目根目录

    rel 可以以 './' 或 '/' 开头，会被规范化。
    """
    rel_clean = rel.lstrip("./").lstrip("/")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = _project_root()
    return str(base / rel_clean)
