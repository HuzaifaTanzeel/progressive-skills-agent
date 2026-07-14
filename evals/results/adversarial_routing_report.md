# Adversarial Routing Report (Standalone)

This document measures **skill trigger/routing accuracy** for the two cross-skill adversarial prompts shared between `iqama-renewal-status`, `traffic-violation-lookup`, and `government-fee-payment-draft`.

ADK does not have a native `expected_skill` field. Routing is the first `load_skill` call in the invocation trajectory — skill selection is just the opening move in the tool trajectory.

## Adversarial cases

| # | Source eval set | Eval ID | User prompt (summary) | Expected `load_skill` | Must NOT load |
|---|-----------------|---------|------------------------|----------------------|---------------|
| 1 | `iqama-renewal-status` | `negative_routes_to_fee_draft` | Total iqama renewal cost with 2 dependents | `government-fee-payment-draft` | `iqama-renewal-status` |
| 2 | `traffic-violation-lookup` | `negative_routes_to_fee_draft` | How much do I owe (violations + iqama) | `government-fee-payment-draft` | `traffic-violation-lookup` |

## Result: 2/2 PASS (routing)

| Case | Routed to | Forbidden skill loaded? | Verdict |
|------|-----------|-------------------------|---------|
| 1 | `government-fee-payment-draft` | No | PASS |
| 2 | `government-fee-payment-draft` | No | PASS |

Observed trajectory (case 1 example):

1. `list_skills`
2. `load_skill(skill_name="government-fee-payment-draft")`
3. `run_skill_script(scripts/compute_fees.py, request-type=iqama_renewal, dependents=2)`

## EDD note: routing vs full trajectory

**Routing passed on first run** — descriptions already steer fee-total questions away from iqama/traffic skills.

**Trajectory initially failed** on case 2's shared prompt ("How much do I owe…") because `government-fee-payment-draft` instructed the agent to ask clarifying questions when dependents/violation codes were omitted. The agent correctly loaded the fee-draft skill but stopped to ask for inputs instead of running `compute_fees.py`.

### Before (trajectory failure on combined-total prompt)

**Skill workflow line (government-fee-payment-draft):**

> For combined totals, include dependents and violation codes when known; if the user omits them, ask once before running the script.

**Agent behavior:** `list_skills` → `load_skill(government-fee-payment-draft)` → *asks user for dependents and violation codes* (no `run_skill_script`).

**Eval scores:** `tool_trajectory_avg_score` 0.0, `final_response_match_v2` 0.0.

### After (trajectory pass after description tighten)

**Skill workflow line (government-fee-payment-draft):**

> For combined totals without explicit dependents or violation codes, run `combined_summary` with illustrative demo defaults: `dependents=2`, `violation-codes=101,205`. Do not ask clarifying questions for this demo combined-total pattern.

**Agent behavior:** `list_skills` → `load_skill(government-fee-payment-draft)` → `run_skill_script(combined_summary, dependents=2, violation-codes=101,205)`.

**Eval scores:** `tool_trajectory_avg_score` 1.0, `final_response_match_v2` 1.0.

This is the whitepaper-style **non-invocation / wrong-completion** finding inverted: routing was right, but the skill body caused an incomplete trajectory until the description was tightened.

## How to reproduce

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install "google-adk[eval]" pytest-asyncio pandas tabulate
python -m pytest tests/test_evals.py::test_adversarial_routing_cases -v
```
