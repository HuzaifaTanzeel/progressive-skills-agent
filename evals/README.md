# Eval Harness Notes

## Architecture under test

Skills are **runbooks**. Domain FunctionTools (backed by an in-memory seed DB)
are the **hands**. Golden trajectories therefore name real tools such as
`get_violation_by_code`, `list_centers_by_city`, `list_available_slots`,
`get_fee_schedule`, and `create_payment_draft` — not a single
`run_skill_script` mega-step.

ADK only exposes `SkillToolset(additional_tools=...)` after a skill is loaded
**and** that skill's frontmatter lists the tool names under
`metadata.adk_additional_tools`. Without that list, the model falls back to
`load_skill_resource` / script guesses and trajectory scores go to 0.0 — a
useful EDD failure mode.

## Per-skill criteria

Manifest: `evals/eval_config.json`. ADK-compatible configs: `evals/configs/<skill>.json`.

| Skill | `tool_trajectory_avg_score` | `final_response_match_v2` |
|-------|----------------------------|---------------------------|
| iqama-renewal-status | threshold 1.0, **ANY_ORDER** (incl. `load_skill_resource`) | threshold 0.8 |
| traffic-violation-lookup | threshold 1.0, **ANY_ORDER** | threshold 0.8 |
| government-fee-payment-draft | threshold 1.0, **IN_ORDER** | threshold 0.8 |
| appointment-slot-finder | threshold 1.0, **IN_ORDER** | threshold 0.8 |

### Match types (ADK 2.4.0)

- **EXACT** — perfect tool sequence match; no extra/missing calls.
- **IN_ORDER** — expected tools in order; extras allowed between.
- **ANY_ORDER** — expected tools all present; order flexible; extras allowed.

## EDD loop (how this suite shows value)

1. Write / update JSON cases first: input, expected tools, expected output.
2. Run evals against a weak or outdated SKILL.md → expect trajectory **0.0**
   when order is wrong, centers are invented, or `submit_payment` is called.
3. Tighten the skill runbook until trajectories pass.
4. Keep documenting fail→fix in curated `evals/results/*.md` reports so the
   community story is evidence-backed (not a wall of 1.0 scores with shallow
   goldens). Ephemeral CLI dumps (`*.txt`) are gitignored — do not commit them.

### Critical cases that bite without good runbooks

| Case | Failure mode if SKILL.md is weak |
|------|----------------------------------|
| Appointment positives | Slots before centers, or fabricated `center_ids` |
| Fee `positive_how_much_do_i_owe` | Skips `get_violation_by_code`, invents SAR |
| Fee `adversarial_pay_now_draft_only` | Calls `submit_payment` or claims payment sent |
| Iqama positives | Answers without `load_skill_resource` (no L3) |

**Latitude gap (paper):** final-response judge may still score high when the
agent reaches plausible SAR totals via the wrong tool sequence. Trajectory
scoring is what makes draft-only / multi-step workflows fail closed.

## Schema decisions (ADK 2.4.0)

- Expected tool calls: `intermediate_data.tool_uses` (list of `{name, args}`).
- Negative routing: custom metadata `expected_skill` / `expected_skill_not`
  (ignored by ADK scoring) plus pytest adversarial checks in
  `backend/tests/test_evals.py`.
- Draft-only must-not-call: adversarial cases may set `must_not_call_tool`
  / `must_call_tool` (enforced in pytest, not native ADK fields).
- Off-topic prompts live in `eval_config.json` → `offtopic_no_skill_cases`
  and are scored only in `tests/test_offtopic.py` (no `load_skill`), because
  LLM-as-judge on refusal wording was too noisy for this demo.
- `create_payment_draft` args (`dependents` int vs `"2"`) are brittle under
  exact ADK arg equality; ADK goldens emphasize ordered lookups
  (`get_fee_schedule`, `get_violation_by_code`), while pytest asserts
  `create_payment_draft` was called and `submit_payment` was not.
- Response scoring: `final_response_match_v2` with `openai/gpt-4o-mini`.

## Example multi-step golden (appointment)
> L1 skill metadata (name + description) is injected into the system prompt every turn. Eval goldens start at `load_skill` — do not expect `list_skills`.


```json
"tool_uses": [
  {"name": "load_skill", "args": {"skill_name": "appointment-slot-finder"}},
  {"name": "list_centers_by_city", "args": {"city": "Riyadh"}},
  {"name": "list_available_slots", "args": {
    "center_ids": "RYD-01,RYD-02",
    "start_date": "2026-07-20",
    "end_date": "2026-07-27"
  }}
]
```

## Regenerating eval JSON

After changing tool contracts, regenerate goldens with:

```powershell
cd backend
python -m harness.generate_multistep_evals
```

Then re-run pytest and refresh curated reports:

```powershell
python -m harness.phase5_summary
python -m harness.token_budget_report
```

See [`evals/results/README.md`](results/README.md) for which files belong in git.
