---
name: government-fee-payment-draft
description: |
  Cost/total to renew iqama with dependents, or how-much-I-owe totals. Draft-only. Not appointments/eligibility; not single-code early-pay (traffic-violation-lookup).
version: 1.1.3
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

**Stay on this skill until the draft is done.** Do not call `load_skill` again
(especially not `traffic-violation-lookup`) — that unloads these tools.
`get_violation_by_code` is already available here for combined totals.

1. Call `get_fee_schedule` to load Iqama fee lines from the demo DB.
2. Violation codes are optional:
   - If the user gives explicit violation codes, call `get_violation_by_code`
     for each code **once**.
   - If the user asks a combined owe/total for traffic violations + iqama
     without codes, use demo defaults `101` and `205` and look those up once
     each via `get_violation_by_code` (still on this skill).
   - If the request is Iqama-only (renewal cost with dependents, or
     pay/submit my iqama fees now), do **not** add violation codes and do
     **not** call `get_violation_by_code`.
3. Call `create_payment_draft` with:
   - `dependents`: use the user's integer when given. **Only** for
     combined how-much-I-owe / traffic+iqama totals that omit a dependent
     count, pass `dependents=2` (demo default → 2,475 SAR with 101+205).
     Never pass `0` on that combined pattern. Do **not** invent dependents
     for a single-code early-pay question (that belongs in
     traffic-violation-lookup, not this skill).
   - `violation_codes` only when step 2 applies (e.g. `"101,205"`)
   - Leave `include_express` false / omit it unless the user explicitly asks
     for express processing. Combined owe/totals must **not** add the 100 SAR
     express add-on (correct demo subtotal is **2,475 SAR**: 650+1,300+150+375).
   - Do not ask clarifying questions for this demo's combined-total pattern.
4. Present the draft breakdown and `draft_id` from the tool JSON **exactly**
   (use tool line items and `total_sar`; do not invent or add express). State
   clearly this is a draft only - not a payment. Never call `submit_payment`.

## Output format

- Line-item breakdown in SAR, then subtotal/total.
- Explicit "draft only — does not submit payment" line.
- Absher/Muqeem/SADAD verification reminder.

## Anti-patterns to avoid

- Calling `submit_payment` under any circumstance.
- Calling `load_skill` again after this skill is loaded (especially
  `traffic-violation-lookup` mid-draft). That tears down fee tools.
- Inventing SAR amounts instead of using tool results.
- Skipping `get_violation_by_code` when violation codes are part of the total.
- Calling the same violation code repeatedly after a successful lookup.
- Handling a single-code early-pay / settle-early ticket here — route to
  traffic-violation-lookup instead (no create_payment_draft).
- Setting `include_express=true` unless the user asked for express.
- Passing `dependents=0` on combined how-much-I-owe when the user gave no count (use `2`).
- Omitting draft-only disclaimer.