# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""OpenAI-compatible async streaming chat client.

Works with OpenAI, DeepSeek, Qwen (OpenAI-compatible mode), Ollama,
LM Studio, OpenRouter, and any OpenAI-compatible endpoint by setting
base_url.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from ..schemas.ai import AISettings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: AISettings):
        self.client = AsyncOpenAI(
            api_key=settings.api_key or "dummy",
            base_url=settings.base_url,
        )
        self.model = settings.model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens

    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        """Yields content chunks (str) as they arrive.

        Raises openai.* exceptions on error — caller is responsible for
        translating to HTTP / SSE error frames.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
