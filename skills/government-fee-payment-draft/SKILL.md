---
name: government-fee-payment-draft
description: |
  Draft how-much-I-owe totals (iqama, dependents, traffic+iqama). Draft-only; never submits. Not for single-code lookup or renewal docs.
version: 1.1.1
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
   - `dependents` from the user as an integer (use `2` only as the demo
     default for combined owe/totals that omit a dependent count)
   - `violation_codes` only when step 2 applies (e.g. `"101,205"`)
   - Leave `include_express` false / omit it unless the user explicitly asks
     for express processing. Combined owe/totals must **not** add the 100 SAR
     express add-on (demo default subtotal is 2,475 SAR without express).
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
- Answering single-code violation lookups without the fee draft tools when
  only one code is asked (route to traffic-violation-lookup).
- Setting `include_express=true` unless the user asked for express.
- Omitting draft-only disclaimer.