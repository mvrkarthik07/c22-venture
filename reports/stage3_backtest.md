# Stage 3 frozen V2 backtest

Data: repaired ingestion, 46,520 fills -> 7,277 positions.
Model: V2 admissible features; the four trader-history fields and all SL/TP-derived fields are excluded.
Target: reverseProfit per lot, with the $7 cost already included exactly once. Hurdle: 0.00.

## Frozen artifact and decision rule

Artifact: `artifacts/stage3_v2.json` (`stage3-v2-2026-08-20`).
Training window: C33-C52, n=694; evaluation: C53-C66, n=6,583.
Inner alpha CV selected `1000`; the frozen alpha is `3162.28`, one half-decade step more regularised.
Threshold grid: fixed -100 to 500 by 1; select maximum training mean rP/lot subject to n>=30. Selected score threshold: `-10.000`; effective execution threshold after the zero hurdle: `0.000`.
Training threshold support: n=88 (12.68%).
The selected-threshold support is reported exactly. Execution never fades a negative predicted rP, because the economic hurdle is exactly zero.
Default overrides, applied after the score threshold: abstain when `win_streak > 1` or `trades_per_hour > 60`.
Executable-grid re-selection (`0..500`, step 1): maximum training support is n=4 at threshold 0; n>=30 is satisfiable: **False**. The re-selected executable operating point is threshold 0 with n=4 and mean rP/lot 50.897, but it is ineligible under the pre-registered n>=30 floor. The mandated training split therefore cannot calibrate an executable threshold under that rule.

| threshold record | score threshold | effective runtime threshold | training n | status |
|---|---:|---:|---:|---|
| Current frozen artifact | -10 | 0 | 88 at offline selection; 4 at executable 0 | offline support-selected, not executable as selected |
| Executable-grid re-selection | 0 | 0 | 4 | no valid threshold: n>=30 floor fails |

## Common-split performance

Account CIs resample traderKey clusters; IP CIs are the secondary ipClusterId robustness check. Dollar totals below exclude corrupted C66; DO NOTHING acts on zero rows by construction.

| model / baseline | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI | total realized rP ($) |
|---|---:|---:|---:|---|---|---:|

### C53-C65 (6,582 positions)

| Model (overrides) | 177 | 2.69% | 10.433 | [-52.786, 72.331] | [-45.183, 66.523] | -3556.810 |
| Model (no overrides) | 183 | 2.78% | 10.452 | [-49.773, 70.475] | [-42.477, 64.403] | -3534.650 |
| DO NOTHING | 0 | 0.00% | 0.000 | [0.000, 0.000] | [0.000, 0.000] | 0.000 |
| FADE EVERYTHING, equal-weighted | 6582 | 100.00% | 5.436 | [-9.339, 20.713] | [-8.746, 20.384] | -12108.710 |
| FADE EVERYTHING, size-weighted | 6582 | 100.00% | -3.001 | [-11.031, 5.381] | [-11.081, 5.245] | -12108.710 |

Size-weighted dollar economics (C66 excluded):

| model / baseline | n | size-weighted mean rP/lot | account 95% CI | sum(amount) | total rP ($) |
|---|---:|---:|---|---:|---:|
| Model (overrides) | 177 | -33.849 | [-74.360, 1.166] | 105.08 | -3556.81 |
| DO NOTHING | 0 | 0.000 | [0.000, 0.000] | 0.00 | 0.00 |
| FADE EVERYTHING, equal-weighted | 6582 | -3.001 | [-11.031, 5.381] | 4034.37 | -12108.71 |
| FADE EVERYTHING, size-weighted | 6582 | -3.001 | [-11.031, 5.381] | 4034.37 | -12108.71 |

The model captures 29.37% of the fade-everything dollar loss while acting on 2.69% of positions and 2.60% of total amount (10.92x the position-coverage share; 11.28x the amount share).
Against DO NOTHING ($0 total rP), the model's total is $-3556.81: it does **not** beat DO NOTHING in absolute dollars.

Per-campaign model breakdown (default overrides):

| campaign | n acted | mean rP/lot | account 95% CI |
|---:|---:|---:|---|
| 53 | 5 | 173.557 | [48.512, 510.000] |
| 54 | 14 | 45.775 | [-71.219, 195.638] |
| 55 | 14 | -6.592 | [-375.126, 126.609] |
| 56 | 10 | 144.503 | [-111.370, 446.548] |
| 57 | 9 | -33.607 | [-220.217, 224.867] |
| 58 | 17 | -43.661 | [-256.267, 222.994] |
| 59 | 21 | -99.990 | [-221.813, -8.205] |
| 60 | 10 | -19.361 | [-294.341, 325.622] |
| 61 | 26 | -24.816 | [-138.010, 66.643] |
| 62 | 11 | 44.010 | [-99.998, 199.999] |
| 63 | 14 | -110.691 | [-296.714, 70.673] |
| 64 | 14 | 147.154 | [-89.265, 358.417] |
| 65 | 12 | 164.495 | [-66.447, 460.256] |

Single-best-campaign check: the best acted-on campaign by mean was C53.

| result | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI | total realized rP ($) |
|---|---:|---:|---:|---|---|---:|
| Model, best campaign C53 removed | 172 | 2.84% | 5.691 | [-60.200, 66.313] | [-54.817, 62.697] | -3702.070 |

### C53-C66 (6,583 positions; C66 excluded from dollar totals)

| Model (overrides) | 177 | 2.69% | 10.433 | [-52.786, 72.331] | [-45.183, 66.523] | -3556.810 |
| Model (no overrides) | 183 | 2.78% | 10.452 | [-49.773, 70.475] | [-42.477, 64.403] | -3534.650 |
| DO NOTHING | 0 | 0.00% | 0.000 | [0.000, 0.000] | [0.000, 0.000] | 0.000 |
| FADE EVERYTHING, equal-weighted | 6582 | 100.00% | 5.436 | [-9.339, 20.713] | [-8.746, 20.384] | -12108.710 |
| FADE EVERYTHING, size-weighted | 6582 | 100.00% | -3.001 | [-11.031, 5.381] | [-11.081, 5.245] | -12108.710 |

Size-weighted dollar economics (C66 excluded):

| model / baseline | n | size-weighted mean rP/lot | account 95% CI | sum(amount) | total rP ($) |
|---|---:|---:|---|---:|---:|
| Model (overrides) | 177 | -33.849 | [-74.360, 1.166] | 105.08 | -3556.81 |
| DO NOTHING | 0 | 0.000 | [0.000, 0.000] | 0.00 | 0.00 |
| FADE EVERYTHING, equal-weighted | 6582 | -3.001 | [-11.031, 5.381] | 4034.37 | -12108.71 |
| FADE EVERYTHING, size-weighted | 6582 | -3.001 | [-11.031, 5.381] | 4034.37 | -12108.71 |

The model captures 29.37% of the fade-everything dollar loss while acting on 2.69% of positions and 2.60% of total amount (10.92x the position-coverage share; 11.28x the amount share).
Against DO NOTHING ($0 total rP), the model's total is $-3556.81: it does **not** beat DO NOTHING in absolute dollars.

Per-campaign model breakdown (default overrides):

| campaign | n acted | mean rP/lot | account 95% CI |
|---:|---:|---:|---|
| 53 | 5 | 173.557 | [48.512, 510.000] |
| 54 | 14 | 45.775 | [-71.219, 195.638] |
| 55 | 14 | -6.592 | [-375.126, 126.609] |
| 56 | 10 | 144.503 | [-111.370, 446.548] |
| 57 | 9 | -33.607 | [-220.217, 224.867] |
| 58 | 17 | -43.661 | [-256.267, 222.994] |
| 59 | 21 | -99.990 | [-221.813, -8.205] |
| 60 | 10 | -19.361 | [-294.341, 325.622] |
| 61 | 26 | -24.816 | [-138.010, 66.643] |
| 62 | 11 | 44.010 | [-99.998, 199.999] |
| 63 | 14 | -110.691 | [-296.714, 70.673] |
| 64 | 14 | 147.154 | [-89.265, 358.417] |
| 65 | 12 | 164.495 | [-66.447, 460.256] |

Single-best-campaign check: the best acted-on campaign by mean was C53.

| result | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI | total realized rP ($) |
|---|---:|---:|---:|---|---|---:|
| Model, best campaign C53 removed | 172 | 2.84% | 5.691 | [-60.200, 66.313] | [-54.817, 62.697] | -3702.070 |

## C66 amount-collapse audit

C66 has 1911 fills collapsed to 1 position. The collapse currently uses `amount: sum` in `pipeline.to_positions()`; C66 therefore has position amount **462.30 lots** and total rP **$-4019.40**, or -8.694/lot.

This is a C66-specific corrupted test export: its 1,911 fill amounts sum to 462.30 lots, versus a maximum collapsed amount of 6.50 lots in primary C53-C65. The SUM aggregation remains the intended operation for ordinary partial-close fills, and no other primary-era multi-fill position exceeds 6.50 lots. C66 is excluded from every dollar total in this report; its per-lot observation remains in the 178-trade evaluation/power comparison.

## Expanding-window folds within C53-C65

Each fold fits V2, selects alpha and threshold using only its expanding training campaigns, then evaluates the next campaign block. Track A is trader-purged; Track B is the unpurged returning-trader analogue.

| track | fold | train n | validation n | threshold | alpha frozen | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| A | 1 | 2037 | 371 | 25.0 | 3162.2776601683795 | 15 | 4.04% | 128.165 | [-19.601, 350.132] | [-10.844, 351.410] |
| A | 2 | 2986 | 454 | 57.0 | 3162.2776601683795 | 8 | 1.76% | -134.945 | [-281.500, 0.371] | [-168.000, -59.000] |
| A | 3 | 4019 | 464 | 40.0 | 3162.2776601683795 | 83 | 17.89% | -15.609 | [-134.196, 107.650] | [-133.108, 101.895] |
| A | 4 | 4992 | 901 | 52.0 | 3162.2776601683795 | 8 | 0.89% | 257.934 | [-25.931, 552.238] | [-25.880, 586.200] |
| A | Pooled |  |  |  |  | 114 | 5.21% | 14.130 | [-80.926, 111.031] | [-77.725, 106.496] |
| A | Pooled DO NOTHING |  |  |  |  | 0 | 0.00% | 0.000 | [0.000, 0.000] | [0.000, 0.000] |
| A | Pooled FADE EVERYTHING equal |  |  |  |  | 2190 | 100.00% | 21.711 | [-3.458, 44.978] | [-2.586, 46.187] |
| A | Pooled FADE EVERYTHING size |  |  |  |  | 2190 | 100.00% | 8.282 | [-4.582, 21.592] | [-3.882, 21.210] |
| B | 1 | 2037 | 949 | 25.0 | 3162.2776601683795 | 53 | 5.58% | 49.201 | [-73.662, 188.866] | [-76.745, 199.785] |
| B | 2 | 2986 | 1033 | 57.0 | 3162.2776601683795 | 19 | 1.84% | -210.475 | [-479.776, -43.912] | [-473.419, -58.707] |
| B | 3 | 4019 | 973 | 40.0 | 3162.2776601683795 | 157 | 16.14% | 26.148 | [-75.667, 120.751] | [-66.241, 121.306] |
| B | 4 | 4992 | 1590 | 52.0 | 3162.2776601683795 | 8 | 0.50% | 257.934 | [-24.205, 554.967] | [-32.661, 554.121] |
| B | Pooled |  |  |  |  | 237 | 5.21% | 20.157 | [-52.517, 95.979] | [-55.847, 94.067] |
| B | Pooled DO NOTHING |  |  |  |  | 0 | 0.00% | 0.000 | [0.000, 0.000] | [0.000, 0.000] |
| B | Pooled FADE EVERYTHING equal |  |  |  |  | 4545 | 100.00% | 11.980 | [-5.507, 29.821] | [-4.959, 29.230] |
| B | Pooled FADE EVERYTHING size |  |  |  |  | 4545 | 100.00% | 0.071 | [-9.216, 9.239] | [-9.307, 8.999] |

## In-sample versus out-of-sample gap

| window | n | coverage | mean rP/lot | account 95% CI |
|---|---:|---:|---:|---|
| Training C33-C52 | 4 | 0.58% | 50.897 | [-62.924, 193.331] |
| Evaluation C53-C66 | 178 | 2.70% | 10.325 | [-52.204, 72.290] |

The acted-on mean changes by -40.571 rP/lot from training to evaluation. This gap is the relevant Stage 4 survival warning: the training result is not evidence of a deployable edge unless it survives the mandated evaluation interval and the fold checks.

## Decision-rule clarification

The exact boolean expression executed by `predict()` is:

```text
FADE = (score > max(selected_threshold, hurdle)) AND (win_streak <= 1) AND (trades_per_hour <= 60)
```


### Evaluation score distribution (frozen alpha)

Frozen alpha: `3162.28`; n=6,583; unique scores=6419; std=30.358107.

| min | p01 | p25 | p50 | p75 | p99 | max | std |
|---:|---:|---:|---:|---:|---:|---:|---:|
| -410.384603 | -131.786551 | -49.421374 | -29.922995 | -15.294056 | 27.530757 | 162.173027 | 30.358107 |

The predictions are not effectively constant: the standard deviation is about $30.36/lot and the central 98% span is broad, although most scores remain below the zero hurdle.

### Sequential evaluation gate counts

Counts are disjoint and applied in execution order. Raw NaN rows are also shown separately: imputation means they do not form an abstain gate, and V2 has no cold-start feature or cold-start override.

| gate | count | interpretation |
|---|---:|---|
| score fails effective threshold | 6399 | score <= 0.000 |
| win_streak > 1 after score pass | 0 | pre-registered override |
| trades_per_hour > 60 after prior gates | 6 | pre-registered override |
| NaN feature after prior gates | 90 | none excluded; imputer handles NaNs |
| FADE | 178 | 2.70% of evaluation |
| raw rows with >=1 NaN V2 feature | 5469 | diagnostic only; not an abstain gate |
| cold-start exclusion | 0 | V2 dropped history features and has no cold-start gate |

### Compact fixed threshold sweep

Training selection uses `train_n >= 30` and maximizes training mean rP/lot. This table retains only rows where training n changes, selection status changes, or the executable operating point 0 is reached. Evaluation coverage uses the zero economic hurdle and both abstain overrides, so negative grid values have the same effective execution threshold of zero.

| grid threshold | train n | train mean rP/lot | effective execution threshold | evaluation n acted | evaluation coverage | support eligible | selected |
|---:|---:|---:|---:|---:|---:|---|---|
| -100.0 | 694 | -29.854211 | 0.0 | 178 | 2.70% | yes | no |
| -97.0 | 693 | -28.536541 | 0.0 | 178 | 2.70% | yes | no |
| -71.0 | 692 | -28.525298 | 0.0 | 178 | 2.70% | yes | no |
| -67.0 | 691 | -28.666268 | 0.0 | 178 | 2.70% | yes | no |
| -65.0 | 690 | -28.556996 | 0.0 | 178 | 2.70% | yes | no |
| -63.0 | 689 | -28.660955 | 0.0 | 178 | 2.70% | yes | no |
| -62.0 | 688 | -28.397317 | 0.0 | 178 | 2.70% | yes | no |
| -61.0 | 687 | -27.985960 | 0.0 | 178 | 2.70% | yes | no |
| -58.0 | 685 | -27.237307 | 0.0 | 178 | 2.70% | yes | no |
| -55.0 | 684 | -27.334962 | 0.0 | 178 | 2.70% | yes | no |
| -54.0 | 682 | -27.226972 | 0.0 | 178 | 2.70% | yes | no |
| -53.0 | 681 | -26.109831 | 0.0 | 178 | 2.70% | yes | no |
| -52.0 | 678 | -24.826882 | 0.0 | 178 | 2.70% | yes | no |
| -51.0 | 674 | -24.399215 | 0.0 | 178 | 2.70% | yes | no |
| -50.0 | 671 | -24.624125 | 0.0 | 178 | 2.70% | yes | no |
| -49.0 | 669 | -24.648094 | 0.0 | 178 | 2.70% | yes | no |
| -48.0 | 668 | -24.426584 | 0.0 | 178 | 2.70% | yes | no |
| -47.0 | 666 | -24.288253 | 0.0 | 178 | 2.70% | yes | no |
| -46.0 | 664 | -24.032225 | 0.0 | 178 | 2.70% | yes | no |
| -45.0 | 661 | -22.093016 | 0.0 | 178 | 2.70% | yes | no |
| -44.0 | 660 | -21.635109 | 0.0 | 178 | 2.70% | yes | no |
| -41.0 | 658 | -22.392064 | 0.0 | 178 | 2.70% | yes | no |
| -40.0 | 655 | -20.725195 | 0.0 | 178 | 2.70% | yes | no |
| -38.0 | 648 | -20.144056 | 0.0 | 178 | 2.70% | yes | no |
| -37.0 | 641 | -20.752993 | 0.0 | 178 | 2.70% | yes | no |
| -36.0 | 639 | -20.974154 | 0.0 | 178 | 2.70% | yes | no |
| -35.0 | 636 | -21.057447 | 0.0 | 178 | 2.70% | yes | no |
| -34.0 | 630 | -19.584807 | 0.0 | 178 | 2.70% | yes | no |
| -33.0 | 622 | -19.976255 | 0.0 | 178 | 2.70% | yes | no |
| -32.0 | 620 | -20.361336 | 0.0 | 178 | 2.70% | yes | no |
| -31.0 | 613 | -20.573482 | 0.0 | 178 | 2.70% | yes | no |
| -30.0 | 611 | -21.194825 | 0.0 | 178 | 2.70% | yes | no |
| -29.0 | 609 | -21.179703 | 0.0 | 178 | 2.70% | yes | no |
| -28.0 | 607 | -21.584217 | 0.0 | 178 | 2.70% | yes | no |
| -27.0 | 606 | -20.955286 | 0.0 | 178 | 2.70% | yes | no |
| -26.0 | 604 | -20.942102 | 0.0 | 178 | 2.70% | yes | no |
| -23.0 | 602 | -20.642856 | 0.0 | 178 | 2.70% | yes | no |
| -22.0 | 601 | -20.997467 | 0.0 | 178 | 2.70% | yes | no |
| -21.0 | 600 | -20.841716 | 0.0 | 178 | 2.70% | yes | no |
| -20.0 | 590 | -21.259837 | 0.0 | 178 | 2.70% | yes | no |
| -19.0 | 575 | -19.368437 | 0.0 | 178 | 2.70% | yes | no |
| -18.0 | 573 | -20.245049 | 0.0 | 178 | 2.70% | yes | no |
| -17.0 | 566 | -19.797704 | 0.0 | 178 | 2.70% | yes | no |
| -16.0 | 541 | -23.871457 | 0.0 | 178 | 2.70% | yes | no |
| -15.0 | 462 | -5.427964 | 0.0 | 178 | 2.70% | yes | no |
| -14.0 | 345 | 0.796209 | 0.0 | 178 | 2.70% | yes | no |
| -13.0 | 271 | 4.655820 | 0.0 | 178 | 2.70% | yes | no |
| -12.0 | 251 | 5.202147 | 0.0 | 178 | 2.70% | yes | no |
| -11.0 | 179 | 9.810467 | 0.0 | 178 | 2.70% | yes | no |
| -10.0 | 88 | 9.977676 | 0.0 | 178 | 2.70% | yes | yes |
| -9.0 | 33 | -1.720762 | 0.0 | 178 | 2.70% | yes | no |
| -8.0 | 8 | 44.443583 | 0.0 | 178 | 2.70% | no | no |
| -7.0 | 6 | 76.710565 | 0.0 | 178 | 2.70% | no | no |
| -2.0 | 5 | 68.471377 | 0.0 | 178 | 2.70% | no | no |
| -1.0 | 4 | 50.896591 | 0.0 | 178 | 2.70% | no | no |
| 0.0 | 4 | 50.896591 | 0.0 | 178 | 2.70% | no | no |
| 4.0 | 3 | 71.696126 | 4.0 | 155 | 2.35% | no | no |
| 5.0 | 2 | 65.203641 | 5.0 | 147 | 2.23% | no | no |
| 9.0 | 1 | 193.331307 | 9.0 | 126 | 1.91% | no | no |
| 20.0 | 0 |  | 20.0 | 96 | 1.46% | no | no |

## Acting-subset power and coverage frontier

The default acting subsets are reported on both evaluation windows:

| window | n acted | distinct traderKey | distinct ipClusterId | campaigns |
|---|---:|---:|---:|---:|
| C53-C65 | 177 | 65 | 55 | 13 |
| C53-C66 | 178 | 66 | 56 | 14 |

MDE uses `MDE = 2.801585 * sigma * sqrt(DEFF / n)` for alpha=0.05 and power=0.80. Sigma is held at the primary-era C53-C65 outcome dispersion, so the calculation does not reuse the selected subset's realized variance: raw sigma=555.326284; winsorized 1%/99% sigma=482.451536.

### ICC, DEFF, and MDE recomputed on the acted-on positions

Unfloored MDEs show the direct negative-ICC calculation. Floored MDEs set ICC=max(ICC,0), hence DEFF=max(DEFF,1), and are the non-anti-conservative values.

| window | clustering scheme | effective clusters | mean cluster size | ICC | DEFF | unfloored raw / win. | floored raw / win. |
|---|---|---:|---:|---:|---:|---:|---:|
| C53-C65 | traderKey | 65 | 2.723 | -0.082534 | 0.857788 | $108.31 / $94.09 | $116.94 / $101.59 |
| C53-C65 | ipClusterId | 55 | 3.218 | -0.091150 | 0.797813 | $104.45 / $90.74 | $116.94 / $101.59 |
| C53-C66 | traderKey | 66 | 2.697 | -0.088830 | 0.849258 | $107.46 / $93.36 | $116.61 / $101.31 |
| C53-C66 | ipClusterId | 56 | 3.179 | -0.097521 | 0.787544 | $103.49 / $89.91 | $116.61 / $101.31 |

The negative acting-subset ICCs are treated as small-sample noise, not as information that increases power: mean cluster size is only about 2.7 and the unfloored DEFF<1 is anti-conservative. For comparison, the n=694 training MDE used positive primary estimates traderKey ICC=0.162328 / DEFF=1.753221 and ipClusterId ICC=0.096472 / DEFF=1.615386. The acting-subset calculation is therefore not directly comparable unless the ICC floor is applied.

The C53-C65 acted mean is +10.433 rP/lot (the C53-C66 mean is +10.325); both are far below even the floored MDEs and their account-clustered intervals include zero. The acting result is not distinguishable from zero at this sample size.

The fixed overrides impose a maximum actual acting coverage of 5616 / 6,583 = 85.31%; therefore the 100% row below means a hurdle low enough for every score to pass, while the overrides still leave some rows abstaining.

### Coverage-power frontier

Each row sweeps the effective score hurdle while retaining both abstain overrides. The requested target is rounded to the nearest position; achieved coverage is the actual post-override coverage. MDE uses the DEFF recomputed on that row's acted-on subset.

| target | effective hurdle | target n | n acted | achieved coverage | mean rP/lot | account 95% CI | account DEFF | account MDE unfloored raw / win. | account MDE floored raw / win. | IP DEFF | IP MDE unfloored raw / win. | IP MDE floored raw / win. |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1.0% | 27.477136 | 66 | 66 | 1.00% | 0.918 | [-116.231, 110.628] | 0.603 | $148.68 / $129.17 | $191.50 / $166.37 | 0.603 | $148.68 / $129.17 | $191.50 / $166.37 |
| 2.7% | 0.000000 | 178 | 178 | 2.70% | 10.325 | [-52.204, 72.290] | 0.849 | $107.46 / $93.36 | $116.61 / $101.31 | 0.788 | $103.49 / $89.91 | $116.61 / $101.31 |
| 5.0% | -10.278081 | 329 | 329 | 5.00% | 23.329 | [-27.046, 75.815] | 1.157 | $92.28 / $80.17 | $92.28 / $80.17 | 0.809 | $77.17 / $67.04 | $85.77 / $74.52 |
| 10.0% | -11.429065 | 658 | 658 | 10.00% | 21.691 | [-21.420, 66.439] | 1.382 | $71.30 / $61.95 | $71.30 / $61.95 | 1.134 | $64.59 / $56.11 | $64.59 / $56.11 |
| 25.0% | -15.318667 | 1646 | 1646 | 25.00% | 31.743 | [-0.608, 62.686] | 1.281 | $43.41 / $37.71 | $43.41 / $37.71 | 1.282 | $43.43 / $37.73 | $43.43 / $37.73 |
| 50.0% | -31.801081 | 3292 | 3292 | 50.01% | 21.666 | [-0.196, 43.667] | 1.352 | $31.53 / $27.39 | $31.53 / $27.39 | 1.252 | $30.34 / $26.36 | $30.34 / $26.36 |
| 100.0% | -410.384603 | 6583 | 5616 | 85.31% | 13.135 | [-2.928, 29.412] | 1.628 | $26.49 / $23.01 | $26.49 / $23.01 | 1.497 | $25.40 / $22.06 | $25.40 / $22.06 |

No coverage level clears its own MDE: **0 of 7 frontier rows** clears an unfloored MDE, and **0 of 7** clears a floored MDE. The realized point estimate is therefore below the corresponding 80%-power detection floor at every tested coverage.

The threshold sweep is intentionally inert over the support-eligible region: every support-eligible training threshold is negative and is overridden by the zero economic hurdle. This is a property of the design—acting is `score > 0` plus the two abstain overrides—not a pipeline defect.