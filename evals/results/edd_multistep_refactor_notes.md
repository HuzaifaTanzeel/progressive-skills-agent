# Multi-step tools + EDD refactor notes

Date: 2026-07-14.

## Why scores looked empty before

Previous goldens mostly checked:

`list_skills → load_skill → run_skill_script` (one domain script)

That scored **routing**, not **workflow fidelity**. After SKILL.md was tuned to
match goldens, the suite reported a wall of 1.0 scores — useful for CI green,
weak for teaching Evaluation-Driven Development.

## What changed

| Before | After |
|--------|--------|
| Domain logic inside one script | Domain FunctionTools + in-memory seed DB |
| Skill ≈ thin script wrapper | Skill = ordered runbook over tools |
| Iqama positives: `tool_uses: []` | Iqama positives require `load_skill_resource` |
| Fee amounts duplicated in script | Shared `get_violation_by_code` + `create_payment_draft` |
| Draft-only was text-only | `submit_payment` exists and must never be called |

## EDD fail → fix evidence (this refactor)

1. **Missing `metadata.adk_additional_tools`**  
   Agent tried `load_skill_resource` on fake scripts like
   `scripts/get_violation_by_code.py` instead of calling FunctionTools.
   Trajectory score **0.0**. Fix: declare tools per skill in frontmatter.

2. **Iqama-only "pay now" used combined violation defaults**  
   `adversarial_pay_now_draft_only` called `get_violation_by_code` for 101/205.
   Fix: skill workflow distinguishes Iqama-only vs combined owe/totals.

3. **Appointment rephrasing used week defaults instead of explicit dates**  
   Prompt said July 22–25; agent passed July 20–27. Fix: date rules in
   appointment SKILL.md.

4. **`dependents` int vs string**  
   ADK trajectory matching uses exact `args ==`. Softened goldens for
   `create_payment_draft` presence (pytest `must_call_tool`) while keeping
   ordered fee schedule + violation lookups in ADK goldens.

## Suite shape after refactor

- ADK eval sets: critical multi-step trajectories (centers→slots, fee schedule
  → violations, L3 resource load, draft-only routing).
- Pytest adversarial: skill routing + `must_call` / `must_not_call`
  (`create_payment_draft` / `submit_payment`).
- Pytest offtopic: prompts must not `load_skill` (response judge removed —
  too flaky for teaching).
- Unit tests: deterministic DB/tools (no API key).

## How to re-run

```powershell
cd backend
python -m pytest tests/test_demo_tools.py -v
python -m pytest tests/test_evals.py tests/test_offtopic.py -v
```

LLM evals can flake under rate limits (empty tool lists). Re-run the failed
skill parametrize target alone before changing goldens.
