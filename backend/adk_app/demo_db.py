"""In-memory seeded demo database for GovTech FunctionTools.

Data lives only for the process lifetime. All values are illustrative dummy
data — not real Saudi government records.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class DemoDB:
    """Process-local seed store used by demo FunctionTools."""

    violations: list[dict[str, Any]] = field(default_factory=list)
    early_payment_window_days: int = 30
    fee_schedule: dict[str, int] = field(default_factory=dict)
    holidays: list[str] = field(default_factory=list)
    cities: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    renewal_policy: dict[str, Any] = field(default_factory=dict)
    payment_drafts: dict[str, dict[str, Any]] = field(default_factory=dict)
    payments: dict[str, dict[str, Any]] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        """Return a deep copy useful for tests."""
        return {
            "violations": copy.deepcopy(self.violations),
            "early_payment_window_days": self.early_payment_window_days,
            "fee_schedule": copy.deepcopy(self.fee_schedule),
            "holidays": list(self.holidays),
            "cities": copy.deepcopy(self.cities),
            "renewal_policy": copy.deepcopy(self.renewal_policy),
            "payment_drafts": copy.deepcopy(self.payment_drafts),
            "payments": copy.deepcopy(self.payments),
        }


def seed_demo_db() -> DemoDB:
    """Build a fresh in-memory DB with demo seed rows."""
    return DemoDB(
        violations=[
            {
                "code": "101",
                "description": "Speeding 20 km/h over the limit",
                "base_fine_sar": 300,
                "early_payment_discount_pct": 50,
            },
            {
                "code": "205",
                "description": "Running a red light",
                "base_fine_sar": 500,
                "early_payment_discount_pct": 25,
            },
            {
                "code": "310",
                "description": "Illegal U-turn",
                "base_fine_sar": 200,
                "early_payment_discount_pct": 40,
            },
        ],
        early_payment_window_days=30,
        fee_schedule={
            "iqama_renewal_primary": 650,
            "iqama_renewal_dependent": 650,
            "express_processing_addon": 100,
        },
        holidays=["2026-09-23", "2026-12-05", "2026-08-15"],
        cities={
            "Riyadh": [
                {
                    "center_id": "RYD-01",
                    "name": "Riyadh Central",
                    "slots": {
                        "2026-07-20": ["09:00", "14:00"],
                        "2026-07-22": ["10:00"],
                        "2026-07-23": ["11:00"],
                        "2026-07-24": ["08:00"],
                        "2026-07-27": ["09:00"],
                    },
                },
                {
                    "center_id": "RYD-02",
                    "name": "Riyadh North",
                    "slots": {
                        "2026-07-21": ["10:00"],
                        "2026-07-22": ["15:00"],
                        "2026-07-24": ["09:00"],
                        "2026-07-26": ["11:00"],
                    },
                },
            ],
            "Jeddah": [
                {
                    "center_id": "JED-01",
                    "name": "Jeddah Corniche",
                    "slots": {
                        "2026-07-20": ["11:00"],
                        "2026-07-22": ["09:00"],
                        "2026-07-23": ["14:00"],
                        "2026-07-24": ["10:00"],
                    },
                },
                {
                    "center_id": "JED-02",
                    "name": "Jeddah South",
                    "slots": {
                        "2026-07-21": ["13:00"],
                        "2026-07-24": ["10:00"],
                        "2026-07-26": ["09:00"],
                    },
                },
            ],
            "Dammam": [
                {
                    "center_id": "DMM-01",
                    "name": "Dammam Main",
                    "slots": {
                        "2026-07-22": ["09:00"],
                        "2026-07-23": ["10:00"],
                        "2026-07-24": ["14:00"],
                    },
                },
                {
                    "center_id": "DMM-02",
                    "name": "Dammam East",
                    "slots": {
                        "2026-07-22": ["15:00"],
                        "2026-07-23": ["11:00"],
                    },
                },
            ],
        },
        renewal_policy={
            "required_documents": [
                "Valid passport copy",
                "Sponsor or employer letter confirming employment and sponsorship",
                "Medical fitness certificate from an approved clinic",
            ],
            "grace_period_days": 30,
            "grace_period_rule": (
                "Within 30 days of expiry: standard renewal still applies. "
                "Beyond 30 days after expiry: a different dummy corrective "
                "path may apply before standard renewal is available again."
            ),
            "disclaimer": (
                "Illustrative dummy demo data only. Verify via Absher, "
                "Muqeem, or SADAD."
            ),
        },
    )


def discounted_fine_sar(base_fine_sar: int, discount_pct: int) -> int:
    return round(base_fine_sar * (1 - discount_pct / 100))


def parse_center_ids(center_ids: str | list[str]) -> list[str]:
    if isinstance(center_ids, list):
        return [str(c).strip() for c in center_ids if str(c).strip()]
    return [part.strip() for part in str(center_ids).split(",") if part.strip()]


def parse_violation_codes(violation_codes: str | list[str]) -> list[str]:
    if isinstance(violation_codes, list):
        return [str(c).strip() for c in violation_codes if str(c).strip()]
    return [
        part.strip()
        for part in str(violation_codes).split(",")
        if part.strip()
    ]


def filter_slots_for_centers(
    db: DemoDB,
    center_ids: list[str],
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    holiday_set = set(db.holidays)
    wanted = set(center_ids)
    results: list[dict[str, Any]] = []

    for city_centers in db.cities.values():
        for center in city_centers:
            if center["center_id"] not in wanted:
                continue
            available: list[dict[str, str]] = []
            for day_str, times in center.get("slots", {}).items():
                day = datetime.strptime(day_str, "%Y-%m-%d").date()
                if day < start_date or day > end_date:
                    continue
                if day.weekday() in (4, 5):  # Fri/Sat
                    continue
                if day_str in holiday_set:
                    continue
                for time_slot in times:
                    available.append({"date": day_str, "time": time_slot})
            if available:
                results.append(
                    {
                        "center_id": center["center_id"],
                        "name": center["name"],
                        "slots": sorted(
                            available,
                            key=lambda s: (s["date"], s["time"]),
                        ),
                    }
                )
    return results


def new_draft_id() -> str:
    return f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
