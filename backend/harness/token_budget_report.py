"""Token budget comparison: progressive disclosure vs monolithic prompt baseline."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset
from tabulate import tabulate

from adk_app.code_executor import demo_code_executor
from harness.eval_helpers import REPO_SKILLS_DIR
from harness.token_helpers import (
    count_tokens,
    get_encoding,
    l1_index_xml,
    load_all_reference_text,
    skill_md_body,
    skill_system_instruction_text,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "evals" / "results" / "token_budget_report.md"
DEFAULT_JSON_OUTPUT = REPO_ROOT / "evals" / "results" / "token_budget_report.json"


def compute_metrics() -> dict[str, int | float | str]:
    skill_dirs = sorted(d for d in REPO_SKILLS_DIR.iterdir() if d.is_dir())
    skills = [load_skill_from_dir(d) for d in skill_dirs]
    toolset = skill_toolset.SkillToolset(
        skills=skills,
        code_executor=demo_code_executor,
    )

    enc = get_encoding()
    l1_xml = l1_index_xml(toolset)
    l1_tokens = count_tokens(l1_xml, enc)

    body_tokens_by_skill: dict[str, int] = {}
    ref_tokens_by_skill: dict[str, int] = {}
    for skill_dir in skill_dirs:
        body = skill_md_body(skill_dir / "SKILL.md")
        refs = load_all_reference_text(skill_dir)
        body_tokens_by_skill[skill_dir.name] = count_tokens(body, enc)
        ref_tokens_by_skill[skill_dir.name] = count_tokens(refs, enc)

    largest_skill = max(body_tokens_by_skill, key=body_tokens_by_skill.get)
    largest_l2 = body_tokens_by_skill[largest_skill]

    monolithic = sum(body_tokens_by_skill.values()) + sum(ref_tokens_by_skill.values())
    progressive = l1_tokens + largest_l2
    reduction_pct = ((monolithic - progressive) / monolithic * 100) if monolithic else 0.0

    sys_instr = count_tokens(skill_system_instruction_text(), enc)

    return {
        "l1_index": l1_tokens,
        "largest_l2_skill": largest_skill,
        "largest_l2": largest_l2,
        "monolithic": monolithic,
        "progressive": progressive,
        "reduction_pct": reduction_pct,
        "system_instruction": sys_instr,
        "body_by_skill": body_tokens_by_skill,
        "ref_by_skill": ref_tokens_by_skill,
    }


def format_report(metrics: dict) -> str:
    rows = [
        ["L1 index (always-on system catalog, all 4 skills)", metrics["l1_index"]],
        [
            f"Largest L2 body ({metrics['largest_l2_skill']})",
            metrics["largest_l2"],
        ],
        [
            "Typical progressive turn (L1 + largest L2)",
            metrics["progressive"],
        ],
        [
            "Monolithic baseline (all L2 bodies + all references)",
            metrics["monolithic"],
        ],
        [
            "Token reduction (monolithic -> progressive)",
            f"{metrics['reduction_pct']:.1f}%",
        ],
        [
            "Compact skill protocol (always injected with L1 catalog)",
            metrics["system_instruction"],
        ],
    ]

    table = tabulate(rows, headers=["Metric", "Tokens (cl100k_base)"], tablefmt="github")

    per_skill_rows = []
    for skill in sorted(metrics["body_by_skill"]):
        per_skill_rows.append([
            skill,
            metrics["body_by_skill"][skill],
            metrics["ref_by_skill"][skill],
            metrics["body_by_skill"][skill] + metrics["ref_by_skill"][skill],
        ])
    per_skill_table = tabulate(
        per_skill_rows,
        headers=["Skill", "L2 body", "References", "Combined"],
        tablefmt="github",
    )

    return "\n".join([
        "# Token Budget Report (Progressive Disclosure vs Monolithic)",
        "",
        f"Run date: {date.today().isoformat()}.",
        "Encoding: tiktoken `cl100k_base` (OpenAI-compatible).",
        "",
        "L1 index measured via ADK `format_skills_as_xml` — the always-on "
        "system-prompt catalog (progressive disclosure L1; not a list_skills "
        "tool response).",
        "",
        "## Comparison",
        "",
        table,
        "",
        "## Per-skill breakdown",
        "",
        per_skill_table,
        "",
        "## Note on scale",
        "",
        "At only **4 skills**, token savings look modest compared to the Agent Skills "
        "whitepaper's ~50-skill Figure 8 example (~90%+ reduction). That is expected: "
        "progressive disclosure savings scale with library size. This demo proves the "
        "mechanism with real numbers at small scale, not the magnitude of a production "
        "catalog.",
        "",
    ])


def metrics_to_json_payload(metrics: dict) -> dict:
    """Serialize metrics for the admin API (JSON-safe)."""
    return {
        "run_date": date.today().isoformat(),
        "encoding": "cl100k_base",
        "comparison": {
            "l1_index": metrics["l1_index"],
            "largest_l2_skill": metrics["largest_l2_skill"],
            "largest_l2": metrics["largest_l2"],
            "progressive": metrics["progressive"],
            "monolithic": metrics["monolithic"],
            "reduction_pct": round(float(metrics["reduction_pct"]), 1),
            "system_instruction": metrics["system_instruction"],
        },
        "body_by_skill": metrics["body_by_skill"],
        "ref_by_skill": metrics["ref_by_skill"],
        "per_skill": {
            skill: {
                "l2_body": metrics["body_by_skill"][skill],
                "references": metrics["ref_by_skill"][skill],
                "combined": (
                    metrics["body_by_skill"][skill] + metrics["ref_by_skill"][skill]
                ),
            }
            for skill in sorted(metrics["body_by_skill"])
        },
    }


def write_json_report(metrics: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metrics_to_json_payload(metrics), indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Token budget comparison report")
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

    metrics = compute_metrics()
    report = format_report(metrics)
    print(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Report written to {args.output}")

    write_json_report(metrics, args.json_output)
    print(f"JSON report written to {args.json_output}")


if __name__ == "__main__":
    main()
