# Complete per-campaign Stage 3 breakdown

Date: 2026-08-26

This report uses the public `predict()` entry point on the full collapsed
7,277-position stream. V2 uses `artifacts/stage3_v2.json`; V3 uses the clean
9-feature artifact `artifacts/stage3_v3_clean.json` on branch
`stage3-tp-remediation`. No refit was performed.

EW is the arithmetic mean of `reverseProfit / amount`. SW is total
`reverseProfit` divided by total acted lots. All intervals use 2,000
accountId-clustered bootstrap replicates with seed 7. Under the corrected
convention, C66 is excluded from coverage, EW, SW, dollar P&L, and acted-lot
bases. C66 is retained below as a separately flagged diagnostic row. It is a
one-position corrupted export with 462.30 summed lots.

## Headline context

| model | eval trades | acted | coverage | acted lots | EW/lot [95% accountId CI] | SW/lot | dollar P&L | acted accounts |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| V2 | 6,582 | 177 | 2.6892% | 105.08 | 10.433 [-46.117, 66.826] | -33.849 [-70.260, 2.964] | -$3,556.81 | 92 |
| V3 clean | 6,582 | 5 | 0.0760% | 1.28 | 243.012 [-78.775, 572.100] | 228.180 [-133.868, 655.217] | +$292.07 | 5 |

## One row per campaign

The coverage percentage is within the campaign. A dash means zero acted rows;
there is then no EW/SW estimate or acted account count. The dollar value for
C66 is marked excluded rather than included in the total.

| campaign | n trades | V2 acted | V2 coverage | V2 lots | V2 EW/lot [95% CI] | V2 SW/lot | V2 dollars | V2 accounts | V3 acted | V3 coverage | V3 lots | V3 EW/lot [95% CI] | V3 SW/lot | V3 dollars | V3 accounts | flag / note |
|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| C53 | 519 | 5 | 0.96% | 1.41 | 173.557 [62.119, 411.750] | 103.021 | $145.26 | 4 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | V2 highest acted-campaign EW; V3 has no acted rows |
| C54 | 509 | 14 | 2.75% | 7.59 | 45.775 [-67.989, 195.326] | 11.617 | $88.17 | 11 | 1 | 0.20% | 0.40 | 745.250 [745.250, 745.250] | 745.250 | $298.10 | 1 | — |
| C55 | 485 | 14 | 2.89% | 6.12 | -6.592 [-347.710, 109.515] | 81.985 | $501.75 | 6 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C56 | 524 | 10 | 1.91% | 4.70 | 144.503 [-90.793, 411.359] | 91.955 | $432.19 | 7 | 1 | 0.19% | 0.10 | 482.000 [482.000, 482.000] | 482.000 | $48.20 | 1 | — |
| C57 | 511 | 9 | 1.76% | 3.66 | -33.607 [-207.456, 198.640] | -49.385 | -$180.75 | 7 | 1 | 0.20% | 0.26 | -360.000 [-360.000, -360.000] | -360.000 | -$93.60 | 1 | — |
| C58 | 438 | 17 | 3.88% | 12.85 | -43.661 [-247.919, 199.595] | -145.371 | -$1,868.02 | 10 | 1 | 0.23% | 0.37 | -58.189 [-58.189, -58.189] | -58.189 | -$21.53 | 1 | — |
| C59 | 552 | 21 | 3.80% | 18.07 | -99.990 [-212.512, -13.058] | -87.301 | -$1,577.53 | 13 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C60 | 481 | 10 | 2.08% | 8.63 | -19.361 [-265.068, 241.071] | -45.824 | -$395.46 | 6 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C61 | 564 | 26 | 4.61% | 12.21 | -24.816 [-127.849, 64.762] | -42.242 | -$515.77 | 11 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C62 | 409 | 11 | 2.69% | 7.32 | 44.010 [-89.949, 185.426] | -18.184 | -$133.11 | 8 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C63 | 584 | 14 | 2.40% | 7.17 | -110.691 [-285.042, 69.215] | -83.173 | -$596.35 | 9 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C64 | 496 | 14 | 2.82% | 8.27 | 147.154 [-85.793, 363.677] | -0.253 | -$2.09 | 9 | 0 | 0.00% | 0.00 | — | — | $0.00 | 0 | — |
| C65 | 510 | 12 | 2.35% | 7.08 | 164.495 [-55.792, 421.499] | 76.963 | $544.90 | 7 | 1 | 0.20% | 0.15 | 406.000 [406.000, 406.000] | 406.000 | $60.90 | 1 | — |
| C66 | 1 | 1 | 100.00% | 462.30 | -8.694 [-8.694, -8.694] | -8.694 | **excluded** | 1 | 1 | 100.00% | 462.30 | -8.694 [-8.694, -8.694] | -8.694 | **excluded** | 1 | **EXCLUDED FROM DOLLAR TOTALS**; corrupted single-position export |

## Leave-one-campaign-out sensitivity — V2

Each row removes the named campaign from the acted set, then recomputes EW and
SW. CIs are recomputed with the same accountId bootstrap. The leave-one table
below is the previously emitted sensitivity diagnostic and retains C66 unless
C66 is the campaign dropped; it is not part of the corrected C66-excluded
headline aggregate above.

| dropped campaign | remaining acted n | EW/lot [95% accountId CI] | SW/lot [95% accountId CI] |
|---:|---:|---|---|
| C53 | 173 | 5.608 [-48.422, 61.513] | -13.643 [-63.177, -5.563] |
| C54 | 164 | 7.299 [-50.967, 69.540] | -13.692 [-64.960, -6.074] |
| C55 | 164 | 11.769 [-42.136, 69.395] | -14.393 [-69.613, -8.097] |
| C56 | 168 | 2.339 [-53.983, 62.758] | -14.233 [-66.429, -7.115] |
| C57 | 169 | 12.665 [-41.752, 70.249] | -13.119 [-60.013, -5.021] |
| C58 | 161 | 16.026 [-37.235, 75.837] | -10.294 [-48.196, 9.750] |
| C59 | 157 | 25.081 [-30.040, 90.941] | -10.920 [-51.047, 6.840] |
| C60 | 168 | 12.092 [-40.898, 72.885] | -12.851 [-61.253, -0.357] |
| C61 | 152 | 16.336 [-46.437, 77.681] | -12.718 [-60.539, -3.034] |
| C62 | 167 | 8.107 [-44.035, 68.951] | -13.290 [-62.252, -2.083] |
| C63 | 164 | 20.656 [-30.226, 79.201] | -12.459 [-54.651, 1.019] |
| C64 | 164 | -1.355 [-52.137, 54.392] | -13.547 [-65.195, -4.704] |
| C65 | 166 | -0.819 [-51.506, 52.620] | -14.494 [-67.853, -7.665] |
| C66 | 177 | 10.433 [-46.117, 66.826] | -33.849 [-70.260, 2.964] |

## Leave-one-campaign-out sensitivity — V3 clean

| dropped campaign | remaining acted n | EW/lot [95% accountId CI] | SW/lot [95% accountId CI] |
|---:|---:|---|---|
| C53 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C54 | 5 | 92.223 [-169.015, 353.461] | -8.691 [-185.715, 174.419] |
| C55 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C56 | 5 | 144.873 [-169.015, 458.761] | -8.146 [-120.113, 473.789] |
| C57 | 5 | 313.273 [54.447, 572.100] | -7.843 [-8.681, 655.217] |
| C58 | 5 | 252.911 [-68.946, 572.100] | -8.000 [-34.368, 655.217] |
| C59 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C60 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C61 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C62 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C63 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C64 | 6 | 201.061 [-79.386, 487.875] | -8.040 [-71.685, 481.559] |
| C65 | 5 | 160.073 [-159.116, 531.912] | -8.174 [-103.055, 489.832] |
| C66 | 5 | 243.012 [-78.775, 572.100] | 228.180 [-133.868, 655.217] |

## What the sensitivity says

- V2 C53 contributes only `n=5` of 178 acted trades, but it is the highest
  acted-campaign EW at `173.557`/lot. Dropping it changes V2 EW from `10.325`
  to `5.608`/lot; the point estimate remains positive, while V2 SW changes
  from `-13.353` to `-13.643`/lot.
- V3 has `n=0` acted trades in C53, so dropping C53 leaves V3 unchanged at
  EW `201.061`/lot and SW `-8.040`/lot.
- C66 is not a normal campaign comparison: its one acted trade carries
  `462.30` lots. The old full-scope headline changed V2 SW from `-13.353` to
  `-33.849`/lot and V3 SW from `-8.040` to `228.180`/lot when C66 was dropped.
  Under the corrected convention, the latter values are already the headline
  V2/V3 SW values; the historical leave-one table is retained as provenance.

## First Git-recorded provenance of the exclusions and overrides

The first Git-tracked Stage 3 occurrence of all three rules is the same
submission commit:

`06efdd595f890857a8ece7f587be5d35f83644c0` — commit date
`2026-08-21 22:03:09 +0800` (author date `2026-08-21 21:43:26 +0800`),
**Stage 3 submission: frozen V2 model, backtest, trials log, power analysis,
brief**.

| rule | first tracked location in that commit | evidence |
|---|---|---|
| C66 exclusion from dollar totals | `stage3_model.py` lines 1112-1116 in the committed file | the C53-C66 economic subset applies `campaignId != 66`; the committed report also states C66 is excluded from every dollar total |
| abstain override 1 | `stage3_model.py` lines 369 and 549-556 | artifact metadata lists `win_streak > 1`; `predict()` applies it after the score/hurdle gate |
| abstain override 2 | `stage3_model.py` lines 369 and 549-556 | artifact metadata lists `trades_per_hour > 60`; `predict()` applies it after the score/hurdle gate |

The committed report records the two overrides as default/pre-registered and
prints the exact boolean decision rule. Git history contains no earlier
tracked Stage 3 model commit than `06efdd5`, so this is the first recorded
date, not a claim about an unrecorded design discussion before that commit.
