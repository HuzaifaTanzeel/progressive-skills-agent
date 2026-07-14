---
name: iqama-renewal-status
description: |
  Iqama/residency renewal docs, expiry, grace-period eligibility, steps. Use when asking what to prepare or whether standard renewal still applies. Do NOT use for fee totals or payment quotes — use government-fee-payment-draft.
version: 1.1.0
license: MIT
tier: read-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
---

## Workflow

1. Call `load_skill_resource` with
   `file_path="references/renewal_rules.md"` (after this skill is loaded).
2. Answer the specific question using only values from that reference.
3. Label all data as illustrative dummy demo content; add Absher/Muqeem/SADAD
   verification line.

## Output format

- Direct answer first, then supporting bullets if needed.
- Cite dummy document list or grace rule only when relevant.
- End with one-line official-channel verification reminder.

## Anti-patterns to avoid

- Answering from memory without calling `load_skill_resource`.
- Quoting fees as the main answer when the user only asked for documents or
  eligibility (fee totals belong in government-fee-payment-draft).
- Inventing requirements beyond `renewal_rules.md`.
- Omitting the illustrative/dummy disclaimer.
