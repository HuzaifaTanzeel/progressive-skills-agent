"""Domain FunctionTools backed by the in-memory DemoDB.

These are the agent's "hands". Skills (SKILL.md) are the runbooks that say
which tools to call, in what order, and which tools must never be called.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .demo_db import (
    DemoDB,
    discounted_fine_sar,
    filter_slots_for_centers,
    new_draft_id,
    parse_center_ids,
    parse_violation_codes,
    seed_demo_db,
)


def build_demo_tools(db: DemoDB | None = None) -> list:
    """Return plain callables for SkillToolset(additional_tools=...).

    ADK wraps Python callables as FunctionTools automatically.
    """
    store = db or seed_demo_db()

    def get_violation_by_code(code: str) -> dict[str, Any]:
        """Look up a traffic violation code and compute the early-payment fine.

        Args:
            code: Violation code string, e.g. "101".

        Returns:
            Violation details including base and discounted fine in SAR, or an
            error if the code is unknown in the demo DB.
        """
        for violation in store.violations:
            if violation["code"] == code:
                base = violation["base_fine_sar"]
                discount_pct = violation["early_payment_discount_pct"]
                return {
                    "code": violation["code"],
                    "description": violation["description"],
                    "base_fine_sar": base,
                    "early_payment_discount_pct": discount_pct,
                    "discounted_fine_sar": discounted_fine_sar(base, discount_pct),
                    "early_payment_window_days": store.early_payment_window_days,
                    "demo_data": True,
                }
        return {
            "error": f"Violation code '{code}' not found in dummy data.",
            "demo_data": True,
        }

    def get_fee_schedule() -> dict[str, Any]:
        """Return the dummy government fee schedule for Iqama renewal lines.

        Returns:
            Fee schedule amounts in SAR for primary, dependent, and optional
            express add-on lines.
        """
        return {
            "fees_sar": dict(store.fee_schedule),
            "demo_data": True,
            "draft_only_note": (
                "Amounts are for draft summaries only; never submit payment "
                "from this tool."
            ),
        }

    def list_centers_by_city(city: str) -> dict[str, Any]:
        """Resolve a city name to government service center IDs and names.

        Args:
            city: City name, e.g. "Riyadh", "Jeddah", or "Dammam".

        Returns:
            Matching centers with center_id and name. Pass those center_ids to
            list_available_slots. Empty centers list if city is unknown.
        """
        centers = store.cities.get(city, [])
        return {
            "city": city,
            "centers": [
                {"center_id": c["center_id"], "name": c["name"]} for c in centers
            ],
            "demo_data": True,
        }

    def list_available_slots(
        center_ids: str | list[str],
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """List available appointment slots for known center IDs in a date range.

        Call list_centers_by_city first and pass the returned center_id values.
        Do not invent center IDs. Excludes Fridays, Saturdays, and dummy holidays.

        Args:
            center_ids: Comma-separated center IDs from list_centers_by_city,
                e.g. "RYD-01,RYD-02", or a list of ID strings.
            start_date: Inclusive start date as YYYY-MM-DD.
            end_date: Inclusive end date as YYYY-MM-DD.

        Returns:
            Filtered slots grouped by center, or an error for bad dates.
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as exc:
            return {"error": f"Invalid date: {exc}", "demo_data": True}

        ids = parse_center_ids(center_ids)
        if not ids:
            return {
                "error": "center_ids is required; call list_centers_by_city first.",
                "demo_data": True,
            }

        filtered = filter_slots_for_centers(store, ids, start, end)
        return {
            "center_ids": ids,
            "start_date": start_date,
            "end_date": end_date,
            "centers": filtered,
            "demo_data": True,
        }

    def create_payment_draft(
        dependents: int = 0,
        violation_codes: str = "",
        include_express: bool = False,
    ) -> dict[str, Any]:
        """Create a draft-only fee breakdown using demo fee and violation tables.

        Never submits payment. Returns a draft_id for human review. Call
        get_fee_schedule first, and call get_violation_by_code for each
        violation code before creating a combined draft.

        Args:
            dependents: Number of dependent renewals as an integer
                (0, 1, 2, ...). Pass a number, not a string. Only for
                combined how-much-I-owe / traffic+iqama drafts when the user
                omits a dependent count, pass 2 (demo default). Do not use
                this tool for a single-code early-pay lookup.
            violation_codes: Comma-separated violation codes for early-payment
                fines, e.g. "101,205". Empty string for Iqama-only drafts.
            include_express: Include the optional 100 SAR express add-on.
                Default False. Set True only if the user explicitly asks for
                express processing; leave False for how-much-I-owe / combined
                totals (demo combined total is 2475 SAR without express).

        Returns:
            Draft breakdown with line items, totals, draft_id, and draft_only=True.
        """
        lines: list[dict[str, Any]] = []
        schedule = store.fee_schedule
        # LLM tool args may arrive as str; normalize for business logic.
        dependent_count = max(0, int(dependents))

        lines.append(
            {
                "item": "Primary Iqama renewal",
                "amount_sar": schedule["iqama_renewal_primary"],
            }
        )
        for i in range(1, dependent_count + 1):
            lines.append(
                {
                    "item": f"Dependent {i} renewal",
                    "amount_sar": schedule["iqama_renewal_dependent"],
                }
            )

        codes = parse_violation_codes(violation_codes)
        for code in codes:
            match = next((v for v in store.violations if v["code"] == code), None)
            if match is None:
                return {
                    "error": f"Violation code '{code}' not found in dummy data.",
                    "demo_data": True,
                }
            discounted = discounted_fine_sar(
                match["base_fine_sar"],
                match["early_payment_discount_pct"],
            )
            lines.append(
                {
                    "item": f"Traffic violation {code} (early payment)",
                    "amount_sar": discounted,
                }
            )

        if include_express:
            lines.append(
                {
                    "item": "Optional express processing (dummy add-on)",
                    "amount_sar": schedule["express_processing_addon"],
                }
            )

        total = sum(line["amount_sar"] for line in lines)
        draft_id = new_draft_id()
        draft = {
            "draft_id": draft_id,
            "request_type": (
                "combined_summary" if codes else "iqama_renewal"
            ),
            "dependents": dependent_count,
            "violation_codes": codes,
            "lines": lines,
            "total_sar": total,
            "draft_only": True,
            "submitted": False,
            "demo_data": True,
            "message": (
                "Draft only — does not submit payment. Human sign-off required "
                "before any real payment."
            ),
        }
        store.payment_drafts[draft_id] = draft
        return draft

    def submit_payment(draft_id: str) -> dict[str, Any]:
        """Attempt to submit a payment draft.

        This tool exists so draft-only compliance can be evaluated. The
        government-fee-payment-draft skill forbids calling it. Prefer
        create_payment_draft and tell the user a human must approve payment.

        Args:
            draft_id: ID returned by create_payment_draft.

        Returns:
            Always a blocked/demo response; never a successful payment.
        """
        draft = store.payment_drafts.get(draft_id)
        result = {
            "draft_id": draft_id,
            "submitted": False,
            "blocked": True,
            "demo_data": True,
            "error": (
                "submit_payment is blocked in this demo. The fee skill is "
                "draft-only; a human must approve before any real payment."
            ),
        }
        if draft is None:
            result["error"] = (
                f"Unknown draft_id '{draft_id}'. create_payment_draft first, "
                "then remember this demo never submits payment."
            )
        store.payments[draft_id] = result
        return result

    return [
        get_violation_by_code,
        get_fee_schedule,
        list_centers_by_city,
        list_available_slots,
        create_payment_draft,
        submit_payment,
    ]


# Module-level singleton for the running agent process.
DEMO_DB = seed_demo_db()
DEMO_TOOLS = build_demo_tools(DEMO_DB)
