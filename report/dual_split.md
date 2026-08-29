# Frozen V2: C22 common split versus Stage 2 own split

Date: 2026-08-25

The frozen V2 artifact was not refit. The same public `predict()` entry point,
20 features, frozen alpha `3162.27766017`, hurdle `0`, and both abstain
overrides were used throughout. Predictions were generated once on the full
7,277-position stream, then remasked to the evaluation rows defined by each
split.

The corrected C22-mandated common split excludes corrupted C66 from both
coverage and per-lot metrics: C53-C65, `n=6,582`. The original Stage 2
walk-forward scope is the same C53-C65 window, with four expanding campaign
folds:

| fold | training campaigns used by the original fold definition | validation campaigns | Track A retained n | Track B retained n |
|---:|---|---|---:|---:|
| 1 | C53-C56 | C57-C58 | 371 | 949 |
| 2 | C53-C58 | C59-C60 | 454 | 1,033 |
| 3 | C53-C60 | C61-C62 | 464 | 973 |
| 4 | C53-C62 | C63-C65 | 901 | 1,590 |
| **Pooled** | — | C57-C65 | **2,190** | **4,545** |

Track A applies the original traderKey purge plus targeted synchrony-IP
purging. Track B applies no identity purge. The fold training campaigns above
are reported for split provenance only; they were not used to fit a new model
in this report.

EW/lot is the arithmetic mean of `reverseProfit / amount`. SW/lot is total
`reverseProfit` divided by total lots. Every interval below is a 95% bootstrap
with 2,000 replicates, seed 7, resampling `accountId` clusters and retaining
all selected trades for each sampled account. With zero acted rows, the
interval is `[0.000, 0.000]` by construction.

C66 is excluded from the common split's numerator, denominator, per-lot
metrics, and dollar totals. C66 is not present in the Stage 2 own split, so
that exclusion is vacuous there. The previously emitted common-split row
`178/6,583`, EW `10.3253`, SW `-13.3530`, is superseded by the C53-C65 row
below; the `-13.3530` value divided all C66-included realized reverseProfit by
all C66-included lots while retaining a C66-excluded dollar total.

## Side-by-side headline results

| split | evaluation rows | acted n | coverage | EW/lot (accountId 95% CI) | SW/lot (accountId 95% CI) | dollar total |
|---|---:|---:|---:|---|---|---:|
| **Common split (C22-mandated; C66 excluded)** | 6,582 | 177 | 2.6892% | 10.4327 [-46.117, 66.826] | -33.8486 [-70.260, 2.964] | -$3,556.81 |
| **Own split (Stage 2 walk-forward) — Track A pooled** | 2,190 | 6 | 0.2740% | 83.0047 [-117.7662, 289.4423] | -9.6772 [-76.0778, 132.0286] | -$48.87 |
| **Own split (Stage 2 walk-forward) — Track B pooled** | 4,545 | 134 | 2.9483% | -7.5730 [-70.3750, 61.3823] | -55.4091 [-94.2404, -15.7822] | -$4,724.18 |

The two own-split rows are separate tracks, not additive subsets. Track A is
the purged unseen-trader sensitivity; Track B is the unpurged returning-trader
analogue.

## Common split (C22-mandated): per-campaign breakdown

The C66 row is displayed for auditability but is excluded from the corrected
common-split aggregate and its acted-lot base.

| campaign | evaluation n | acted n (coverage) | EW/lot [95% CI] | SW/lot [95% CI] | dollar total |
|---:|---:|---:|---|---|---:|
| C53 | 519 | 5 (0.96%) | 173.557 [62.119, 411.750] | 103.021 [37.091, 228.277] | $145.26 |
| C54 | 509 | 14 (2.75%) | 45.775 [-67.989, 195.326] | 11.617 [-42.598, 86.784] | $88.17 |
| C55 | 485 | 14 (2.89%) | -6.592 [-347.710, 109.515] | 81.985 [-100.870, 165.357] | $501.75 |
| C56 | 524 | 10 (1.91%) | 144.503 [-90.793, 411.359] | 91.955 [-62.566, 371.856] | $432.19 |
| C57 | 511 | 9 (1.76%) | -33.607 [-207.456, 198.640] | -49.385 [-222.167, 321.177] | -$180.75 |
| C58 | 438 | 17 (3.88%) | -43.661 [-247.919, 199.595] | -145.371 [-253.513, -70.761] | -$1,868.02 |
| C59 | 552 | 21 (3.80%) | -99.990 [-212.512, -13.058] | -87.301 [-208.358, 9.142] | -$1,577.53 |
| C60 | 481 | 10 (2.08%) | -19.361 [-265.068, 241.071] | -45.824 [-204.030, -17.647] | -$395.46 |
| C61 | 564 | 26 (4.61%) | -24.816 [-127.849, 64.762] | -42.242 [-121.689, 9.981] | -$515.77 |
| C62 | 409 | 11 (2.69%) | 44.010 [-89.949, 185.426] | -18.184 [-88.369, 81.692] | -$133.11 |
| C63 | 584 | 14 (2.40%) | -110.691 [-285.042, 69.215] | -83.173 [-276.389, -13.290] | -$596.35 |
| C64 | 496 | 14 (2.82%) | 147.154 [-85.793, 363.677] | -0.253 [-112.668, 171.607] | -$2.09 |
| C65 | 510 | 12 (2.35%) | 164.495 [-55.792, 421.499] | 76.963 [-72.802, 310.417] | $544.90 |
| C66 | 1 | 1 (100.00%) | -8.694 [-8.694, -8.694] | -8.694 [-8.694, -8.694] | **excluded** |

## Own split (Stage 2 walk-forward): per-fold breakdown

### Track A — purged

| fold | retained n | acted n | coverage | EW/lot [95% CI] | SW/lot [95% CI] | dollar total |
|---:|---:|---:|---:|---|---|---:|
| 1 | 371 | 1 | 0.2695% | -325.080 [-325.080, -325.080] | -325.080 [-325.080, -325.080] | -$81.27 |
| 2 | 454 | 0 | 0.0000% | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | $0.00 |
| 3 | 464 | 3 | 0.6466% | 155.885 [-0.346, 423.000] | 18.300 [-0.346, 423.000] | $54.90 |
| 4 | 901 | 2 | 0.2220% | 177.727 [-50.545, 406.000] | -12.500 [-50.545, 406.000] | -$22.50 |
| **Pooled** | **2,190** | **6** | **0.2740%** | **83.005 [-117.766, 289.442]** | **-9.677 [-76.078, 132.029]** | **-$48.87** |

### Track B — unpurged

| fold | retained n | acted n | coverage | EW/lot [95% CI] | SW/lot [95% CI] | dollar total |
|---:|---:|---:|---:|---|---|---:|
| 1 | 949 | 26 | 2.7397% | -40.181 [-188.010, 137.967] | -124.093 [-213.543, -32.319] | -$2,048.77 |
| 2 | 1,033 | 31 | 3.0010% | -73.981 [-175.846, 18.206] | -73.895 [-162.767, -5.777] | -$1,972.99 |
| 3 | 973 | 37 | 3.8027% | -4.354 [-79.580, 77.470] | -33.225 [-86.449, 11.332] | -$648.88 |
| 4 | 1,590 | 40 | 2.5157% | 62.111 [-82.052, 206.227] | -2.377 [-78.260, 86.370] | -$53.54 |
| **Pooled** | **4,545** | **134** | **2.9483%** | **-7.573 [-70.375, 61.382]** | **-55.409 [-94.240, -15.782]** | **-$4,724.18** |

## Own split: per-campaign breakdown

The Track A denominator is the retained, purged row count. The Track B
denominator is the unpurged row count. A dash means that track had no acted
rows in that campaign.

### Track A — purged

| campaign | retained n | acted n (coverage) | EW/lot [95% CI] | SW/lot [95% CI] | dollar total |
|---:|---:|---:|---|---|---:|
| C57 | 187 | 0 (0.00%) | — | — | $0.00 |
| C58 | 184 | 1 (0.54%) | -325.080 [-325.080, -325.080] | -325.080 [-325.080, -325.080] | -$81.27 |
| C59 | 212 | 0 (0.00%) | — | — | $0.00 |
| C60 | 242 | 0 (0.00%) | — | — | $0.00 |
| C61 | 244 | 1 (0.41%) | 45.000 [45.000, 45.000] | 45.000 [45.000, 45.000] | $13.50 |
| C62 | 220 | 2 (0.91%) | 211.327 [-0.346, 423.000] | 15.333 [-0.346, 423.000] | $41.40 |
| C63 | 251 | 0 (0.00%) | — | — | $0.00 |
| C64 | 314 | 1 (0.32%) | -50.545 [-50.545, -50.545] | -50.545 [-50.545, -50.545] | -$83.40 |
| C65 | 336 | 1 (0.30%) | 406.000 [406.000, 406.000] | 406.000 [406.000, 406.000] | $60.90 |

### Track B — unpurged

| campaign | retained n | acted n (coverage) | EW/lot [95% CI] | SW/lot [95% CI] | dollar total |
|---:|---:|---:|---|---|---:|
| C57 | 511 | 9 (1.76%) | -33.607 [-207.456, 198.640] | -49.385 [-222.167, 321.177] | -$180.75 |
| C58 | 438 | 17 (3.88%) | -43.661 [-247.919, 199.595] | -145.371 [-253.513, -70.761] | -$1,868.02 |
| C59 | 552 | 21 (3.80%) | -99.990 [-212.512, -13.058] | -87.301 [-208.358, 9.142] | -$1,577.53 |
| C60 | 481 | 10 (2.08%) | -19.361 [-265.068, 241.071] | -45.824 [-204.030, -17.647] | -$395.46 |
| C61 | 564 | 26 (4.61%) | -24.816 [-127.849, 64.762] | -42.242 [-121.689, 9.981] | -$515.77 |
| C62 | 409 | 11 (2.69%) | 44.010 [-89.949, 185.426] | -18.184 [-88.369, 81.692] | -$133.11 |
| C63 | 584 | 14 (2.40%) | -110.691 [-285.042, 69.215] | -83.173 [-276.389, -13.290] | -$596.35 |
| C64 | 496 | 14 (2.82%) | 147.154 [-85.793, 363.677] | -0.253 [-112.668, 171.607] | -$2.09 |
| C65 | 510 | 12 (2.35%) | 164.495 [-55.792, 421.499] | 76.963 [-72.802, 310.417] | $544.90 |

## No-refit feasibility

Strict no-refit evaluation is possible for this request. The original split
defines evaluation membership separately from model fitting: campaign-block
membership and Track A/B purge masks can be computed from `splits.py`, while
the frozen `predict()` output supplies the unchanged decisions and realized
outcomes. The evaluation-only procedure therefore remasks the frozen output;
it does not call `_fit_artifact`, `_fold_artifact`, alpha selection, threshold
selection, or any other refit path.

This is deliberately **not** the original Stage 2 fold-refit estimand. The
historical Stage 2 walk-forward report fitted a fresh model and selected an
alpha/threshold inside each fold. Reproducing those historical numbers while
also forbidding refit would be contradictory. No minimal-deviation alternative
was selected because the requested frozen-model evaluation is directly
defined and executable.
