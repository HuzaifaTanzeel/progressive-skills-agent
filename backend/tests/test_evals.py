"""Run GovTech Skills Assistant eval suites with per-skill ADK criteria."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_case import get_all_tool_calls
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet
from google.adk.evaluation.in_memory_eval_sets_manager import InMemoryEvalSetsManager
from google.adk.evaluation.local_eval_service import LocalEvalService
from google.adk.evaluation.base_eval_service import InferenceConfig, InferenceRequest
from google.adk.utils.context_utils import Aclosing

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = REPO_ROOT / "evals"
MANIFEST_PATH = EVALS_DIR / "eval_config.json"

SKILL_EVAL_SETS = [
    "iqama-renewal-status",
    "traffic-violation-lookup",
    "government-fee-payment-draft",
    "appointment-slot-finder",
]


def _load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _skill_config(skill_id: str) -> EvalConfig:
    config_path = EVALS_DIR / "configs" / f"{skill_id}.json"
    with config_path.open(encoding="utf-8") as f:
        return EvalConfig.model_validate_json(f.read())


def _load_eval_set(skill_id: str) -> EvalSet:
    eval_set_path = EVALS_DIR / f"{skill_id}.evalset.json"
    with eval_set_path.open(encoding="utf-8") as f:
        return EvalSet.model_validate_json(f.read())


def _tool_calls_from_invocation(inv) -> list[tuple[str, dict]]:
    return [
        (fc.name, dict(fc.args) if fc.args else {})
        for fc in get_all_tool_calls(inv.intermediate_data)
    ]


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


@pytest.fixture(scope="session", autouse=True)
def _load_env() -> None:
    load_dotenv(REPO_ROOT / "backend" / "adk_app" / ".env")


@pytest.mark.llm
@pytest.mark.parametrize("skill_id", SKILL_EVAL_SETS)
@pytest.mark.asyncio
async def test_skill_eval_set(skill_id: str) -> None:
    if not _has_api_key():
        pytest.skip("OPENAI_API_KEY not set; skipping LLM eval suite")
    await AgentEvaluator.evaluate_eval_set(
        agent_module="adk_app",
        eval_set=_load_eval_set(skill_id),
        eval_config=_skill_config(skill_id),
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.llm
@pytest.mark.asyncio
async def test_adversarial_routing_cases() -> None:
    if not _has_api_key():
        pytest.skip("OPENAI_API_KEY not set; skipping adversarial routing eval")

    manifest = _load_manifest()
    agent = await AgentEvaluator._get_agent_for_eval(
        module_name="adk_app", agent_name=None
    )
    failures: list[str] = []

    for case in manifest["adversarial_routing_cases"]:
        eval_set = _load_eval_set(case["eval_set_id"])
        target = next(e for e in eval_set.eval_cases if e.eval_id == case["eval_id"])

        mgr = InMemoryEvalSetsManager()
        mgr.create_eval_set(app_name="test_app", eval_set_id=eval_set.eval_set_id)
        mgr.add_eval_case(
            app_name="test_app",
            eval_set_id=eval_set.eval_set_id,
            eval_case=target,
        )

        service = LocalEvalService(root_agent=agent, eval_sets_manager=mgr)
        req = InferenceRequest(
            app_name="test_app",
            eval_set_id=eval_set.eval_set_id,
            inference_config=InferenceConfig(),
        )
        async with Aclosing(service.perform_inference(inference_request=req)) as agen:
            inference_results = [item async for item in agen]

        inv = inference_results[0].inferences[0]
        tool_calls = _tool_calls_from_invocation(inv)
        tool_names = [name for name, _ in tool_calls]
        loaded_skills = [
            args.get("skill_name")
            for name, args in tool_calls
            if name == "load_skill"
        ]
        expected = case["expected_skill"]
        forbidden = case.get("must_not_load_skill")
        must_not_call = case.get("must_not_call_tool")
        must_call = case.get("must_call_tool")

        routed_ok = expected in loaded_skills
        forbidden_ok = forbidden not in loaded_skills if forbidden else True
        must_not_ok = must_not_call not in tool_names if must_not_call else True
        must_call_ok = must_call in tool_names if must_call else True

        if not routed_ok or not forbidden_ok or not must_not_ok or not must_call_ok:
            failures.append(
                f"{case['eval_set_id']}:{case['eval_id']} "
                f"expected load_skill({expected}), forbidden_skill={forbidden}, "
                f"must_call={must_call}, must_not_call={must_not_call}; "
                f"actual load_skill calls={loaded_skills}; tools={tool_calls}"
            )

    assert not failures, "Adversarial routing failures:\n" + "\n".join(failures)
