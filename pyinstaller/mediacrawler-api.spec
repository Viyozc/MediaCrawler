# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: mediacrawler-api (FastAPI + uvicorn backend)。

构建命令：
    uv run pyinstaller pyinstaller/mediacrawler-api.spec --noconfirm
产物：
    dist/mediacrawler-api/mediacrawler-api      (入口二进制)
    dist/mediacrawler-api/_internal/             (依赖目录)
"""
import sys
import os

# PyInstaller 执行 spec 时 sys.path 不含项目根，需手动注入才能 import pyinstaller._common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

from pyinstaller._common import build_analysis

a = build_analysis("pyinstaller/api_entry.py", include_playwright=False, include_ai=True)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mediacrawler-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # 后端需要看到 uvicorn 日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mediacrawler-api",
)
