**SUPERSEDED — see [sl_leak_audit_v2.md](../sl_leak_audit_v2.md). Retained for audit trail. Conclusions in this file are not current. Reason: generated while ingestion emitted one position per fill (46,520 rows instead of 7,277), invalidating all position-level conclusions.**

# SL Leak Audit — Refreshed Data

This audit was run only after the refreshed ingestion and Step 1 report were
complete. It uses the current `datasets/` files and the current inferred exit
type. Raw trader-registration values were not read into outputs.

## Scope and definition

The source schema has no observed exit-type field and no modification/update
timestamp. `exit_type` is therefore inferred at the existing one-price-point
tolerance:

- `sl_hit`: close price is within 1.0 of `slPrice`;
- `tp_hit`: close price is within 1.0 of `tpPrice`, unless already classified as
  `sl_hit`;
- otherwise `manual`.

This is an audit of whether `slPrice` can be treated as an as-of-open feature.
It does not assume that the recorded stop is the initial stop.

## 1. Exit-type split

| scope / inferred exit | n | SL set | TP set | mean gross loss/lot | mean rP/lot |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full / manual | 28,695 | 23.88% | 33.56% | 16.74 | 9.74 |
| Full / SL hit | 11,297 | 100.00% | 83.41% | 401.39 | 394.39 |
| Full / TP hit | 6,528 | 57.61% | 100.00% | -756.71 | -763.71 |
| Primary C53-C65 / manual | 11,896 | 23.70% | 31.89% | -1.63 | -8.63 |
| Primary C53-C65 / SL hit | 4,973 | 100.00% | 84.01% | 366.31 | 359.31 |
| Primary C53-C65 / TP hit | 2,575 | 64.47% | 100.00% | -675.04 | -682.04 |

The full refreshed corpus contains 46,520 position rows under the current
identifier interpretation. Primary-era exit-type counts are 11,896 manual,
4,973 inferred SL hits, and 2,575 inferred TP hits.

## 2. Stop/target direction and missingness checks

For the conventional interpretation, a BUY stop is below its open price and a
SELL stop is above it; TP direction is the reverse. The check is descriptive:
an apparent direction violation could also mean the platform records a moved
or trailing stop rather than an invalid order.

| scope | rows | SL null | TP null | non-null SL with conventional-direction violation | non-null TP with violation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full | 46,520 | 24,611 | 20,938 | 3,207 / 21,909 (14.64%) | 97 / 25,582 (0.38%) |
| Primary C53-C65 | 19,444 | 9,992 | 8,897 | 1,345 / 9,452 (14.23%) | 37 / 10,547 (0.35%) |

SL direction violations by inferred exit type in the full corpus are:

| inferred exit | non-null SL | direction violations |
| --- | ---: | ---: |
| manual | 6,851 | 743 |
| SL hit | 11,297 | 1,936 |
| TP hit | 3,761 | 528 |

The concentration of apparent violations among inferred SL hits is consistent
with a final/moved stop field, and is not consistent with treating every
non-null `slPrice` as a clean initial-stop snapshot. It is a semantic warning,
not by itself a proof that target information leaked into the feature.

## 3. Raw-fills recovery attempt

The refreshed raw trade files were checked for repeated event keys that could
recover modifications or partial closes. All candidate keys had zero duplicate
rows and zero duplicate groups:

| candidate recovery key | duplicate rows | duplicate groups |
| --- | ---: | ---: |
| `campaignId + positionId` | 0 | 0 |
| `campaignId + accountId + positionId` | 0 | 0 |
| `campaignId + accountId + openOrderId` | 0 | 0 |
| `campaignId + accountId + closeOrderId` | 0 | 0 |
| `campaignId + accountId + openDateTime + closeDateTime` | 0 | 0 |

Every campaign has one raw row per `positionId` under the refreshed files, so
the loader cannot recover a fill sequence or stop-modification sequence from
the raw trade files. No source column contains `exit`, `modif`, or `update`; the
only time fields are `openDateTime` and `closeDateTime`.

The replacement-file matched-row comparison gives this direct change audit:

| campaign | matched rows | `slPrice` cell changes | `tpPrice` cell changes | inferred exit labels changed |
| --- | ---: | ---: | ---: | ---: |
| C41 | 1,227 | 12 | 8 | 6 |
| C66 | 1,911 | 0 | 0 | 0 |

C41 also changes `reverseProfit` on all 1,227 matched rows. The C66 economic,
SL, TP, and inferred-exit values match after numeric type normalization.

## 4. Blast radius

| item | result |
| --- | --- |
| replacement campaigns inside primary era | None; C41 and C66 are excluded |
| direct primary-era SL/TP source-cell changes | None |
| direct replacement-driven inferred-exit changes | 6 rows in C41; 0 in C66 |
| current full-corpus inferred exits | 28,695 manual; 11,297 SL hit; 6,528 TP hit |
| current primary feature rows | 19,444 rows / 499 active accounts |
| prior published primary feature rows | 6,582 rows / 496 active accounts |
| causal initial-stop history recoverable | No |

The primary-era source files themselves were byte-identical to the intake
archive, so the direct replacement blast radius is outside C53-C65. However,
the refreshed identifier interpretation changes the full position table and
therefore changes the primary Stage 2 artifact substantially; this is an
ingestion/position-key blast radius, not an SL-cell-only effect.

## Verdict and required handling

1. The audit does not prove an SL target leak.
2. It does not certify `slPrice` as causal: the source has no modification
   history, and 14.64% of non-null stops fail the conventional direction check,
   including 1,936 inferred SL-hit rows.
3. `has_sl`, `sl_distance_pct`, `sl_usage_rate_5`, `manual_exit_rate_5`, and
   `sl_widening_delta` should remain **semantics-unresolved** until C22 supplies
   initial-order or stop-modification history. They should not be presented as
   confirmed as-of-open predictors on this export alone.
4. The refreshed position-key discrepancy must be resolved separately before
   comparing the refreshed 19,444-row Stage 2 results with the prior 6,582-row
   results as a pure dataset update.
