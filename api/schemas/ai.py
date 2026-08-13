# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""AI provider settings, chat request schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field


# Recognized provider values for UI dropdown presets.
# Any other string is accepted as "custom" OpenAI-compatible endpoint.
KNOWN_PROVIDERS = {
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "ollama": {"base_url": "http://localhost:11434/v1", "model": "qwen2.5"},
    "lmstudio": {"base_url": "http://localhost:1234/v1", "model": "local-model"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "model": "anthropic/claude-3.5-sonnet"},
}


class AISettings(BaseModel):
    """User's AI provider config. Stored locally as plaintext JSON.

    The api_key is stored as-is for desktop convenience. The GET endpoint
    returns a masked version (AISettingsResponse).
    """
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    system_prompt_override: Optional[str] = None


class AISettingsResponse(BaseModel):
    """GET response — api_key masked."""
    provider: str
    base_url: str
    api_key_masked: str
    model: str
    temperature: float
    max_tokens: int
    system_prompt_override: Optional[str] = None
    is_configured: bool


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    task_id: str
    messages: List[ChatMessage]
    include_full_data: bool = False
    sample_size: int = Field(default=20, ge=1, le=500)
