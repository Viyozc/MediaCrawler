# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: mediacrawler-cli (爬虫入口，含 Playwright + Chromium)。

构建命令：
    uv run pyinstaller pyinstaller/mediacrawler-cli.spec --noconfirm
前提：
    uv run playwright install chromium    # 已包含在 docs/打包说明 里
产物：
    dist/mediacrawler-cli/mediacrawler-cli       (入口二进制)
    dist/mediacrawler-cli/_internal/              (依赖目录)
    dist/mediacrawler-cli/_internal/playwright_driver/chromium/Chromium.app
"""
import sys
import os

# PyInstaller 执行 spec 时 sys.path 不含项目根，需手动注入才能 import pyinstaller._common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

from pyinstaller._common import build_analysis

a = build_analysis("pyinstaller/cli_entry.py", include_playwright=True)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mediacrawler-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    name="mediacrawler-cli",
)
