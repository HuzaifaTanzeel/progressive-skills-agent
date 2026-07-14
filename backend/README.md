# Backend — Python environment

This project uses **uv** as the recommended package manager, with **pip + venv** as a fallback (especially on Windows).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup with uv (recommended)

`powershell
cd backend
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -e .
`

## Setup with pip + venv (fallback)

`powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
`

## Environment variables

ADK loads dk_app/.env from the agent directory. Copy the example and set your API key:

`powershell
copy adk_app\.env.example adk_app\.env
`

| Variable | Purpose |
|----------|---------|
| OPENAI_API_KEY | OpenAI API key for LiteLLM |
| LITELLM_MODEL | Model string (default: openai/gpt-4o-mini) |
| PYTHONUTF8 | Set to 1 on Windows to avoid LiteLLM encoding errors |
| SESSIONS_DB_PATH | Optional override for the SQLite session DB path (used in Docker) |

## Verify install

`powershell
python -c "import google.adk; import litellm; print(google.adk.__version__)"
`

Expected output: 2.4.0

## Run the agent

From ackend/ with the venv activated:

`powershell
# Interactive CLI chat
adk run adk_app

# Browser UI (dev only)
adk web --port 8000
`

Open http://localhost:8000, select **govtech_assistant**, and send a message.

## FastAPI server (custom UI + admin)

From ackend/ with the venv activated:

`powershell
uvicorn server.main:app --host 127.0.0.1 --port 8000
`

- ADK Dev UI: http://localhost:8000 (select dk_app)
- Interactive docs: http://localhost:8000/docs
- Admin eval summary: GET /api/admin/eval-summary
- Simplified chat: POST /api/chat with {"message": "..."}

Sessions persist in server/sessions.db locally (or $SESSIONS_DB_PATH in Docker).

### Refresh admin JSON reports

`powershell
python -m harness.phase5_summary
python -m harness.token_budget_report
python -m harness.regression_eval
`

Reports land in ../evals/results/*.json for the admin endpoint.

## Docker

Prefer repo-root Compose (frontend + backend together). Backend-only:

`powershell
# from repo root
docker build -f backend/Dockerfile -t govtech-backend .
docker run --rm -p 8000:8000 -e OPENAI_API_KEY=sk-... govtech-backend
`

See the [root README](../README.md#docker-compose) for docker compose up.

## Pinned dependencies

- google-adk[db,eval]==2.4.0 — ADK 2.x with experimental Skills (SkillToolset)
- litellm — excludes compromised versions 1.82.7–1.82.8
- 	iktoken — token counting for harness token-budget report

## Eval harness (pytest)

`powershell
python -m harness.lint_skills
python -m pytest -m "not llm" -v
python -m pytest -m llm -v
`

CI: ackend-ci runs -m "not llm"; skills-ci requires OPENAI_API_KEY.

Domain tools: dk_app/demo_tools.py + in-memory dk_app/demo_db.py. See repo-root AGENTS.md.

## Analysis harness scripts

`powershell
python -m harness.lint_skills
python -m harness.token_budget_report
python -m harness.regression_eval
python -m harness.phase5_summary
`

Reports land in evals/results/. Keep curated .md/.json only — ephemeral *.txt dumps are gitignored.
