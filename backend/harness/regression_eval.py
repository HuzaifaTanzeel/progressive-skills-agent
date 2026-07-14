"""Incremental skill-library regression eval.

Runs the eval suite with skills added one at a time (iqama -> traffic ->
fee-draft -> appointment) and checks that previously-passing cases still pass.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google.adk.evaluation.evaluator import EvalStatus
from tabulate import tabulate

from adk_app.agent_factory import build_root_agent
from harness.eval_helpers import (
    REPO_SKILLS_DIR,
    SKILL_ADD_ORDER,
    build_subset_skills_dir,
    run_eval_set,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "evals" / "results" / "regression_eval_report.md"
DEFAULT_JSON_OUTPUT = REPO_ROOT / "evals" / "results" / "regression_eval_report.json"


@dataclass
class StepResult:
    step: int
    present_skills: list[str]
    added_skill: str | None
    passed: dict[str, set[str]] = field(default_factory=dict)
    failed: dict[str, set[str]] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)


def _case_key(skill_id: str, eval_id: str) -> str:
    return f"{skill_id}:{eval_id}"


async def run_regression() -> list[StepResult]:
    previous_passing: set[str] = set()
    steps: list[StepResult] = []

    for step_idx, present in enumerate(SKILL_ADD_ORDER, start=1):
        present_list = SKILL_ADD_ORDER[:step_idx]
        added = present if step_idx > 1 else None
        present_set = set(present_list)

        with tempfile.TemporaryDirectory(prefix="regression_skills_") as tmp:
            skills_dir = build_subset_skills_dir(
                REPO_SKILLS_DIR, present_list, Path(tmp)
            )
            agent = build_root_agent(skills_dir)

            step = StepResult(
                step=step_idx,
                present_skills=present_list,
                added_skill=added,
            )

            for skill_id in present_list:
                statuses, skipped = await run_eval_set(
                    agent, skill_id, present_set, retries=1
                )
                step.skipped.extend(skipped)

                passed_ids = {
                    eid for eid, st in statuses.items() if st == EvalStatus.PASSED
                }
                failed_ids = {
                    eid for eid, st in statuses.items() if st != EvalStatus.PASSED
                }
                step.passed[skill_id] = passed_ids
                step.failed[skill_id] = failed_ids

                for eval_id in failed_ids:
                    key = _case_key(skill_id, eval_id)
                    if key in previous_passing:
                        culprit = added or "(baseline)"
                        step.regressions.append(
                            f"{culprit} broke {key} (status={statuses[eval_id].name})"
                        )

            current_passing = {
                _case_key(skill_id, eval_id)
                for skill_id, ids in step.passed.items()
                for eval_id in ids
            }
            previous_passing = current_passing
            steps.append(step)

    return steps


def format_report(steps: list[StepResult]) -> str:
    lines = [
        "# Skill Library Regression Eval Report",
        "",
        f"Run date: {date.today().isoformat()}.",
        "Order: iqama-renewal-status -> traffic-violation-lookup -> "
        "government-fee-payment-draft -> appointment-slot-finder.",
        "",
        "Cross-skill routing cases are skipped until all referenced skills "
        "are present in the temp skills/ copy (dependency-aware filtering).",
        "",
    ]

    step_rows = []
    for s in steps:
        run_count = sum(len(v) + len(s.failed.get(k, set())) for k, v in s.passed.items())
        pass_count = sum(len(v) for v in s.passed.values())
        step_rows.append([
            s.step,
            ", ".join(s.present_skills),
            s.added_skill or "(baseline)",
            run_count,
            pass_count,
            len(s.skipped),
            len(s.regressions),
        ])

    lines.extend([
        "## Step summary",
        "",
        tabulate(
            step_rows,
            headers=["Step", "Skills present", "Added", "Cases run", "Passed", "Skipped", "Regressions"],
            tablefmt="github",
        ),
        "",
    ])

    all_regressions = [r for s in steps for r in s.regressions]
    lines.extend([
        "## Regression details",
        "",
    ])
    if all_regressions:
        for r in all_regressions:
            lines.append(f"- {r}")
    else:
        lines.append("No unexpected regressions detected.")
    lines.append("")

    for s in steps:
        if s.skipped:
            lines.extend([
                f"### Step {s.step} skipped cases",
                "",
            ])
            for skip in s.skipped:
                lines.append(f"- {skip}")
            lines.append("")

    total_regressions = len(all_regressions)
    lines.extend([
        "## Verdict",
        "",
        f"**{total_regressions} unexpected regression(s).**",
        "",
    ])
    return "\n".join(lines)


def steps_to_json_payload(steps: list[StepResult]) -> dict:
    """Serialize regression steps for the admin API (JSON-safe)."""
    step_summaries = []
    for s in steps:
        run_count = sum(
            len(v) + len(s.failed.get(k, set())) for k, v in s.passed.items()
        )
        pass_count = sum(len(v) for v in s.passed.values())
        step_summaries.append({
            "step": s.step,
            "present_skills": s.present_skills,
            "added_skill": s.added_skill,
            "cases_run": run_count,
            "passed": pass_count,
            "skipped": len(s.skipped),
            "regressions": len(s.regressions),
            "passed_ids": {k: sorted(v) for k, v in s.passed.items()},
            "failed_ids": {k: sorted(v) for k, v in s.failed.items()},
            "skipped_cases": list(s.skipped),
            "regression_details": list(s.regressions),
        })

    all_regressions = [r for s in steps for r in s.regressions]
    return {
        "run_date": date.today().isoformat(),
        "order": list(SKILL_ADD_ORDER),
        "steps": step_summaries,
        "total_regressions": len(all_regressions),
        "verdict": (
            f"{len(all_regressions)} unexpected regression(s)."
        ),
    }


def write_json_report(steps: list[StepResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(steps_to_json_payload(steps), indent=2) + "\n",
        encoding="utf-8",
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Incremental skill-library regression eval")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown report path",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help="JSON report path (for admin API)",
    )
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / "backend" / "adk_app" / ".env")

    print("Running incremental regression eval (4 steps, LLM calls required)...")
    steps = await run_regression()
    report = format_report(steps)
    print(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport written to {args.output}")

    write_json_report(steps, args.json_output)
    print(f"JSON report written to {args.json_output}")

    total_regressions = sum(len(s.regressions) for s in steps)
    return 1 if total_regressions else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
