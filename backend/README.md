# Backend - Python environment

This project uses **uv** as the recommended package manager, with **pip + venv** as a fallback (especially on Windows).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup with uv (recommended)

```powershell
cd backend
uv venv
.venv\Scripts\Activate.ps1
uv pip install -e .
```

## Setup with pip + venv (fallback)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Environment variables

ADK loads `.env` from the agent directory. Copy the example file and set your API key:

```powershell
copy adk_app\.env.example adk_app\.env
```

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LiteLLM |
| `LITELLM_MODEL` | Model string (default: `openai/gpt-4o-mini`) |
| `PYTHONUTF8` | Set to `1` on Windows to avoid LiteLLM encoding errors |

## Verify install

```powershell
python -c "import google.adk; import litellm; print(google.adk.__version__)"
```

Expected output: `2.4.0`

## Run agent

From `backend/` with the venv activated:

```powershell
# Interactive CLI chat
adk run adk_app

# Browser UI (dev only)
adk web --port 8000
```

Open http://localhost:8000, select **govtech_assistant**, and send a message.

From the repo root, you can also run:

```powershell
adk run backend/adk_app
```


## FastAPI server (custom UI + admin)

From `backend/` with the venv activated:

```powershell
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

- ADK Dev UI: http://localhost:8000 (select `adk_app`)
- Interactive docs: http://localhost:8000/docs
- Admin eval summary: `GET /api/admin/eval-summary`
- Simplified chat: `POST /api/chat` with `{"message": "..."}` → `{response, skill_used, tool_trajectory, session_id}`
- Default ADK chat still available at `POST /run` / `POST /run_sse` (full Event arrays)

Sessions persist in `server/sessions.db` (gitignored).

### Refresh admin JSON reports

```powershell
python -m harness.phase5_summary
python -m harness.token_budget_report  # also writes token_budget_report.json
# LLM required:
python -m harness.regression_eval
```

Reports land in `../evals/results/*.json` for the admin endpoint.

## Pinned dependencies

- `google-adk==2.4.0` - ADK 2.x with experimental Skills support (`SkillToolset`)
- `litellm` - excludes compromised versions 1.82.7 / 1.82.8 (see [ADK security advisory](https://github.com/google/adk-python/issues/5005))
- `tiktoken` - token counting for harness token-budget report

## Eval harness (pytest)

```powershell
# Skill frontmatter lint (CLI; also covered by test_skill_frontmatter.py)
python -m harness.lint_skills

# Fast suite: tools/DB, progressive skills, frontmatter (no API key)
python -m pytest -m "not llm" -v

# LLM suite only: ADK evals + adversarial + offtopic (needs OPENAI_API_KEY)
python -m pytest -m llm -v
```

LLM tests are marked `@pytest.mark.llm` (registered in `pyproject.toml`). CI splits the same way: `backend-ci` runs `-m "not llm"`; `skills-ci` runs the full EDD gate and **requires** the `OPENAI_API_KEY` repository secret.

Domain tools live in `adk_app/demo_tools.py` and read an in-memory seed DB from
`adk_app/demo_db.py` (process lifetime only). Skills instruct which tools to
call; see repo-root `AGENTS.md`.

Context budget (Agent Skills whitepaper):
- **L1 always-on** — skill name+description in the system prompt; no `list_skills` discovery round-trip.
- **Capability Profile swap** — one active skill (`unload_skill` / replace-on-load).
- **Event compaction** — ADK `App` summarizes older L2 bodies so history does not grow forever.

## Analysis harness scripts

From `backend/` with venv activated:

```powershell
# Skill frontmatter lint (L1 description budget via tiktoken)
python -m harness.lint_skills

# Token budget comparison (no API calls; uses tiktoken)
python -m harness.token_budget_report  # also writes token_budget_report.json

# Incremental skill-library regression eval (requires OPENAI_API_KEY)
python -m harness.regression_eval  # writes .md + regression_eval_report.json
python -m harness.phase5_summary  # writes phase5_eval_summary.json from ADK eval_history
```

The regression eval adds skills one at a time (iqama → traffic → fee-draft → appointment) in a temp copy of `skills/`, re-running eval cases for already-present skills at each step. Cross-skill routing cases are skipped until their referenced skills exist.

Reports land in `evals/results/`. At only four skills, token savings in the budget report will look modest vs the whitepaper's 50-skill example — that is expected.

