# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: mediacrawler-mcp (standalone MCP server, stdio transport).

Lightweight: no Playwright / Chromium, no FastAPI runtime. Only needs the
`mcp` SDK + pydantic + the project's mcp_server package + data_access.

Build:
    uv run pyinstaller pyinstaller/mediacrawler-mcp.spec --noconfirm
Output:
    dist/mediacrawler-mcp/mediacrawler-mcp
"""
import sys
import os

# PyInstaller 执行 spec 时把项目根加到 sys.path，让 import pyinstaller._common 工作
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(SPEC))))

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

PROJECT_ROOT = Path(SPEC).resolve().parent.parent

# --- datas / binaries / hidden ---
datas: list = []
binaries: list = []
hidden: list = [
    # MCP SDK + pydantic
    "mcp",
    "mcp.server.fastmcp",
    "pydantic",
    "pydantic_core",
    # Project MCP package (PyInstaller should pick it up from imports,
    # but explicit collect_submodules is safe)
] + collect_submodules("mcp_server")

# Collect everything for the mcp package (datas + binaries + hidden)
mcp_d, mcp_b, mcp_h = collect_all("mcp")
datas += mcp_d
binaries += mcp_b
hidden += mcp_h

# pydantic v2 sometimes needs explicit collection
py_d, py_b, py_h = collect_all("pydantic")
datas += py_d
binaries += py_b
hidden += py_h

a = Analysis(
    [str(PROJECT_ROOT / "pyinstaller" / "mcp_entry.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Heavy deps we don't need
        "playwright",
        "matplotlib",
        "pandas",
        "numpy",
        "opencv",
        "cv2",
        "fastapi",
        "uvicorn",
        "openai",
        "jieba",
        "wordcloud",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mediacrawler-mcp",
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
    name="mediacrawler-mcp",
)
