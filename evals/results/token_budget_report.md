# Token Budget Report (Progressive Disclosure vs Monolithic)

Run date: 2026-07-15.
Encoding: tiktoken `cl100k_base` (OpenAI-compatible).

L1 index measured via ADK `format_skills_as_xml` — the always-on system-prompt catalog (progressive disclosure L1; not a list_skills tool response).

## Comparison

| Metric                                                   | Tokens (cl100k_base)   |
|----------------------------------------------------------|------------------------|
| L1 index (always-on system catalog, all 4 skills)        | 312                    |
| Largest L2 body (government-fee-payment-draft)           | 539                    |
| Typical progressive turn (L1 + largest L2)               | 851                    |
| Monolithic baseline (all L2 bodies + all references)     | 2243                   |
| Token reduction (monolithic -> progressive)              | 62.1%                  |
| Compact skill protocol (always injected with L1 catalog) | 167                    |

## Per-skill breakdown

| Skill                        |   L2 body |   References |   Combined |
|------------------------------|-----------|--------------|------------|
| appointment-slot-finder      |       355 |          557 |        912 |
| government-fee-payment-draft |       539 |            0 |        539 |
| iqama-renewal-status         |       183 |          235 |        418 |
| traffic-violation-lookup     |       224 |          150 |        374 |

## Note on scale

At only **4 skills**, token savings look modest compared to the Agent Skills whitepaper's ~50-skill Figure 8 example (~90%+ reduction). That is expected: progressive disclosure savings scale with library size. This demo proves the mechanism with real numbers at small scale, not the magnitude of a production catalog.
