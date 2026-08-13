# -*- coding: utf-8 -*-
"""两个 spec 文件共用的配置生成器。

PyInstaller 执行 spec 文件时把项目根目录加到 sys.path，所以这里能被 import。
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _collect(*packages):
    """聚合多个包的 datas/binaries/hiddenimports。"""
    datas, binaries, hidden = [], [], []
    for pkg in packages:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hidden += h
    return datas, binaries, hidden


def _abs(p: str) -> str:
    """把项目相对路径解析为绝对路径（基于 _common.py 所在目录的爷爷目录）。

    PyInstaller 把 datas 里相对路径当相对于 spec 文件目录，
    所以必须传绝对路径。
    """
    return str(PROJECT_ROOT / p) if not os.path.isabs(p) else p


def common_datas() -> list:
    """项目自带的数据文件（非第三方包）。"""
    return [
        # 词云字体 + 停用词表（config.STOP_WORDS_FILE / FONT_PATH 引用）
        (_abs("docs/hit_stopwords.txt"), "docs"),
        (_abs("docs/STZHONGS.TTF"), "docs"),
        # 爬虫平台的配置和 JS 签名脚本（部分平台用 execjs 跑 .js 文件）
        (_abs("media_platform"), "media_platform"),
        (_abs("config"), "config"),
        # JS 签名脚本（douyin.js / zhihu.js / stealth.min.js）
        (_abs("libs"), "libs"),
        # 前端构建产物（api/main.py:WEBUI_DIR = api/webui/）
        # 不存在时不打包（dev 模式 vite 单独跑）
        *([(_abs("api/webui"), "api/webui")] if os.path.isdir(_abs("api/webui")) else []),
    ]


def common_hiddenimports() -> list:
    """PyInstaller 静态分析发现不了的导入。"""
    return [
        # uvicorn 运行时动态 import
        "uvicorn.logging",
        "uvicorn.protocols",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # DB 驱动（C 扩展）
        "asyncmy",
        "aiomysql",
        "asyncpg",
        "aiosqlite",
        # 中文分词 + 词云
        "jieba",
        "wordcloud",
        "matplotlib.backends.backend_agg",
        # 项目子模块（PyInstaller 默认按 import 抓，保险起见显式列）
    ] + collect_submodules("api") + collect_submodules("media_platform") + collect_submodules("config")


def heavy_deps() -> tuple[list, list, list]:
    """重型第三方依赖（fastapi 链路）。"""
    return _collect("fastapi", "uvicorn", "pydantic", "starlette")


def ai_deps() -> tuple[list, list, list]:
    """OpenAI-compatible LLM client + httpx transport.

    Only the api binary needs these — the cli/mcp binaries don't call the LLM.
    """
    return _collect("openai", "httpx")


def _find_chromium_bundle():
    """定位 playwright 安装的 chromium-XXXX 目录（完整目录，含 chrome-mac-arm64/...app）。

    返回 (目录路径, 目录名如 "chromium-1228") 或 (None, None)。
    必须保留整个目录结构，因为 playwright 运行时按
    {PLAYWRIGHT_BROWSERS_PATH}/chromium-XXXX/chrome-mac-arm64/Google Chrome for Testing.app 定位浏览器。
    """
    if sys.platform == "darwin":
        cache_glob = os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*")
    elif sys.platform == "win32":
        cache_glob = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright", "chromium-*")
    else:
        cache_glob = os.path.expanduser("~/.cache/ms-playwright/chromium-*")

    for c in sorted(glob.glob(cache_glob), reverse=True):
        c = Path(c)
        # macOS: chrome-mac-arm64/Google Chrome for Testing.app 或 chrome-mac/Chromium.app
        for sub in ("chrome-mac-arm64", "chrome-mac"):
            for app_name in ("Google Chrome for Testing.app", "Chromium.app"):
                if (c / sub / app_name).exists():
                    return c, c.name
        # Linux
        if (c / "chrome-linux" / "chrome").exists():
            return c, c.name
        # Windows
        if (c / "chrome-win" / "chrome.exe").exists():
            return c, c.name
    return None, None


def playwright_deps() -> tuple[list, list, list]:
    """Playwright Python 包（不含 Chromium 二进制）。

    Chromium 的 .app 带有代码签名，PyInstaller 会把里面的 Mach-O 当作 binary
    重新签名导致构建失败，所以这里只收集 playwright Python 包。Chromium 由
    post-build 步骤（pyinstaller/post_build.py）用 cp -R 原样拷贝到
    dist/<name>/_internal/playwright_driver/chromium-XXXX/，绕过 PyInstaller 签名处理。
    必须先用 `uv run playwright install chromium` 下载 Chromium。
    """
    datas, binaries, hidden = _collect("playwright")

    cr_dir, cr_name = _find_chromium_bundle()
    if not cr_dir:
        print(
            "⚠️  Playwright Chromium 未找到，请先运行: uv run playwright install chromium",
            file=sys.stderr,
        )
    # cr_dir / cr_name 供 post_build.py 使用，这里不进 datas

    return datas, binaries, hidden


def build_analysis(entry: str, *, include_playwright: bool, include_ai: bool = False):
    """生成 Analysis 对象，供 spec 主体调用。

    include_ai=True 时收集 openai/httpx（仅 api spec 需要）。
    """
    from PyInstaller.building.build_main import Analysis as _Analysis

    h_datas, h_binaries, h_hidden = heavy_deps()
    datas = common_datas() + h_datas
    binaries = list(h_binaries)
    hidden = common_hiddenimports() + h_hidden

    if include_playwright:
        pw_datas, pw_binaries, pw_hidden = playwright_deps()
        datas += pw_datas
        binaries += pw_binaries
        hidden += pw_hidden

    if include_ai:
        ai_d, ai_b, ai_h = ai_deps()
        datas += ai_d
        binaries += ai_b
        hidden += ai_h

    return _Analysis(
        [str(PROJECT_ROOT / entry) if not os.path.isabs(entry) else entry],
        pathex=[str(PROJECT_ROOT)],
        binaries=binaries,
        datas=datas,
        hiddenimports=hidden,
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
    )
