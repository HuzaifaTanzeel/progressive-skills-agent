"""Simplified chat API for the custom frontend."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from google.adk.runners import Runner
from google.genai import types
from pydantic import BaseModel, Field

from adk_app.agent import app as adk_app

router = APIRouter(prefix="/api", tags=["chat"])

# Shared across requests; main.py may replace with the FastAPI-wired session service.
_session_service = None
_runner: Runner | None = None


def configure_chat(session_service: Any) -> None:
    """Wire the same session service used by get_fast_api_app."""
    global _session_service, _runner
    _session_service = session_service
    _runner = Runner(
        app=adk_app,
        session_service=session_service,
        auto_create_session=True,
    )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = "demo_user"
    session_id: str | None = None


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    skill_used: str | None
    tool_trajectory: list[ToolCall]
    session_id: str


def _extract_from_events(events: list[Any]) -> tuple[str, str | None, list[ToolCall]]:
    texts: list[str] = []
    trajectory: list[ToolCall] = []
    skill_used: str | None = None

    for event in events:
        content = getattr(event, "content", None)
        if content is None:
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                name = getattr(fc, "name", None) or ""
                args = dict(getattr(fc, "args", None) or {})
                trajectory.append(ToolCall(name=name, args=args))
                if name == "load_skill" and skill_used is None:
                    skill_used = args.get("skill_name") or args.get("skillName")
                continue
            text = getattr(part, "text", None)
            if text:
                role = getattr(content, "role", None)
                # Prefer model/assistant text for the final response.
                if role in (None, "model", "assistant"):
                    texts.append(text)

    response = texts[-1] if texts else ""
    return response, skill_used, trajectory


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    if _runner is None or _session_service is None:
        raise HTTPException(
            status_code=503,
            detail="Chat runner not configured; server startup incomplete.",
        )

    session_id = body.session_id or str(uuid.uuid4())
    app_name = adk_app.name

    # Ensure session exists (auto_create_session on Runner may also handle this).
    session = await _session_service.get_session(
        app_name=app_name,
        user_id=body.user_id,
        session_id=session_id,
    )
    if session is None:
        await _session_service.create_session(
            app_name=app_name,
            user_id=body.user_id,
            session_id=session_id,
        )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=body.message)],
    )

    events: list[Any] = []
    async for event in _runner.run_async(
        user_id=body.user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        events.append(event)

    response, skill_used, trajectory = _extract_from_events(events)
    return ChatResponse(
        response=response,
        skill_used=skill_used,
        tool_trajectory=trajectory,
        session_id=session_id,
    )
