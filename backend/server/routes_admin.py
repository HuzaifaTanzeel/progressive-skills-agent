"""Admin API routes for eval / harness report summaries."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "evals" / "results"

PHASE5_JSON = RESULTS_DIR / "phase5_eval_summary.json"
REGRESSION_JSON = RESULTS_DIR / "regression_eval_report.json"
TOKEN_BUDGET_JSON = RESULTS_DIR / "token_budget_report.json"

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail=(
                f"Missing report file: {path.name}. "
                "Generate with: python -m harness.phase5_summary | "
                "python -m harness.regression_eval | "
                "python -m harness.token_budget_report"
            ),
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Invalid JSON in {path.name}: {exc}",
        ) from exc


@router.get("/eval-summary")
async def eval_summary() -> dict:
    """Latest Phase 5 eval summary + Phase 6 regression/token-budget reports."""
    phase5 = _read_json(PHASE5_JSON)
    regression = _read_json(REGRESSION_JSON)
    token_budget = _read_json(TOKEN_BUDGET_JSON)

    return {
        "skills": phase5.get("skills", []),
        "adversarial": phase5.get("adversarial", []),
        "token_budget": token_budget,
        "regression": regression,
        "sources": {
            "phase5": str(PHASE5_JSON),
            "regression": str(REGRESSION_JSON),
            "token_budget": str(TOKEN_BUDGET_JSON),
            "phase5_run_date": phase5.get("run_date"),
            "regression_run_date": regression.get("run_date"),
            "token_budget_run_date": token_budget.get("run_date"),
        },
    }
