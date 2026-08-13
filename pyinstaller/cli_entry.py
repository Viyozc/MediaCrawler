# -*- coding: utf-8 -*-
"""PyInstaller 入口：替代 `python main.py`。

参数完全透传给 main.py 的 parse_cmd / main / async_cleanup 流程。
直接复用 main 模块已定义好的 main / async_cleanup / crawler 全局变量，
不重复实现，保证行为与 python main.py 一致。
"""
from __future__ import annotations

# 必须放在所有应用 import 之前，让运行时补丁先生效
import pyinstaller.runtime_patches  # noqa: F401

import main as main_module
from tools.app_runner import run


def _force_stop() -> None:
    """与 main.py 末尾 _force_stop 一致：首次 Ctrl+C 时清理 CDP launcher。"""
    c = main_module.crawler
    if not c:
        return
    cdp_manager = getattr(c, "cdp_manager", None)
    launcher = getattr(cdp_manager, "launcher", None)
    if not launcher:
        return
    try:
        launcher.cleanup()
    except Exception:
        pass


if __name__ == "__main__":
    run(
        main_module.main,
        main_module.async_cleanup,
        cleanup_timeout_seconds=15.0,
        on_first_interrupt=_force_stop,
    )
