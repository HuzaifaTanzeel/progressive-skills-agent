"""Deprecated: use list_centers_by_city + list_available_slots FunctionTools.

Kept for local inspection only. Primary agent workflows must call the tools.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from adk_app.demo_db import seed_demo_db  # noqa: E402
from adk_app.demo_tools import build_demo_tools  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deprecated wrapper; prefer multi-step center/slot tools."
    )
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()
    tools = {t.__name__: t for t in build_demo_tools(seed_demo_db())}
    centers = tools["list_centers_by_city"](args.city)
    ids = ",".join(c["center_id"] for c in centers.get("centers", []))
    result = tools["list_available_slots"](ids, args.start_date, args.end_date)
    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
