# Common-split baselines

Window: C53-C65, 6,582 positions. C66 is the corrupted single-position export
(1,911 fills collapsed to 462.30 lots) and is excluded from numerator,
denominator, per-lot summaries, and dollar totals.

## FADE EVERYTHING

FADE EVERYTHING acts on every corrected evaluation row: n=6,582 and
coverage=100.00%. There were no additional data-quality exclusions. On the
6,582-row window, EW is 5.436/lot and SW is -3.001/lot. The account-clustered
95% CIs are [-8.572, 20.475] and [-10.493, 4.840], respectively. The C66-excluded
dollar total is **-$12,108.71** on 4,034.37 non-C66 lots.

| campaign | n | EW/lot | EW account 95% CI | SW/lot | dollar P&L (C66 excluded) |
|---:|---:|---:|---|---:|---:|
| C53 | 519 | 74.333 | [4.126, 143.905] | 31.161 | $5,527.39 |
| C54 | 509 | -7.213 | [-50.577, 34.884] | -13.181 | -$3,904.79 |
| C55 | 485 | -55.639 | [-103.681, -7.245] | -20.682 | -$4,666.24 |
| C56 | 524 | -50.745 | [-98.396, -3.398] | -28.584 | -$9,279.72 |
| C57 | 511 | 22.530 | [-23.357, 75.433] | 2.857 | $755.15 |
| C58 | 438 | 46.680 | [-10.121, 112.538] | 4.881 | $1,337.82 |
| C59 | 552 | 51.859 | [-4.305, 117.752] | 18.957 | $5,734.56 |
| C60 | 481 | 34.029 | [-18.185, 95.549] | 10.132 | $3,052.23 |
| C61 | 564 | 4.522 | [-34.954, 46.342] | 5.250 | $1,988.53 |
| C62 | 409 | -13.442 | [-45.230, 18.753] | -22.533 | -$8,804.62 |
| C63 | 584 | -20.719 | [-69.431, 26.133] | -6.413 | -$2,294.07 |
| C64 | 496 | -13.305 | [-53.586, 28.133] | 3.441 | $1,249.63 |
| C65 | 510 | -1.681 | [-47.143, 41.630] | -7.421 | -$2,804.58 |
| C66 | 1 | -8.694 | [-8.694, -8.694] | -8.694 | excluded |
| **Total** | **6,582** | **5.436** | **[-8.572, 20.475]** | **-3.001** | **-$12,108.71** |

## Three-row common-split comparison

EW and SW use the same C66-excluded 6,582 evaluation rows as the dollar P&L
for all three policies.

| policy | acted n | coverage | EW/lot | EW account 95% CI | SW/lot | SW account 95% CI | dollar P&L |
|---|---:|---:|---:|---|---:|---|---:|
| DO NOTHING | 0 | 0.00% | 0.000 | [0.000, 0.000] by construction | 0.000 | [0.000, 0.000] by construction | $0.00 |
| MODEL | 177 | 2.6892% | 10.433 | [-46.117, 66.826] | -33.849 | [-70.260, 2.964] | -$3,556.81 |
| FADE EVERYTHING | 6,582 | 100.00% | 5.436 | [-8.572, 20.475] | -3.001 | [-10.493, 4.840] | -$12,108.71 |

The corrected model row contains the 177 non-C66 acted trades and -$3,556.81.
DO NOTHING, MODEL, and FADE EVERYTHING use the identical C66 exclusion for
coverage, EW, SW, dollar totals, and lot bases.

## Enforcement and clustering

C66 exclusion is centralized in
`stage3_model.py:_common_split_economic()` and is used by the Stage 3 report's
C53-C66 economic subset. The calculations in this report apply that same
`campaignId != 66` rule to all three dollar totals. The account intervals use
the fixed-seed accountId bootstrap:
2,000 resamples, seed 7. The full-evaluation set has 496 distinct accounts
with 1/11/63 trades per account (min/median/max); the 177 non-C66 model-acted
set has 92 accounts with 1/1/8 trades per account.
