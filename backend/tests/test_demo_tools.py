"""Unit tests for in-memory demo DB and FunctionTools (no LLM / API key)."""

from __future__ import annotations

from adk_app.demo_db import discounted_fine_sar, seed_demo_db
from adk_app.demo_tools import build_demo_tools


def _tools():
    return {t.__name__: t for t in build_demo_tools(seed_demo_db())}


def test_seed_contains_core_rows() -> None:
    db = seed_demo_db()
    assert {v["code"] for v in db.violations} == {"101", "205", "310"}
    assert db.fee_schedule["iqama_renewal_primary"] == 650
    assert "Riyadh" in db.cities
    assert db.renewal_policy["grace_period_days"] == 30
    assert db.payment_drafts == {}


def test_get_violation_by_code_computes_discount() -> None:
    tools = _tools()
    result = tools["get_violation_by_code"]("101")
    assert result["base_fine_sar"] == 300
    assert result["discounted_fine_sar"] == discounted_fine_sar(300, 50)
    assert result["discounted_fine_sar"] == 150


def test_get_violation_unknown_code() -> None:
    tools = _tools()
    result = tools["get_violation_by_code"]("999")
    assert "error" in result


def test_centers_then_slots_chain() -> None:
    tools = _tools()
    centers = tools["list_centers_by_city"]("Riyadh")
    ids = [c["center_id"] for c in centers["centers"]]
    assert ids == ["RYD-01", "RYD-02"]

    slots = tools["list_available_slots"](
        ",".join(ids), "2026-07-20", "2026-07-27"
    )
    assert "error" not in slots
    # Friday 2026-07-24 must be excluded from RYD-01
    ryd01 = next(c for c in slots["centers"] if c["center_id"] == "RYD-01")
    assert all(s["date"] != "2026-07-24" for s in ryd01["slots"])


def test_slots_without_centers_errors() -> None:
    tools = _tools()
    result = tools["list_available_slots"]("", "2026-07-20", "2026-07-27")
    assert "error" in result


def test_fee_schedule_and_iqama_draft() -> None:
    tools = _tools()
    schedule = tools["get_fee_schedule"]()
    assert schedule["fees_sar"]["iqama_renewal_dependent"] == 650

    draft = tools["create_payment_draft"](dependents="2")
    assert draft["draft_only"] is True
    assert draft["submitted"] is False
    assert draft["total_sar"] == 1950
    assert draft["draft_id"].startswith("DRAFT-")


def test_combined_draft_uses_violation_discounts() -> None:
    tools = _tools()
    draft = tools["create_payment_draft"](
        dependents=2, violation_codes="101,205"
    )
    assert draft["total_sar"] == 2475
    assert draft["violation_codes"] == ["101", "205"]


def test_submit_payment_is_always_blocked() -> None:
    tools = _tools()
    draft = tools["create_payment_draft"](dependents=1)
    result = tools["submit_payment"](draft["draft_id"])
    assert result["submitted"] is False
    assert result["blocked"] is True
