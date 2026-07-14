"""Deprecated: use get_violation_by_code FunctionTool instead.

Kept as a thin reference wrapper over the same demo seed values for local
script inspection. Primary agent workflows must call the FunctionTool.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow importing backend when run from the skill scripts directory.
_BACKEND = Path(__file__).resolve().parents[3] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from adk_app.demo_db import seed_demo_db  # noqa: E402
from adk_app.demo_tools import build_demo_tools  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deprecated wrapper; prefer get_violation_by_code tool."
    )
    parser.add_argument("--code", required=True)
    args = parser.parse_args()
    tools = {t.__name__: t for t in build_demo_tools(seed_demo_db())}
    result = tools["get_violation_by_code"](args.code)
    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
