# -*- coding: utf-8 -*-
"""output_scanner must map API platform codes to on-disk store directories.

Task records store PlatformEnum values (dy/ks/wb), but AsyncFileWriter
writes under full names (douyin/kuaishou/weibo). Scanning the wrong dir
leaves output_files empty and AI chat reports (no output files).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from api.services import output_scanner as scanner


@pytest.fixture
def data_tree(tmp_path, monkeypatch):
    """Create <tmp>/data/<store_dir>/json/search_contents_*.json layout."""
    monkeypatch.setenv("MEDIACRAWLER_DATA_DIR", str(tmp_path))

    def _seed(store_dir: str, filename: str = "search_contents_2026-08-10.json") -> Path:
        target = tmp_path / "data" / store_dir / "json" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps([{"id": "1", "title": "hello"}]), encoding="utf-8")
        return target

    return _seed


@pytest.mark.parametrize(
    "api_code,store_dir",
    [
        ("dy", "douyin"),
        ("ks", "kuaishou"),
        ("wb", "weibo"),
        ("xhs", "xhs"),
        ("bili", "bili"),
        ("tieba", "tieba"),
        ("zhihu", "zhihu"),
    ],
)
def test_scan_all_maps_api_code_to_store_dir(data_tree, api_code, store_dir):
    data_tree(store_dir)
    files = scanner.scan_all_for_platform_sync(api_code)
    assert len(files) >= 1
    assert files[0].path.startswith(f"{store_dir}/")


@pytest.mark.parametrize(
    "api_code,store_dir",
    [
        ("dy", "douyin"),
        ("ks", "kuaishou"),
        ("wb", "weibo"),
    ],
)
def test_scan_mtime_window_maps_api_code(data_tree, api_code, store_dir):
    path = data_tree(store_dir)
    mtime = path.stat().st_mtime
    started = datetime.fromtimestamp(mtime) - timedelta(seconds=5)
    ended = datetime.fromtimestamp(mtime) + timedelta(seconds=5)
    files = scanner.scan_output_files_sync(api_code, started, ended)
    assert len(files) >= 1
    assert store_dir in files[0].path


def test_scan_all_dy_does_not_look_under_literal_dy(data_tree, tmp_path):
    """Regression: must not require data/dy/ when files live in data/douyin/."""
    data_tree("douyin")
    assert not (tmp_path / "data" / "dy").exists()
    files = scanner.scan_all_for_platform_sync("dy")
    assert len(files) >= 1
