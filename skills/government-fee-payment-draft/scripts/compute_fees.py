"""Deprecated: use get_fee_schedule + create_payment_draft FunctionTools.

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
        description="Deprecated wrapper; prefer create_payment_draft tool."
    )
    parser.add_argument(
        "--request-type",
        required=True,
        choices=["iqama_renewal", "combined_summary"],
    )
    parser.add_argument("--dependents", type=int, default=0)
    parser.add_argument("--violation-codes", default="")
    parser.add_argument("--include-express", action="store_true")
    args = parser.parse_args()
    tools = {t.__name__: t for t in build_demo_tools(seed_demo_db())}
    codes = args.violation_codes
    if args.request_type == "combined_summary" and not codes:
        codes = "101,205"
    result = tools["create_payment_draft"](
        dependents=args.dependents,
        violation_codes=codes,
        include_express=args.include_express,
    )
    print(json.dumps(result, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
