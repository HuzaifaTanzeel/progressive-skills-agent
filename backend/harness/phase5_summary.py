"""Aggregate latest Phase 5 ADK eval history into a JSON summary for the admin API.

For each (eval_set_id, eval_id), keeps the case with the highest creation
timestamp so partial re-runs do not wipe earlier full-suite results.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
EVALS_DIR = REPO_ROOT / "evals"
MANIFEST_PATH = EVALS_DIR / "eval_config.json"
EVAL_HISTORY_DIR = BACKEND_DIR / "adk_app" / ".adk" / "eval_history"
DEFAULT_JSON_OUTPUT = EVALS_DIR / "results" / "phase5_eval_summary.json"

# Compliance tiers from AGENTS.md skill catalog.
SKILL_TIERS: dict[str, str] = {
    "iqama-renewal-status": "read-only",
    "traffic-violation-lookup": "read-only",
    "government-fee-payment-draft": "draft-only",
    "appointment-slot-finder": "read-only",
}

SKILL_ORDER = [
    "iqama-renewal-status",
    "traffic-violation-lookup",
    "government-fee-payment-draft",
    "appointment-slot-finder",
]

# ADK EvalStatus.PASSED == 1
_PASSED = 1


def _status_label(code: int | None) -> str:
    if code == _PASSED:
        return "PASS"
    if code is None:
        return "UNKNOWN"
    return "FAIL"


def _load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _trajectory_mode(manifest: dict, skill_id: str) -> str | None:
    criteria = (
        manifest.get("skill_configs", {})
        .get(skill_id, {})
        .get("criteria", {})
    )
    traj = criteria.get("tool_trajectory_avg_score")
    if not traj:
        return None
    return traj.get("match_type")


def _collect_latest_cases(
    history_dir: Path,
) -> dict[tuple[str, str], dict]:
    """Map (eval_set_id, eval_id) -> best case record with metadata."""
    best: dict[tuple[str, str], dict] = {}
    if not history_dir.is_dir():
        return best

    for path in history_dir.glob("*.evalset_result.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        file_ts = float(data.get("creation_timestamp") or path.stat().st_mtime)
        for case in data.get("eval_case_results") or []:
            set_id = case.get("eval_set_id") or data.get("eval_set_id")
            eval_id = case.get("eval_id")
            if not set_id or not eval_id:
                continue
            key = (set_id, eval_id)
            case_ts = float(
                case.get("creation_timestamp")
                or data.get("creation_timestamp")
                or file_ts
            )
            prev = best.get(key)
            if prev is None or case_ts >= prev["_ts"]:
                metrics = []
                for m in case.get("overall_eval_metric_results") or []:
                    metrics.append({
                        "metric_name": m.get("metric_name"),
                        "score": m.get("score"),
                        "threshold": m.get("threshold"),
                        "eval_status": _status_label(m.get("eval_status")),
                        "match_type": (m.get("criterion") or {}).get("match_type"),
                    })
                best[key] = {
                    "_ts": case_ts,
                    "eval_set_id": set_id,
                    "eval_id": eval_id,
                    "final_eval_status": case.get("final_eval_status"),
                    "status": _status_label(case.get("final_eval_status")),
                    "metrics": metrics,
                    "source_file": path.name,
                }
    return best


def build_summary(
    history_dir: Path | None = None,
    manifest: dict | None = None,
) -> dict:
    history_dir = history_dir or EVAL_HISTORY_DIR
    manifest = manifest or _load_manifest()
    latest = _collect_latest_cases(history_dir)

    skills = []
    for skill_id in SKILL_ORDER:
        cases = [
            {
                "eval_id": v["eval_id"],
                "status": v["status"],
                "metrics": v["metrics"],
                "source_file": v["source_file"],
            }
            for (set_id, _), v in sorted(latest.items())
            if set_id == skill_id
        ]
        passed = sum(1 for c in cases if c["status"] == "PASS")
        total = len(cases)
        accuracy = (passed / total) if total else 0.0
        last_result = "PASS" if total and passed == total else (
            "FAIL" if total else "UNKNOWN"
        )
        skills.append({
            "skill_id": skill_id,
            "tier": SKILL_TIERS.get(skill_id, "unknown"),
            "trajectory_mode": _trajectory_mode(manifest, skill_id),
            "accuracy": round(accuracy, 4),
            "passed": passed,
            "total": total,
            "last_result": last_result,
            "cases": cases,
        })

    adversarial = []
    for case_def in manifest.get("adversarial_routing_cases") or []:
        set_id = case_def["eval_set_id"]
        eval_id = case_def["eval_id"]
        result = latest.get((set_id, eval_id))
        adversarial.append({
            **case_def,
            "last_result": result["status"] if result else "UNKNOWN",
            "source_file": result["source_file"] if result else None,
        })

    return {
        "run_date": date.today().isoformat(),
        "skills": skills,
        "adversarial": adversarial,
        "history_dir": str(history_dir),
        "case_count": len(latest),
    }


def write_summary(path: Path | None = None, history_dir: Path | None = None) -> dict:
    path = path or DEFAULT_JSON_OUTPUT
    summary = build_summary(history_dir=history_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Phase 5 eval summary JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help="JSON output path",
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=EVAL_HISTORY_DIR,
        help="ADK eval_history directory",
    )
    args = parser.parse_args()

    summary = write_summary(path=args.output, history_dir=args.history_dir)
    print(f"Wrote {args.output} ({summary['case_count']} unique cases)")
    for skill in summary["skills"]:
        print(
            f"  {skill['skill_id']}: {skill['passed']}/{skill['total']} "
            f"({skill['last_result']}) mode={skill['trajectory_mode']}"
        )


if __name__ == "__main__":
    main()
