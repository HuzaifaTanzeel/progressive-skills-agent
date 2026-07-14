"""Unit tests for progressive skill activation / unload (no LLM)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.adk.skills import load_skill_from_dir

from adk_app.agent_factory import REPO_SKILLS_DIR
from adk_app.code_executor import demo_code_executor
from adk_app.demo_tools import DEMO_TOOLS
from adk_app.progressive_skill_toolset import (
    ProgressiveSkillToolset,
    activated_skills_state_key,
)


class _FakeToolContext:
    def __init__(self, agent_name: str = "govtech_assistant"):
        self.agent_name = agent_name
        self.invocation_id = "test-inv"
        self.state: dict = {}


def _toolset() -> ProgressiveSkillToolset:
    skills = [
        load_skill_from_dir(d)
        for d in sorted(REPO_SKILLS_DIR.iterdir())
        if d.is_dir()
    ]
    return ProgressiveSkillToolset(
        skills=skills,
        code_executor=demo_code_executor,
        additional_tools=list(DEMO_TOOLS),
    )


def _load_tool(toolset: ProgressiveSkillToolset):
    return next(t for t in toolset._tools if t.name == "load_skill")


def _unload_tool(toolset: ProgressiveSkillToolset):
    return next(t for t in toolset._tools if t.name == "unload_skill")


@pytest.mark.asyncio
async def test_load_skill_replaces_previous_activation() -> None:
    toolset = _toolset()
    ctx = _FakeToolContext()
    load = _load_tool(toolset)
    state_key = activated_skills_state_key(ctx.agent_name)

    first = await load.run_async(
        args={"skill_name": "traffic-violation-lookup"},
        tool_context=ctx,  # type: ignore[arg-type]
    )
    assert first["skill_name"] == "traffic-violation-lookup"
    assert ctx.state[state_key] == ["traffic-violation-lookup"]

    second = await load.run_async(
        args={"skill_name": "appointment-slot-finder"},
        tool_context=ctx,  # type: ignore[arg-type]
    )
    assert second["skill_name"] == "appointment-slot-finder"
    assert second["unloaded_previous_skills"] == ["traffic-violation-lookup"]
    assert ctx.state[state_key] == ["appointment-slot-finder"]
    assert second["activated_skills"] == ["appointment-slot-finder"]


@pytest.mark.asyncio
async def test_unload_skill_clears_activation() -> None:
    toolset = _toolset()
    ctx = _FakeToolContext()
    load = _load_tool(toolset)
    unload = _unload_tool(toolset)
    state_key = activated_skills_state_key(ctx.agent_name)

    await load.run_async(
        args={"skill_name": "iqama-renewal-status"},
        tool_context=ctx,  # type: ignore[arg-type]
    )
    assert ctx.state[state_key] == ["iqama-renewal-status"]

    result = await unload.run_async(args={}, tool_context=ctx)  # type: ignore[arg-type]
    assert result["unloaded"] == ["iqama-renewal-status"]
    assert ctx.state[state_key] == []


@pytest.mark.asyncio
async def test_only_active_skill_domain_tools_resolve() -> None:
    toolset = _toolset()
    ctx = _FakeToolContext()
    load = _load_tool(toolset)
    state_key = activated_skills_state_key(ctx.agent_name)

    await load.run_async(
        args={"skill_name": "traffic-violation-lookup"},
        tool_context=ctx,  # type: ignore[arg-type]
    )
    await load.run_async(
        args={"skill_name": "appointment-slot-finder"},
        tool_context=ctx,  # type: ignore[arg-type]
    )
    assert ctx.state[state_key] == ["appointment-slot-finder"]

    readonly = SimpleNamespace(
        agent_name=ctx.agent_name,
        invocation_id=ctx.invocation_id,
        state=ctx.state,
    )
    tools = await toolset._resolve_additional_tools_from_state(readonly)  # type: ignore[arg-type]
    names = {t.name for t in tools}
    # Appointment skill tools only — not traffic's get_violation_by_code.
    assert "list_centers_by_city" in names
    assert "list_available_slots" in names
    assert "get_violation_by_code" not in names


def test_toolset_exposes_unload_skill_not_list_skills() -> None:
    toolset = _toolset()
    names = [t.name for t in toolset._tools]
    assert "unload_skill" in names
    assert "list_skills" not in names
    assert names.count("load_skill") == 1


@pytest.mark.asyncio
async def test_process_llm_request_injects_l1_catalog() -> None:
    """Paper: L1 metadata always in system instructions, not via list_skills."""
    toolset = _toolset()
    appended: list[str] = []

    class _Req:
        def append_instructions(self, parts):
            appended.extend(parts)

    await toolset.process_llm_request(
        tool_context=_FakeToolContext(),  # type: ignore[arg-type]
        llm_request=_Req(),  # type: ignore[arg-type]
    )
    blob = "\n".join(appended)
    assert "<available_skills>" in blob
    assert "traffic-violation-lookup" in blob
    assert "government-fee-payment-draft" in blob
    assert "never invent or paraphrase names" in blob.lower() or "never invent" in blob
