# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""Persist AI provider settings.

File: <data_dir>/ai_settings.json
Local plaintext storage — acceptable for desktop. The GET endpoint masks
the api_key before returning to the UI.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from ..schemas.ai import AISettings, AISettingsResponse

logger = logging.getLogger(__name__)


def _resolve_data_dir() -> Path:
    env_data_dir = os.environ.get("MEDIACRAWLER_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)
    return Path(__file__).parent.parent.parent


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "***"
    return f"{key[:3]}...{key[-4:]}"


class AISettingsManager:
    """Singleton."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._cache: Optional[AISettings] = None
        self._loaded = False

    @property
    def _path(self) -> Path:
        return _resolve_data_dir() / "ai_settings.json"

    async def _load_locked(self) -> AISettings:
        if self._loaded and self._cache is not None:
            return self._cache
        path = self._path
        if path.exists():
            try:
                raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
                data = json.loads(raw)
                self._cache = AISettings(**data)
            except Exception as e:
                logger.warning("Failed to load AI settings (%s); using defaults", e)
                self._cache = AISettings()
        else:
            self._cache = AISettings()
        self._loaded = True
        return self._cache

    async def get_raw_settings(self) -> AISettings:
        async with self._lock:
            return await self._load_locked()

    async def get_settings_response(self) -> AISettingsResponse:
        s = await self.get_raw_settings()
        return AISettingsResponse(
            provider=s.provider,
            base_url=s.base_url,
            api_key_masked=_mask_key(s.api_key),
            model=s.model,
            temperature=s.temperature,
            max_tokens=s.max_tokens,
            system_prompt_override=s.system_prompt_override,
            is_configured=bool(s.api_key),
        )

    async def save_settings(self, settings: AISettings) -> AISettingsResponse:
        async with self._lock:
            # If user did not retype the api_key, preserve the existing one.
            # This makes the common UI flow (open settings, tweak model, save)
            # not silently wipe the stored secret.
            existing = await self._load_locked()
            merged = settings.model_copy()
            if not merged.api_key and existing.api_key:
                merged.api_key = existing.api_key
            self._cache = merged
            path = self._path
            path.parent.mkdir(parents=True, exist_ok=True)
            text = merged.model_dump_json(indent=2)
            tmp = path.with_suffix(".json.tmp")
            await asyncio.to_thread(_atomic_write, path, tmp, text)
        return await self.get_settings_response()


def _atomic_write(target: Path, tmp: Path, text: str) -> None:
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


ai_settings = AISettingsManager()
