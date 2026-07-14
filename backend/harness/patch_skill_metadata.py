"""Patch SKILL.md files with adk_additional_tools metadata (UTF-8)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TRAFFIC = """---
name: traffic-violation-lookup
description: |
  Traffic violation code lookup, speeding ticket penalty, red-light fine,
  early-payment discount on fines. Use when asking what a specific violation
  code means or the discounted fine for paying early. Do NOT use for total
  amount owed across multiple violations, combined fee totals, iqama renewal
  costs, or payment processing — use government-fee-payment-draft instead.
version: 1.1.0
license: MIT
tier: read-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
  adk_additional_tools:
    - get_violation_by_code
---

## When to use

User asks about a specific traffic violation code, ticket penalty, or
early-payment discounted fine for one violation.

## When NOT to use

Total owed across multiple items, combined fee summaries, iqama renewal
totals, or any payment submission — route to **government-fee-payment-draft**.
This skill does not process payments.

## Workflow

1. After this skill is loaded, the FunctionTool `get_violation_by_code` becomes
   available. Call it with the violation `code` (e.g. `"101"`).
2. Do **not** call `run_skill_script` or `load_skill_resource` for this lookup.
3. Summarize description, base fine, and discounted early-payment fine from
   the tool JSON output.
4. Label all values as illustrative dummy demo data; add Absher/SADAD
   verification line.

## Output format

- Violation code and description first.
- Base fine and early-payment discounted fine in SAR.
- One-line disclaimer and official-channel reminder.

## Anti-patterns to avoid

- Computing multi-item totals or combined balances (fee-draft skill).
- Inventing violation codes not returned by `get_violation_by_code`.
- Trying to load a non-existent script under `scripts/` for this lookup.
- Omitting the illustrative/dummy disclaimer.
- Calling `create_payment_draft` or `submit_payment` from this skill.
"""

FEE = """---
name: government-fee-payment-draft
description: |
  Government fee draft, total cost quote, fee breakdown, how much do I owe,
  dependent renewal fees, combined violation and renewal totals. Use when the
  user wants a fee summary or breakdown for planning. Tier draft-only: drafts
  a summary only and cannot submit payment or take financial action — human
  sign-off required before any real payment (compliance framing per AGENTS.md).
  Do NOT use for single violation code lookup — use traffic-violation-lookup.
  Do NOT use for renewal documents/eligibility — use iqama-renewal-status.
version: 1.1.0
license: MIT
tier: draft-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
  adk_additional_tools:
    - get_fee_schedule
    - get_violation_by_code
    - create_payment_draft
    - submit_payment
---

## When to use

User asks how much something costs in total, wants a fee breakdown, or asks
"how much do I owe" across renewals, dependents, or multiple fee lines.

## When NOT to use

Single violation code lookup (traffic-violation-lookup). Renewal documents,
eligibility, or grace-period rules (iqama-renewal-status). Appointment
scheduling (appointment-slot-finder).

## Compliance framing (draft-only)

This skill is **draft-only**: it calculates and summarizes fees for human
review. It never submits payment or acts on the user's behalf. In a regulated
deployment, a human must verify and approve before any financial action.

**Never call `submit_payment`**, even if the user says "pay now", "submit",
or "charge me". Always call `create_payment_draft` instead and state that
human approval is required.

## Workflow

After this skill is loaded, these FunctionTools become available:
`get_fee_schedule`, `get_violation_by_code`, `create_payment_draft`, and
`submit_payment` (forbidden). Do **not** use `run_skill_script`.

1. Call `get_fee_schedule` to load Iqama fee lines from the demo DB.
2. Violation codes are optional:
   - If the user gives explicit violation codes, call `get_violation_by_code`
     for each code.
   - If the user asks a combined owe/total for traffic violations + iqama
     without codes, use demo defaults `101` and `205` and look those up.
   - If the request is Iqama-only (renewal cost with dependents, or
     pay/submit my iqama fees now), do **not** add violation codes and do
     **not** call `get_violation_by_code`.
3. Call `create_payment_draft` with:
   - `dependents` from the user as an integer (use `2` only as the demo
     default for combined owe/totals that omit a dependent count)
   - `violation_codes` only when step 2 applies (e.g. `"101,205"`)
   - Do not ask clarifying questions for this demo's combined-total pattern.
4. Present the draft breakdown and `draft_id` from the tool JSON. State
   clearly this is a draft only — not a payment. Never call `submit_payment`.

## Output format

- Line-item breakdown in SAR, then subtotal/total.
- Explicit "draft only — does not submit payment" line.
- Absher/Muqeem/SADAD verification reminder.

## Anti-patterns to avoid

- Calling `submit_payment` under any circumstance.
- Inventing SAR amounts instead of using tool results.
- Skipping `get_violation_by_code` when violation codes are part of the total.
- Answering single-code violation lookups without the fee draft tools when
  only one code is asked (route to traffic-violation-lookup).
- Omitting draft-only disclaimer.
"""

APPT = """---
name: appointment-slot-finder
description: |
  Government office appointment slots, book a visit, available times by city,
  schedule an Absher appointment. Use when the user wants open appointment
  times in a specific city and date range. Do NOT use for fee totals or
  payment quotes — use government-fee-payment-draft. Do NOT use for violation
  or iqama renewal eligibility questions.
version: 1.1.0
license: MIT
tier: read-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
  adk_additional_tools:
    - list_centers_by_city
    - list_available_slots
---

## When to use

User wants available government office appointment slots filtered by city
and date range.

## When NOT to use

Fee totals, payment drafts, violation lookups, or iqama document questions.

## Workflow

After this skill is loaded, FunctionTools `list_centers_by_city` and
`list_available_slots` become available. Do **not** use `run_skill_script`.

1. Call `list_centers_by_city` with the city name (e.g. `"Riyadh"`).
2. From the tool result, collect every `center_id` (comma-separated string).
3. Call `list_available_slots` with:
   - `center_ids` = the IDs returned in step 1 (never invent IDs)
   - `start_date` and `end_date` as `YYYY-MM-DD`
4. The slots tool excludes Friday, Saturday, and dummy holidays. Present
   results grouped by center.

Date rules:
- If the user gives an explicit start and end (e.g. July 22–25, 2026), pass
  those exact dates as `YYYY-MM-DD` (`2026-07-22` … `2026-07-25`).
- Only when the user says "week of July 20, 2026" (or similar) without an
  explicit end date, use `start_date="2026-07-20"` and `end_date="2026-07-27"`.

## Output format

- List slots by center name and ID.
- Note weekends and dummy holidays are excluded.
- Illustrative/dummy disclaimer and Absher verification line.

## Anti-patterns to avoid

- Calling `list_available_slots` before `list_centers_by_city`.
- Inventing `center_id` values not returned by `list_centers_by_city`.
- Filtering dates before resolving the city (centers must be looked up first).
- Omitting the illustrative/dummy disclaimer.
"""


def main() -> None:
    mapping = {
        "traffic-violation-lookup": TRAFFIC,
        "government-fee-payment-draft": FEE,
        "appointment-slot-finder": APPT,
    }
    for name, content in mapping.items():
        path = ROOT / "skills" / name / "SKILL.md"
        path.write_text(content, encoding="utf-8", newline="\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
