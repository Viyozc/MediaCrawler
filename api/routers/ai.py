# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1

"""AI provider settings + Agent Chat endpoints.

GET  /api/ai/settings            masked settings + is_configured
PUT  /api/ai/settings            save settings (plaintext local)
POST /api/ai/chat                SSE streaming chat over task data
GET  /api/ai/chat/{task_id}/history   load prior chat transcript
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..schemas.ai import AISettings, AISettingsResponse, ChatRequest
from ..schemas import TaskStatus
from ..services.ai_settings import ai_settings, _resolve_data_dir
from ..services.task_registry import task_registry
from ..services.context_builder import build_task_context
from ..services.llm_client import LLMClient
from ..services.output_scanner import scan_all_for_platform, infer_record_counts

router = APIRouter(prefix="/ai", tags=["ai"])

DEFAULT_SYSTEM_PROMPT = """You are a data analysis assistant for MediaCrawler Pro, \
a social media crawling tool. The user has completed a crawl task and wants \
to analyze the results. You can see the task configuration and a sample of \
the crawled data in the context block below. Help the user understand \
patterns, summarize findings, suggest next steps, or answer questions about \
the data. Respond in the user's language (Chinese if they write in Chinese)."""


def _chat_file(task_id: str) -> Path:
    chats_dir = _resolve_data_dir() / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    return chats_dir / f"{task_id}.jsonl"


async def _persist_message(task_id: str, role: str, content: str) -> None:
    line = json.dumps(
        {"role": role, "content": content, "ts": datetime.now().isoformat(timespec="seconds")},
        ensure_ascii=False,
    )
    path = _chat_file(task_id)
    await asyncio.to_thread(_append_text, path, line + "\n")


def _append_text(path: Path, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def _read_transcript_sync(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


# ---- Settings ----

@router.get("/settings", response_model=AISettingsResponse)
async def get_ai_settings():
    return await ai_settings.get_settings_response()


@router.put("/settings", response_model=AISettingsResponse)
async def update_ai_settings(settings: AISettings):
    return await ai_settings.save_settings(settings)


# ---- Chat transcript history ----

@router.get("/chat/{task_id}/history")
async def get_chat_history(task_id: str):
    rec = await task_registry.get_task(task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    transcript = await asyncio.to_thread(_read_transcript_sync, _chat_file(task_id))
    return {"messages": transcript, "task_id": task_id}


# ---- Streaming chat ----

@router.post("/chat")
async def chat(req: ChatRequest):
    """SSE streaming chat. Each event is a JSON object:
       {"type": "token"|"done"|"error", ...}
    """
    settings = await ai_settings.get_raw_settings()
    if not settings.api_key:
        raise HTTPException(400, "AI not configured. Set API key in settings.")

    rec = await task_registry.get_task(req.task_id)
    if not rec:
        raise HTTPException(404, detail="Task not found")

    # Fallback re-scan: if the task is finished but has no output_files
    # (e.g. it ran before the cwd fix, or the mtime window missed),
    # scan the platform dir and persist what we find. This makes AI chat
    # resilient to scanner/timing bugs.
    finished_statuses = {
        TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.STOPPED.value,
    }
    if not rec.get("output_files") and rec.get("status") in finished_statuses:
        platform = rec.get("platform")
        if platform:
            try:
                files = await scan_all_for_platform(platform)
                if files:
                    counts = infer_record_counts(files)
                    rec = await task_registry.update_output_files(
                        req.task_id, files, counts
                    ) or rec
            except Exception:
                # Best-effort; chat proceeds with whatever context we have
                pass

    # Build context from task record
    from ..schemas import TaskRecord
    task = TaskRecord(**rec)
    try:
        context = await build_task_context(
            task,
            include_full_data=req.include_full_data,
            sample_size=req.sample_size,
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to build context: {e}")

    system_prompt = (settings.system_prompt_override or DEFAULT_SYSTEM_PROMPT).strip()
    system_prompt += f"\n\n## Task Data Context\n{context}\n"

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    # Persist the latest user message (only user messages from this turn)
    for m in req.messages:
        if m.role == "user":
            await _persist_message(req.task_id, "user", m.content)

    llm = LLMClient(settings)

    task_id = req.task_id

    async def event_stream() -> AsyncIterator[bytes]:
        full_response = ""
        try:
            async for chunk in llm.stream_chat(messages):
                full_response += chunk
                payload = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n".encode("utf-8")

            await _persist_message(task_id, "assistant", full_response)
            yield f"data: {json.dumps({'type': 'done', 'tokens': len(full_response)})}\n\n".encode("utf-8")
        except Exception as e:
            err_payload = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {err_payload}\n\n".encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })
