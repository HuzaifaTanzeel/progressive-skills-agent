"""Off-topic prompts must not load any skill (pytest-only; not ADK response-scored)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.base_eval_service import InferenceConfig, InferenceRequest
from google.adk.evaluation.eval_case import EvalCase, Invocation, get_all_tool_calls
from google.adk.evaluation.in_memory_eval_sets_manager import InMemoryEvalSetsManager
from google.adk.evaluation.local_eval_service import LocalEvalService
from google.adk.utils.context_utils import Aclosing
from google.genai import types as genai_types

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "evals" / "eval_config.json"


@pytest.fixture(scope="session", autouse=True)
def _load_env() -> None:
    load_dotenv(REPO_ROOT / "backend" / "adk_app" / ".env")


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


@pytest.mark.llm
@pytest.mark.asyncio
async def test_offtopic_no_skill_cases() -> None:
    if not _has_api_key():
        pytest.skip("OPENAI_API_KEY not set; skipping offtopic eval")

    with MANIFEST_PATH.open(encoding="utf-8") as f:
        manifest = json.load(f)
    cases = manifest.get("offtopic_no_skill_cases", [])
    if not cases:
        pytest.skip("No offtopic_no_skill_cases in manifest")

    agent = await AgentEvaluator._get_agent_for_eval(
        module_name="adk_app", agent_name=None
    )
    failures: list[str] = []

    for case in cases:
        inv = Invocation(
            invocation_id=case["eval_id"],
            user_content=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=case["prompt"])],
            ),
        )
        target = EvalCase(
            eval_id=case["eval_id"],
            conversation=[inv],
            session_input={
                "app_name": "adk_app",
                "user_id": "eval_user",
                "state": {},
            },
        )

        mgr = InMemoryEvalSetsManager()
        mgr.create_eval_set(app_name="test_app", eval_set_id="offtopic")
        mgr.add_eval_case(
            app_name="test_app", eval_set_id="offtopic", eval_case=target
        )

        service = LocalEvalService(root_agent=agent, eval_sets_manager=mgr)
        req = InferenceRequest(
            app_name="test_app",
            eval_set_id="offtopic",
            inference_config=InferenceConfig(),
        )
        async with Aclosing(service.perform_inference(inference_request=req)) as agen:
            inference_results = [item async for item in agen]

        inv_out = inference_results[0].inferences[0]
        tool_calls = [
            (fc.name, dict(fc.args) if fc.args else {})
            for fc in get_all_tool_calls(inv_out.intermediate_data)
        ]
        loaded = [
            args.get("skill_name")
            for name, args in tool_calls
            if name == "load_skill"
        ]
        if loaded:
            failures.append(
                f"{case['eval_set_id']}:{case['eval_id']} "
                f"loaded skills={loaded}; tools={tool_calls}"
            )

    assert not failures, "Offtopic no-skill failures:\n" + "\n".join(failures)
