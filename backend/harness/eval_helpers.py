"""Shared helpers for harness scripts (regression eval, token budget)."""

from __future__ import annotations

import shutil
from pathlib import Path

from google.adk.agents.base_agent import BaseAgent
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_case import EvalCase, get_all_tool_calls
from google.adk.evaluation.eval_config import EvalConfig, get_eval_metrics_from_config
from google.adk.evaluation.eval_set import EvalSet
from google.adk.evaluation.evaluator import EvalStatus
from google.adk.evaluation.simulation.user_simulator_provider import UserSimulatorProvider

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_DIR = REPO_ROOT / "evals"
REPO_SKILLS_DIR = REPO_ROOT / "skills"

SKILL_ADD_ORDER = [
    "iqama-renewal-status",
    "traffic-violation-lookup",
    "government-fee-payment-draft",
    "appointment-slot-finder",
]

_NO_SKILL_SENTINELS = frozenset({"none", ""})


def _case_extra(eval_case: EvalCase) -> dict:
    return getattr(eval_case, "model_extra", None) or {}


def required_skills(eval_case: EvalCase) -> set[str]:
    """Skills whose folders must exist for this case to be runnable."""
    needed: set[str] = set()
    extra = _case_extra(eval_case)
    expected = extra.get("expected_skill") or getattr(eval_case, "expected_skill", None)
    if expected and str(expected).lower() not in _NO_SKILL_SENTINELS:
        needed.add(expected)

    if eval_case.conversation:
        for inv in eval_case.conversation:
            if not inv.intermediate_data:
                continue
            for fc in get_all_tool_calls(inv.intermediate_data):
                args = dict(fc.args) if fc.args else {}
                skill_name = args.get("skill_name")
                if skill_name:
                    needed.add(skill_name)
    return needed


def load_skill_config(skill_id: str) -> EvalConfig:
    config_path = EVALS_DIR / "configs" / f"{skill_id}.json"
    with config_path.open(encoding="utf-8") as f:
        return EvalConfig.model_validate_json(f.read())


def load_eval_set(skill_id: str) -> EvalSet:
    eval_set_path = EVALS_DIR / f"{skill_id}.evalset.json"
    with eval_set_path.open(encoding="utf-8") as f:
        return EvalSet.model_validate_json(f.read())


def filter_runnable_cases(eval_set: EvalSet, present_skills: set[str]) -> tuple[EvalSet, list[str]]:
    """Return a filtered EvalSet and eval_ids skipped due to missing skills."""
    runnable: list[EvalCase] = []
    skipped: list[str] = []
    for case in eval_set.eval_cases:
        needed = required_skills(case)
        if needed <= present_skills:
            runnable.append(case)
        else:
            missing = sorted(needed - present_skills)
            skipped.append(f"{eval_set.eval_set_id}:{case.eval_id} (needs {missing})")
    filtered = eval_set.model_copy(update={"eval_cases": runnable})
    return filtered, skipped


def build_subset_skills_dir(src: Path, skill_ids: list[str], dest: Path) -> Path:
    """Copy selected skill folders into *dest* and return *dest*."""
    dest.mkdir(parents=True, exist_ok=True)
    for skill_id in skill_ids:
        shutil.copytree(src / skill_id, dest / skill_id)
    return dest


async def run_eval_set(
    agent: BaseAgent,
    skill_id: str,
    present_skills: set[str],
) -> tuple[dict[str, EvalStatus], list[str]]:
    """Run filtered eval cases for *skill_id*; return per-case status and skips."""
    eval_set = load_eval_set(skill_id)
    eval_config = load_skill_config(skill_id)
    filtered, skipped = filter_runnable_cases(eval_set, present_skills)

    if not filtered.eval_cases:
        return {}, skipped

    eval_metrics = get_eval_metrics_from_config(eval_config)
    results_by_id = await AgentEvaluator._get_eval_results_by_eval_id(
        agent_for_eval=agent,
        eval_set=filtered,
        eval_metrics=eval_metrics,
        num_runs=1,
        user_simulator_provider=UserSimulatorProvider(),
    )

    statuses: dict[str, EvalStatus] = {}
    for eval_id, case_results in results_by_id.items():
        statuses[eval_id] = case_results[0].final_eval_status
    return statuses, skipped
