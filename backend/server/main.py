"""FastAPI entrypoint wrapping ADK get_fast_api_app + admin/chat routes."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.sessions.database_session_service import DatabaseSessionService

from server.routes_admin import router as admin_router
from server.routes_chat import configure_chat
from server.routes_chat import router as chat_router

BACKEND_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = Path(__file__).resolve().parent
SESSIONS_DB = Path(
    os.environ.get("SESSIONS_DB_PATH", str(SERVER_DIR / "sessions.db"))
)
SESSIONS_DB.parent.mkdir(parents=True, exist_ok=True)

# Absolute path for sqlite+aiosqlite (forward slashes work on Windows).
SESSION_SERVICE_URI = f"sqlite+aiosqlite:///{SESSIONS_DB.as_posix()}"

load_dotenv(BACKEND_DIR / "adk_app" / ".env")

app = get_fast_api_app(
    agents_dir=str(BACKEND_DIR),
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=["*"],
    web=True,
    auto_create_session=True,
)

# Share the same sqlite DB as get_fast_api_app for custom /api/chat sessions.
_chat_sessions = DatabaseSessionService(db_url=SESSION_SERVICE_URI)
configure_chat(_chat_sessions)

app.include_router(admin_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        reload=False,
    )
