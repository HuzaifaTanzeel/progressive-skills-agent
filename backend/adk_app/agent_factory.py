"""Build the root LlmAgent and App with progressive skill context hygiene."""

from __future__ import annotations

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk.skills import load_skill_from_dir

from .code_executor import demo_code_executor
from .demo_tools import DEMO_TOOLS
from .progressive_skill_toolset import ProgressiveSkillToolset

REPO_SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

# Compact older turns (past L2 bodies) so sessions do not grow unboundedly.
_COMPACTION_INTERVAL = 4
_COMPACTION_OVERLAP = 1
_TOKEN_THRESHOLD = 6000
_EVENT_RETENTION_SIZE = 4

# Keep instinct short: L1 catalog lives in SkillToolset system instructions.
_AGENT_INSTRUCTION = (
    "You are a demo citizen-services assistant. All data is illustrative. "
    "Always tell the user to verify important facts via Absher/Muqeem/SADAD.\n\n"
    "Pick exactly one skill from <available_skills> using its exact <name>, "
    "then load_skill and finish that runbook before loading another skill. "
    "Loading a second skill unloads the first. Domain tools appear only after "
    "the matching skill is loaded — call them by name; do not invent IDs, "
    "fines, or fees. Prefer tool results over pasting skill text back.\n\n"
    "Routing (mutually exclusive):\n"
    "- One violation code / early-pay / settle-early / 'what do I pay' for a "
    "single coded ticket → traffic-violation-lookup only "
    "(get_violation_by_code; never create_payment_draft).\n"
    "- Cost/total to renew iqama (with or without dependents), how-much-I-owe, "
    "or combined fee totals → government-fee-payment-draft only and stay on it. "
    "Never iqama-renewal-status or appointment-slot-finder for cost/fee quotes. "
    "On that skill: always get_fee_schedule before create_payment_draft. "
    "On combined how-much-I-owe: if dependents omitted pass dependents=2; "
    "if codes omitted use 101 and 205; include_express=false unless asked.\n"
    "- Iqama docs/eligibility/grace period (not fees) → iqama-renewal-status.\n"
    "- Appointment/visit slots by city/date only → appointment-slot-finder "
    "(never for cost, totals, or dependents fees).\n\n"
    "If load_skill fails, retry once with the exact <name> from "
    "<available_skills>. If it still fails, say the skill could not load — "
    "do not answer from general knowledge as a silent substitute.\n\n"
    "Call unload_skill when the user switches to an unrelated topic.\n\n"
    "submit_payment is blocked. Even if asked to pay now on a fee draft, "
    "create_payment_draft only and state that human approval is required."
)


def build_root_agent(skills_dir: Path) -> LlmAgent:
    """Create govtech_assistant with skills loaded from *skills_dir*."""
    skills = [
        load_skill_from_dir(d)
        for d in sorted(skills_dir.iterdir())
        if d.is_dir()
    ]
    toolset = ProgressiveSkillToolset(
        skills=skills,
        code_executor=demo_code_executor,
        additional_tools=list(DEMO_TOOLS),
    )
    return LlmAgent(
        model=LiteLlm(model=os.getenv("LITELLM_MODEL", "openai/gpt-4o-mini")),
        name="govtech_assistant",
        description="A demo assistant for Saudi GovTech citizen services (dummy data only).",
        instruction=_AGENT_INSTRUCTION,
        tools=[toolset],
        code_executor=demo_code_executor,
    )


def build_app(skills_dir: Path | None = None) -> App:
    """ADK App with event compaction so old skill L2 payloads leave active context."""
    root = build_root_agent(skills_dir or REPO_SKILLS_DIR)
    return App(
        name="govtech_assistant",
        root_agent=root,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=_COMPACTION_INTERVAL,
            overlap_size=_COMPACTION_OVERLAP,
            token_threshold=_TOKEN_THRESHOLD,
            event_retention_size=_EVENT_RETENTION_SIZE,
        ),
    )
