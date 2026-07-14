# GovTech Skills Assistant

Saudi GovTech citizen services demo (Iqama, traffic violations, fee drafting, appointments) built with **Google ADK** (Python).

This repo demonstrates Agent Skills as **runbooks over tools**, Evaluation-Driven Development (EDD), trajectory scoring, and CI/CD — with four human-authored skills and an in-memory dummy data plane.

## Stack

- **Agent framework:** Google ADK (`google-adk[db,eval]==2.4.0`) + `LiteLlm` (OpenAI default: `gpt-4o-mini`)
- **Skills:** agentskills.io folders under `skills/` via ADK `SkillToolset`
- **Tools:** domain FunctionTools (`get_violation_by_code`, `list_centers_by_city`, …) on an in-memory seeded DB
- **Eval:** ADK `EvalSet` / `tool_trajectory_avg_score` + pytest adversarial checks

## Repo layout

```
govtech-skills-assistant/
├── skills/          # 4 Agent Skills (runbooks)
├── evals/           # Per-skill eval sets + eval_config.json
├── backend/         # ADK agent, demo DB/tools, harness, tests
├── frontend/        # Placeholder
└── .github/workflows/  # backend-ci.yml + skills-ci.yml
```

## Getting started

See [backend/README.md](backend/README.md) for Python environment setup.

## What EDD looks like here

Happy-path answers alone are not enough. Eval goldens require multi-step tool
trajectories (centers before slots; fee schedule + violation lookups before
`create_payment_draft`; never `submit_payment`). See [evals/README.md](evals/README.md)
and [AGENTS.md](AGENTS.md).

## Harness scripts

From `backend/` with venv activated:

```powershell
# Skill frontmatter lint (required fields + L1 description <= 50 tiktoken tokens)
python -m harness.lint_skills

# Fast suite: unit/schema/frontmatter (excludes @pytest.mark.llm)
python -m pytest -m "not llm" -v

# LLM eval suite only (requires OPENAI_API_KEY; enforces eval_config.json thresholds)
python -m pytest -m llm -v

# Token budget: progressive disclosure vs monolithic prompt (no API calls)
python -m harness.token_budget_report

# Incremental skill-library regression eval (many LLM calls)
python -m harness.regression_eval
```

## CI

Two GitHub Actions workflows (cost-split):

| Workflow | When | What |
|----------|------|------|
| `.github/workflows/backend-ci.yml` | push / PR | Fast, **LLM-free**: `pytest -m "not llm"` (tools, progressive skills, frontmatter lint via test) |
| `.github/workflows/skills-ci.yml` | push / PR | Full EDD gate: `harness.lint_skills`, `pytest -m llm`, `harness.regression_eval`, token-budget artifact |

**Required secret for `skills-ci`:** repository secret `OPENAI_API_KEY` (Settings → Secrets and variables → Actions). Without it, `skills-ci` fails closed (no silent skip). Backend deps pin `google-adk[db,eval]==2.4.0` via `backend/pyproject.toml`.
