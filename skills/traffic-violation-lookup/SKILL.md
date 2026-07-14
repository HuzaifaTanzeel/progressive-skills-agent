---
name: traffic-violation-lookup
description: |
  Look up one traffic violation code (fine, early-payment discount). Use for a single code meaning or early-pay amount. Do NOT use for totals owed, combined fees, or iqama costs — use government-fee-payment-draft.
version: 1.1.0
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
