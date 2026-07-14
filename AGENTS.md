# GovTech Skills Assistant

## What this is
A demonstration project showing how Agent Skills (per the agentskills.io open
standard, implemented here via Google ADK's SkillToolset) let a single general-
purpose agent behave as multiple specialists on demand, without a multi-agent
architecture. It covers four Saudi citizen-services workflows: Iqama renewal
info, traffic violation lookup, government fee drafting, and appointment slot
finding.

## Disclaimer
This is a demo only. It is not affiliated with, endorsed by, or representative
of any real Saudi government system. All data (fees, violation codes, renewal
windows, appointment slots) is dummy and illustrative. Always verify anything
that matters via official channels (Absher, Muqeem, SADAD).

## What goes where (paper mental model)

| Layer | Role in this repo | Example |
|---|---|---|
| `AGENTS.md` | Always-on project instincts | Disclaimer, tiers, catalog |
| `skills/*/SKILL.md` | On-demand **runbook** (when + how) | Ordered tool steps, anti-patterns |
| FunctionTools + in-memory DB | Agent **hands** (deterministic I/O) | `get_violation_by_code`, `list_centers_by_city` |
| `evals/` | Spec before polish (EDD) | Expected tool trajectory + response |

One-line model from the Agent Skills whitepaper: system prompt = instinct;
AGENTS.md = project README; **tools = hands**; **skills = the runbook**.

Skills are **not** thin wrappers around one mega-script. A skill loads
instructions, then the agent calls domain tools in the order the skill
specifies. Tool A output feeds tool B (e.g. `center_ids` from
`list_centers_by_city` into `list_available_slots`).

In ADK, domain FunctionTools registered on SkillToolset(additional_tools=...)
only appear after a skill is activated and lists them under
metadata.adk_additional_tools in that skill frontmatter. That is intentional:
tools stay out of context until the matching runbook is loaded.

Progressive disclosure (L1 metadata → L2 SKILL body → L3 references/scripts)
is the token model from the whitepaper:

1. **L1 always-on** — skill name + short description sit in the system prompt
   every turn (~paper: ~50 tokens/skill). Do **not** call list_skills to
   discover names; that costs an extra round-trip and copies the catalog into
   conversation history. Exact <name> values come from <available_skills>.
2. **Capability Profile swap** — load_skill keeps only one skill activated;
   prior skills unload so their domain tools leave the tool list
   (ProgressiveSkillToolset / unload_skill).
3. **Event compaction** — the ADK App summarizes older turns (including past
   L2 bodies) so multi-step sessions do not grow tokens unboundedly.

Keep L1 descriptions short (trigger + anti-trigger). Long routing prose is
Context Debt (paper §7).

## Why skill tiers exist here (compliance framing)
Each skill in this library is assigned a tier: read-only, draft-only, or
action-allowed (see Section 4/Appendix B of the "Agent Skills" whitepaper this
project is based on). The government-fee-payment-draft skill is deliberately
draft-only: it can calculate and summarize a fee breakdown via
`create_payment_draft`, but it must **never** call `submit_payment`. That
forbidden tool exists so trajectory evals can catch compliance failures even
when the final answer sounds fine — the Latitude gap the whitepaper cites
(output-only scoring passes 20–40% more cases than trajectory-aware scoring).

To be explicit: this project does not implement PDPL or SAMA compliance. It
borrows the *shape* of that requirement (draft-only, human sign-off before
action) to demonstrate concretely why skill tiers exist and why "the model
decided it's fine" is never sufficient justification for an action-allowed
skill in a regulated domain.

## The four skills (catalog)
| Skill | Purpose | Tier | Critical tool trajectory |
|---|---|---|---|
| iqama-renewal-status | Renewal docs / grace eligibility | read-only | `load_skill_resource` (L3) |
| traffic-violation-lookup | Single-code fine + early discount | read-only | `get_violation_by_code` |
| government-fee-payment-draft | Fee breakdown; never submits | draft-only | `get_fee_schedule` → (optional `get_violation_by_code`) → `create_payment_draft`; never `submit_payment` |
| appointment-slot-finder | Slots by city / date range | read-only | `list_centers_by_city` → `list_available_slots` |

## Demo data plane
Domain tools read an **in-memory seeded DB** (`backend/adk_app/demo_db.py`) that
lives only for the process lifetime. In production these hands would be MCP /
HTTP APIs; the skill runbooks stay portable.

## Running this project
See backend/README.md for setup.

## Eval harness
Eval sets live in `evals/*.evalset.json`; shared criteria in
`evals/eval_config.json`. Trajectory scoring uses ADK
`tool_trajectory_avg_score` (IN_ORDER / ANY_ORDER). CI runs deterministic
tool unit tests always; LLM evals run when `OPENAI_API_KEY` is available.
See evals/README.md for EDD workflow notes.
