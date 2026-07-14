---
name: traffic-violation-lookup
description: |
  Look up one traffic violation code (fine or early-pay/settle-early). Use for a single coded ticket. Not for how-much-I-owe totals or iqama fees — use government-fee-payment-draft.
version: 1.1.2
license: MIT
tier: read-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
  adk_additional_tools:
    - get_violation_by_code
---

## Workflow

1. After this skill is loaded, the FunctionTool `get_violation_by_code` becomes
   available. Call it with the violation `code` (e.g. `"101"`).
2. Do **not** call `run_skill_script` or `load_skill_resource` for this lookup.
3. Do **not** call `load_skill` for government-fee-payment-draft and do **not**
   call `create_payment_draft` — a single-code early-pay question is answered
   with `get_violation_by_code` alone.
4. Summarize description, base fine, and discounted early-payment fine from
   the tool JSON output.
5. Label all values as illustrative dummy demo data; add Absher/SADAD
   verification line.

## Output format

- Violation code and description first.
- Base fine and early-payment discounted fine in SAR.
- One-line disclaimer and official-channel reminder.

## Anti-patterns to avoid

- Routing a single coded ticket / settle-early question to
  `government-fee-payment-draft`.
- Computing multi-item totals or combined balances (fee-draft skill).
- Inventing violation codes not returned by `get_violation_by_code`.
- Trying to load a non-existent script under `scripts/` for this lookup.
- Omitting the illustrative/dummy disclaimer.
- Calling `create_payment_draft` or `submit_payment` from this skill.
