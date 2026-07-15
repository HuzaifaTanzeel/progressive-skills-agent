---
name: appointment-slot-finder
description: |
  Find Absher/office visit slots by city and date. Never for cost, fee totals, dependents, iqama renew quotes, or violation fines.
version: 1.1.1
license: MIT
tier: read-only
allowed-tools: ""
metadata:
  author: citizen-services-content-team
  adk_additional_tools:
    - list_centers_by_city
    - list_available_slots
---

## Workflow

After this skill is loaded, FunctionTools `list_centers_by_city` and
`list_available_slots` become available. Do **not** use `run_skill_script`.

1. Call `list_centers_by_city` with the city name (e.g. `"Riyadh"`).
2. From the tool result, collect every `center_id` (comma-separated string).
3. Call `list_available_slots` with:
   - `center_ids` = the IDs returned in step 1 (never invent IDs)
   - `start_date` and `end_date` as `YYYY-MM-DD`
4. The slots tool excludes Friday, Saturday, and dummy holidays. Present
   results grouped by center.

Date rules:
- If the user gives an explicit start and end (e.g. July 22–25, 2026), pass
  those exact dates as `YYYY-MM-DD` (`2026-07-22` … `2026-07-25`).
- Only when the user says "week of July 20, 2026" (or similar) without an
  explicit end date, use `start_date="2026-07-20"` and `end_date="2026-07-27"`.

## Output format

- List **every** slot from the tool JSON by center name and ID — do not drop times.
- Note weekends and dummy holidays are already excluded by the tool.
- Illustrative/dummy disclaimer and Absher verification line.

## Anti-patterns to avoid

- Calling `list_available_slots` before `list_centers_by_city`.
- Inventing `center_id` values not returned by `list_centers_by_city`.
- Filtering dates before resolving the city (centers must be looked up first).
- Omitting the illustrative/dummy disclaimer.
