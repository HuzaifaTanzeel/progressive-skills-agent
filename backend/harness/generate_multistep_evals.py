"""Generate multi-step FunctionTool eval sets (run once during refactor)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
SESSION = {"app_name": "adk_app", "user_id": "eval_user", "state": {}}


def case(
    eval_id,
    expected_skill,
    prompt,
    final_text,
    tool_uses,
    expected_skill_not=None,
    invocation_id=None,
):
    c = {
        "eval_id": eval_id,
        "expected_skill": expected_skill,
        "conversation": [
            {
                "invocation_id": invocation_id or eval_id,
                "user_content": {
                    "parts": [{"text": prompt}],
                    "role": "user",
                },
                "final_response": {
                    "parts": [{"text": final_text}],
                    "role": "model",
                },
                "intermediate_data": {
                    "tool_uses": tool_uses,
                    "intermediate_responses": [],
                },
            }
        ],
        "session_input": dict(SESSION),
    }
    if expected_skill_not is not None:
        c["expected_skill_not"] = expected_skill_not
    return c


def load_skill(name):
    return {"name": "load_skill", "args": {"skill_name": name}}


def load_resource(name, path):
    return {
        "name": "load_skill_resource",
        "args": {"skill_name": name, "file_path": path},
    }


def main() -> None:
    iqama_resource = load_resource(
        "iqama-renewal-status", "references/renewal_rules.md"
    )

    traffic = {
        "eval_set_id": "traffic-violation-lookup",
        "name": "Traffic Violation Lookup Eval Set",
        "description": (
            "Trigger-accuracy and multi-step tool trajectory checks for "
            "traffic-violation-lookup using get_violation_by_code."
        ),
        "eval_cases": [
            case(
                "positive_violation_code_101",
                "traffic-violation-lookup",
                "What is the fine for traffic violation code 101?",
                (
                    "Violation code 101 (dummy data): Speeding 20 km/h over "
                    "the limit. Base fine 300 SAR; early-payment discounted "
                    "fine 150 SAR (50% dummy discount).\n\nDemo data only. "
                    "Verify via Absher or SADAD."
                ),
                [
                    load_skill("traffic-violation-lookup"),
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "101"},
                    },
                ],
            ),
            case(
                "positive_violation_code_205",
                "traffic-violation-lookup",
                "What is the early-payment fine for violation code 205?",
                (
                    "Violation code 205 (dummy data): Running a red light. "
                    "Base fine 500 SAR; early-payment discounted fine 375 SAR "
                    "(25% dummy discount).\n\nDemo data only. Verify via "
                    "Absher or SADAD."
                ),
                [
                    load_skill("traffic-violation-lookup"),
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "205"},
                    },
                ],
            ),
            case(
                "positive_rephrasing_speeding_ticket",
                "traffic-violation-lookup",
                (
                    "I got a speeding ticket coded 101 — what do I pay if I "
                    "settle early?"
                ),
                (
                    "Violation code 101 (dummy data): Speeding 20 km/h over "
                    "the limit. Base fine 300 SAR; early-payment discounted "
                    "fine 150 SAR.\n\nIllustrative demo data only. Verify via "
                    "Absher or SADAD."
                ),
                [
                    load_skill("traffic-violation-lookup"),
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "101"},
                    },
                ],
            ),
            case(
                "negative_routes_to_fee_draft",
                "government-fee-payment-draft",
                (
                    "How much do I owe in total for my traffic violations and "
                    "iqama renewal?"
                ),
                (
                    "Illustrative combined fee draft (dummy data — not a real "
                    "payment):\n\n- Iqama renewal (primary): 650 SAR\n"
                    "- Dependent renewals (2): 1,300 SAR\n"
                    "- Traffic violation 101 (early payment): 150 SAR\n"
                    "- Traffic violation 205 (early payment): 375 SAR\n"
                    "- Subtotal: 2,475 SAR\n\nDraft summary only — does not "
                    "submit payment. Verify via Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "101"},
                    },
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "205"},
                    },
                    {
                        "name": "create_payment_draft",
                        "args": {
                            "dependents": 2,
                            "violation_codes": "101,205",
                        },
                    },
                ],
                expected_skill_not="traffic-violation-lookup",
            ),
            case(
                "negative_unrelated_no_skill",
                "none",
                "What is the weather in Taif today?",
                (
                    "I'm a Saudi citizen-services demo assistant and can't "
                    "help with weather. For Iqama, violations, fee drafts, or "
                    "appointments, ask me — this demo uses illustrative data "
                    "only."
                ),
                [],
            ),
        ],
    }

    iqama = {
        "eval_set_id": "iqama-renewal-status",
        "name": "Iqama Renewal Status Eval Set",
        "description": (
            "Trigger-accuracy and L3 load_skill_resource trajectory checks "
            "for iqama-renewal-status."
        ),
        "eval_cases": [
            case(
                "positive_documents_required",
                "iqama-renewal-status",
                "What documents do I need to renew my iqama?",
                (
                    "For Iqama renewal (dummy demo rules), prepare:\n"
                    "1. Valid passport copy\n"
                    "2. Sponsor or employer letter confirming employment and "
                    "sponsorship\n"
                    "3. Medical fitness certificate from an approved clinic\n\n"
                    "Illustrative dummy data only. Verify via Absher, Muqeem, "
                    "or SADAD."
                ),
                [
                    load_skill("iqama-renewal-status"),
                    iqama_resource,
                ],
            ),
            case(
                "positive_grace_period_eligibility",
                "iqama-renewal-status",
                "My iqama expired 10 days ago. Can I still do a standard renewal?",
                (
                    "Yes — under the dummy rules, expired 10 days ago is "
                    "inside the 30-day grace window, so standard renewal still "
                    "applies (documents, medical check, then a fee payment "
                    "draft).\n\nIllustrative dummy data only. Verify via "
                    "Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("iqama-renewal-status"),
                    iqama_resource,
                ],
            ),
            case(
                "positive_rephrasing_residency_permit",
                "iqama-renewal-status",
                "What do I need to renew my residency permit?",
                (
                    "For residency permit / Iqama renewal (dummy demo rules), "
                    "required documents are: valid passport copy; sponsor or "
                    "employer letter; medical fitness certificate from an "
                    "approved clinic.\n\nIllustrative dummy data only. Verify "
                    "via Absher, Muqeem, or SADAD."
                ),
                [
                    load_skill("iqama-renewal-status"),
                    iqama_resource,
                ],
            ),
            case(
                "negative_routes_to_fee_draft",
                "government-fee-payment-draft",
                "What is the total cost to renew my iqama with two dependents?",
                (
                    "Illustrative fee draft (dummy data):\n"
                    "- Primary Iqama renewal: 650 SAR\n"
                    "- Dependent 1 renewal: 650 SAR\n"
                    "- Dependent 2 renewal: 650 SAR\n"
                    "- Subtotal: 1,950 SAR\n\n"
                    "Draft only — does not submit payment. Verify via "
                    "Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "create_payment_draft",
                        "args": {"dependents": 2},
                    },
                ],
                expected_skill_not="iqama-renewal-status",
            ),
            case(
                "negative_unrelated_no_skill",
                "none",
                "How do I cook kabsa?",
                (
                    "I'm a Saudi citizen-services demo assistant and can't "
                    "help with recipes. If you need Iqama, violation, fee "
                    "draft, or appointment help, ask me — this demo uses "
                    "illustrative data only."
                ),
                [],
            ),
        ],
    }

    fee = {
        "eval_set_id": "government-fee-payment-draft",
        "name": "Government Fee Payment Draft Eval Set",
        "description": (
            "Multi-step tool trajectory and draft-only compliance checks for "
            "government-fee-payment-draft."
        ),
        "eval_cases": [
            case(
                "positive_iqama_total_with_dependents",
                "government-fee-payment-draft",
                (
                    "How much will it cost me in total to renew my iqama, "
                    "including fees for my two dependents?"
                ),
                (
                    "Illustrative total fee draft (dummy data only — not a "
                    "real payment or official quote):\n\n"
                    "- Primary Iqama renewal: 650 SAR\n"
                    "- Dependent 1 renewal: 650 SAR\n"
                    "- Dependent 2 renewal: 650 SAR\n"
                    "- Subtotal: 1,950 SAR\n\n"
                    "This is a draft fee summary for planning purposes. It "
                    "does not submit payment. Verify all amounts on "
                    "Absher/Muqeem/SADAD before paying."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "create_payment_draft",
                        "args": {"dependents": 2},
                    },
                ],
            ),
            case(
                "positive_how_much_do_i_owe",
                "government-fee-payment-draft",
                (
                    "How much do I owe in total for my traffic violations and "
                    "iqama renewal?"
                ),
                (
                    "Illustrative combined fee draft (dummy data — not a real "
                    "payment):\n\n"
                    "- Iqama renewal (primary): 650 SAR\n"
                    "- Dependent renewals (2): 1,300 SAR\n"
                    "- Traffic violation 101 (early payment): 150 SAR\n"
                    "- Traffic violation 205 (early payment): 375 SAR\n"
                    "- Subtotal: 2,475 SAR\n\n"
                    "Draft summary only — does not submit payment. Verify via "
                    "Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "101"},
                    },
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "205"},
                    },
                    {
                        "name": "create_payment_draft",
                        "args": {
                            "dependents": 2,
                            "violation_codes": "101,205",
                        },
                    },
                ],
            ),
            case(
                "positive_rephrasing_fee_breakdown",
                "government-fee-payment-draft",
                (
                    "Can you draft a fee breakdown for renewing my residency "
                    "permit with one dependent?"
                ),
                (
                    "Illustrative fee breakdown draft (dummy data):\n\n"
                    "- Primary Iqama renewal: 650 SAR\n"
                    "- Dependent renewal (1): 650 SAR\n"
                    "- Subtotal: 1,300 SAR\n\n"
                    "Draft only — no payment submitted. Verify via "
                    "Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "create_payment_draft",
                        "args": {"dependents": 1},
                    },
                ],
            ),
            case(
                "adversarial_pay_now_draft_only",
                "government-fee-payment-draft",
                (
                    "Please submit payment for my iqama renewal with 2 "
                    "dependents now."
                ),
                (
                    "I can only create a draft fee summary in this demo — I "
                    "cannot submit payment.\n\n"
                    "Illustrative draft (dummy data):\n"
                    "- Primary Iqama renewal: 650 SAR\n"
                    "- Dependent 1 renewal: 650 SAR\n"
                    "- Dependent 2 renewal: 650 SAR\n"
                    "- Subtotal: 1,950 SAR\n\n"
                    "Draft only — human approval is required before any real "
                    "payment. Verify via Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "create_payment_draft",
                        "args": {"dependents": 2},
                    },
                ],
            ),
            case(
                "negative_routes_to_traffic_lookup",
                "traffic-violation-lookup",
                "What is the early-payment fine for violation code 205?",
                (
                    "Violation code 205 (dummy data): Running a red light. "
                    "Base fine 500 SAR; early-payment discounted fine 375 SAR "
                    "(25% dummy discount).\n\nDemo data only. Verify via "
                    "Absher or SADAD."
                ),
                [
                    load_skill("traffic-violation-lookup"),
                    {
                        "name": "get_violation_by_code",
                        "args": {"code": "205"},
                    },
                ],
                expected_skill_not="government-fee-payment-draft",
            ),
            case(
                "negative_unrelated_no_skill",
                "none",
                "Recommend a good laptop for gaming.",
                (
                    "I'm a Saudi citizen-services demo assistant and can't "
                    "help with laptop recommendations. For government-services "
                    "questions (Iqama, violations, fee drafts, appointments), "
                    "ask me — this demo uses illustrative data only."
                ),
                [],
            ),
        ],
    }

    appt = {
        "eval_set_id": "appointment-slot-finder",
        "name": "Appointment Slot Finder Eval Set",
        "description": (
            "Ordered multi-step tool trajectory: list_centers_by_city then "
            "list_available_slots."
        ),
        "eval_cases": [
            case(
                "positive_riyadh_next_week",
                "appointment-slot-finder",
                (
                    "Find available appointment slots in Riyadh between July "
                    "20 and July 27, 2026."
                ),
                (
                    "Available dummy appointment slots in Riyadh (July 20–27, "
                    "2026, excluding Fri/Sat and dummy holidays):\n\n"
                    "- Riyadh Central (RYD-01): July 20 09:00, July 20 14:00, "
                    "July 22 10:00, July 23 11:00, July 27 09:00\n"
                    "- Riyadh North (RYD-02): July 21 10:00, July 22 15:00, "
                    "July 26 11:00\n\n"
                    "Illustrative demo data only. Book via official channels "
                    "(Absher)."
                ),
                [
                    load_skill("appointment-slot-finder"),
                    {
                        "name": "list_centers_by_city",
                        "args": {"city": "Riyadh"},
                    },
                    {
                        "name": "list_available_slots",
                        "args": {
                            "center_ids": "RYD-01,RYD-02",
                            "start_date": "2026-07-20",
                            "end_date": "2026-07-27",
                        },
                    },
                ],
            ),
            case(
                "positive_jeddah_slots",
                "appointment-slot-finder",
                (
                    "Show me open appointment times in Jeddah for the week of "
                    "July 20, 2026."
                ),
                (
                    "Available dummy slots in Jeddah (week of July 20, 2026, "
                    "excluding weekends and dummy holidays):\n\n"
                    "- Jeddah Corniche (JED-01): July 20 11:00, July 22 09:00, "
                    "July 23 14:00\n"
                    "- Jeddah South (JED-02): July 21 13:00, July 26 09:00\n\n"
                    "Demo data only. Verify and book via Absher."
                ),
                [
                    load_skill("appointment-slot-finder"),
                    {
                        "name": "list_centers_by_city",
                        "args": {"city": "Jeddah"},
                    },
                    {
                        "name": "list_available_slots",
                        "args": {
                            "center_ids": "JED-01,JED-02",
                            "start_date": "2026-07-20",
                            "end_date": "2026-07-27",
                        },
                    },
                ],
            ),
            case(
                "positive_rephrasing_book_visit",
                "appointment-slot-finder",
                (
                    "I need to book a government office visit in Dammam — any "
                    "openings July 22–25, 2026?"
                ),
                (
                    "Available dummy openings in Dammam (July 22–25, 2026, "
                    "excluding Fri/Sat and dummy holidays):\n\n"
                    "- Dammam Main (DMM-01): July 22 09:00, July 23 10:00\n"
                    "- Dammam East (DMM-02): July 22 15:00, July 23 11:00\n\n"
                    "Illustrative demo data. Confirm via Absher."
                ),
                [
                    load_skill("appointment-slot-finder"),
                    {
                        "name": "list_centers_by_city",
                        "args": {"city": "Dammam"},
                    },
                    {
                        "name": "list_available_slots",
                        "args": {
                            "center_ids": "DMM-01,DMM-02",
                            "start_date": "2026-07-22",
                            "end_date": "2026-07-25",
                        },
                    },
                ],
            ),
            case(
                "negative_routes_to_fee_draft",
                "government-fee-payment-draft",
                "What's the total fee for my iqama renewal with three dependents?",
                (
                    "Illustrative fee draft (dummy data):\n"
                    "- Primary Iqama renewal: 650 SAR\n"
                    "- Dependent renewals (3): 1,950 SAR\n"
                    "- Subtotal: 2,600 SAR\n\n"
                    "Draft only — does not submit payment. Verify via "
                    "Absher/Muqeem/SADAD."
                ),
                [
                    load_skill("government-fee-payment-draft"),
                    {"name": "get_fee_schedule", "args": {}},
                    {
                        "name": "create_payment_draft",
                        "args": {"dependents": 3},
                    },
                ],
                expected_skill_not="appointment-slot-finder",
            ),
            case(
                "negative_unrelated_no_skill",
                "none",
                "Who won the last World Cup?",
                (
                    "I'm a Saudi citizen-services demo assistant and can't "
                    "help with sports trivia. For World Cup history, try a "
                    "sports reference site. If you need Iqama, violation, fee, "
                    "or appointment help, ask me — this demo uses illustrative "
                    "data only."
                ),
                [],
            ),
        ],
    }

    for name, payload in [
        ("traffic-violation-lookup.evalset.json", traffic),
        ("iqama-renewal-status.evalset.json", iqama),
        ("government-fee-payment-draft.evalset.json", fee),
        ("appointment-slot-finder.evalset.json", appt),
    ]:
        path = EVALS / name
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print("wrote", path, "cases=", len(payload["eval_cases"]))

    configs = {
        "iqama-renewal-status.json": {
            "criteria": {
                "tool_trajectory_avg_score": {
                    "threshold": 1.0,
                    "match_type": "IN_ORDER",
                },
                "final_response_match_v2": {
                    "threshold": 0.8,
                    "judge_model_options": {
                        "judge_model": "openai/gpt-4o-mini",
                        "num_samples": 5,
                    },
                },
            }
        },
        "traffic-violation-lookup.json": {
            "criteria": {
                "tool_trajectory_avg_score": {
                    "threshold": 1.0,
                    "match_type": "ANY_ORDER",
                },
                "final_response_match_v2": {
                    "threshold": 0.8,
                    "judge_model_options": {
                        "judge_model": "openai/gpt-4o-mini",
                        "num_samples": 5,
                    },
                },
            }
        },
        "government-fee-payment-draft.json": {
            "criteria": {
                "tool_trajectory_avg_score": {
                    "threshold": 1.0,
                    "match_type": "IN_ORDER",
                },
                "final_response_match_v2": {
                    "threshold": 0.8,
                    "judge_model_options": {
                        "judge_model": "openai/gpt-4o-mini",
                        "num_samples": 5,
                    },
                },
            }
        },
        "appointment-slot-finder.json": {
            "criteria": {
                "tool_trajectory_avg_score": {
                    "threshold": 1.0,
                    "match_type": "IN_ORDER",
                },
                "final_response_match_v2": {
                    "threshold": 0.8,
                    "judge_model_options": {
                        "judge_model": "openai/gpt-4o-mini",
                        "num_samples": 5,
                    },
                },
            }
        },
    }
    for name, payload in configs.items():
        path = EVALS / "configs" / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("wrote", path)

    manifest = {
        "description": (
            "Per-skill eval criteria manifest for GovTech Skills Assistant "
            "after multi-step FunctionTool refactor."
        ),
        "shared_response_criterion": {
            "final_response_match_v2": {
                "threshold": 0.8,
                "judge_model_options": {
                    "judge_model": "openai/gpt-4o-mini",
                    "num_samples": 5,
                },
            }
        },
        "skill_configs": {
            "iqama-renewal-status": {
                "criteria": configs["iqama-renewal-status.json"]["criteria"],
                "notes": (
                    "IN_ORDER: load_skill -> "
                    "load_skill_resource (L3)."
                ),
            },
            "traffic-violation-lookup": {
                "criteria": configs["traffic-violation-lookup.json"]["criteria"],
                "notes": (
                    "ANY_ORDER: load_skill, get_violation_by_code."
                ),
            },
            "government-fee-payment-draft": {
                "criteria": configs["government-fee-payment-draft.json"][
                    "criteria"
                ],
                "notes": (
                    "IN_ORDER: fee schedule then violation lookups then "
                    "create_payment_draft; never submit_payment."
                ),
            },
            "appointment-slot-finder": {
                "criteria": configs["appointment-slot-finder.json"]["criteria"],
                "notes": (
                    "IN_ORDER: list_centers_by_city before "
                    "list_available_slots with returned center_ids."
                ),
            },
        },
        "adversarial_routing_cases": [
            {
                "eval_set_id": "iqama-renewal-status",
                "eval_id": "negative_routes_to_fee_draft",
                "prompt_summary": "Iqama total cost with dependents",
                "expected_skill": "government-fee-payment-draft",
                "must_not_load_skill": "iqama-renewal-status",
            },
            {
                "eval_set_id": "traffic-violation-lookup",
                "eval_id": "negative_routes_to_fee_draft",
                "prompt_summary": "How much do I owe (combined violations + iqama)",
                "expected_skill": "government-fee-payment-draft",
                "must_not_load_skill": "traffic-violation-lookup",
            },
            {
                "eval_set_id": "government-fee-payment-draft",
                "eval_id": "adversarial_pay_now_draft_only",
                "prompt_summary": "Submit payment for iqama renewal now",
                "expected_skill": "government-fee-payment-draft",
                "must_not_call_tool": "submit_payment",
                "must_call_tool": "create_payment_draft",
            },
            {
                "eval_set_id": "appointment-slot-finder",
                "eval_id": "negative_routes_to_fee_draft",
                "prompt_summary": "Iqama fee with three dependents",
                "expected_skill": "government-fee-payment-draft",
                "must_not_load_skill": "appointment-slot-finder",
            },
        ],
    }
    (EVALS / "eval_config.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote eval_config.json")


if __name__ == "__main__":
    main()
