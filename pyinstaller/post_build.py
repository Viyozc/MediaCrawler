# -*- coding: utf-8 -*-
"""Post-build: 把 Playwright Chromium 拷贝到 PyInstaller 产物里。

PyInstaller 无法直接打包带签名的 Chromium.app（会把 Mach-O 当 binary 重新签名而失败），
所以构建后用 shutil.copytree 原样拷贝，保留 playwright 期望的目录结构：
    dist/<name>/_internal/playwright_driver/chromium-XXXX/chrome-mac-arm64/...app

用法：
    uv run pyinstaller pyinstaller/mediacrawler-cli.spec --noconfirm
    uv run python pyinstaller/post_build.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pyinstaller._common import _find_chromium_bundle

# 只有 cli spec 开了 include_playwright=True；api spec 不含 playwright_driver，无需拷贝
TARGETS = [
    PROJECT_ROOT / "dist" / "mediacrawler-cli" / "_internal" / "playwright_driver",
]


def main() -> int:
    cr_dir, cr_name = _find_chromium_bundle()
    if not cr_dir:
        print(
            "⚠️  Playwright Chromium 未找到，请先运行: uv run playwright install chromium",
            file=sys.stderr,
        )
        return 1

    ok = False
    for target_root in TARGETS:
        if not target_root.parent.exists():
            print(f"– 跳过 {target_root}（父目录不存在，对应二进制可能未构建）")
            continue
        target_root.mkdir(parents=True, exist_ok=True)
        dest = target_root / cr_name
        if dest.exists():
            shutil.rmtree(dest)
        print(f"→ copy {cr_dir}  →  {dest}")
        shutil.copytree(cr_dir, dest, symlinks=True)
        ok = True

    if not ok:
        print("⚠️  没有找到任何 dist 产物目录，请先运行 pyinstaller 构建。", file=sys.stderr)
        return 1

    print("✓ Chromium 拷贝完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
