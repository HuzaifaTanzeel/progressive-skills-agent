# Skill Library Regression Eval Report

Run date: 2026-07-15.
Order: iqama-renewal-status -> traffic-violation-lookup -> government-fee-payment-draft -> appointment-slot-finder.

Cross-skill routing cases are skipped until all referenced skills are present in the temp skills/ copy (dependency-aware filtering).

## Step summary

|   Step | Skills present                                                                                        | Added                        |   Cases run |   Passed |   Skipped |   Regressions |
|--------|-------------------------------------------------------------------------------------------------------|------------------------------|-------------|----------|-----------|---------------|
|      1 | iqama-renewal-status                                                                                  | (baseline)                   |           3 |        3 |         1 |             0 |
|      2 | iqama-renewal-status, traffic-violation-lookup                                                        | traffic-violation-lookup     |           6 |        6 |         2 |             0 |
|      3 | iqama-renewal-status, traffic-violation-lookup, government-fee-payment-draft                          | government-fee-payment-draft |          13 |       13 |         0 |             0 |
|      4 | iqama-renewal-status, traffic-violation-lookup, government-fee-payment-draft, appointment-slot-finder | appointment-slot-finder      |          17 |       17 |         0 |             0 |

## Regression details

No unexpected regressions detected.

### Step 1 skipped cases

- iqama-renewal-status:negative_routes_to_fee_draft (needs ['government-fee-payment-draft'])

### Step 2 skipped cases

- iqama-renewal-status:negative_routes_to_fee_draft (needs ['government-fee-payment-draft'])
- traffic-violation-lookup:negative_routes_to_fee_draft (needs ['government-fee-payment-draft'])

## Verdict

**0 unexpected regression(s).**
