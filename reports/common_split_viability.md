# Stage 3 common-split viability

Date: 20 Aug 2026  
Data: repaired ingestion (`46,520` fills -> `7,277` positions)  
Common split mandated by C22: fit/select on campaigns `<= C52`; evaluate on
`C53-C66`.

## 1. Common split

The split is by campaign ID and includes C41 in the training range and C66 in
the evaluation range, as required.

| window | raw fills | positions | distinct accounts | campaigns |
|---|---:|---:|---:|---|
| train (`C33-C52`) | 25,165 | 694 | 330 | 20 (`C33-C52`) |
| evaluate (`C53-C66`) | 21,355 | 6,583 | 496 | 14 (`C53-C66`) |

The evaluation positions are the repaired primary-era `6,582` positions plus
the one-position C66 test campaign.

## 2. Evaluation-window cold starts

Cold start is defined on keyed evaluation positions as a non-null `traderKey`
with zero appearances in any training campaign `C33-C52`. Missing `traderKey`
rows are reported separately because they have no identity history to query.

| campaign | eval positions | keyed positions | cold keyed positions | cold rate among keyed | missing traderKey | strict unavailable rate |
|---:|---:|---:|---:|---:|---:|---:|
| C53 | 519 | 519 | 365 | 70.33% | 0 | 70.33% |
| C54 | 509 | 509 | 353 | 69.35% | 0 | 69.35% |
| C55 | 485 | 485 | 325 | 67.01% | 0 | 67.01% |
| C56 | 524 | 509 | 398 | 78.19% | 15 | 78.82% |
| C57 | 511 | 511 | 357 | 69.86% | 0 | 69.86% |
| C58 | 438 | 438 | 268 | 61.19% | 0 | 61.19% |
| C59 | 552 | 552 | 432 | 78.26% | 0 | 78.26% |
| C60 | 481 | 481 | 416 | 86.49% | 0 | 86.49% |
| C61 | 564 | 564 | 474 | 84.04% | 0 | 84.04% |
| C62 | 409 | 409 | 370 | 90.46% | 0 | 90.46% |
| C63 | 584 | 584 | 517 | 88.53% | 0 | 88.53% |
| C64 | 496 | 496 | 457 | 92.14% | 0 | 92.14% |
| C65 | 510 | 510 | 481 | 94.31% | 0 | 94.31% |
| C66 | 1 | 1 | 1 | 100.00% | 0 | 100.00% |
| **total** | **6,583** | **6,568** | **5,214** | **79.39%** | **15** | **79.44%** |

Only `1,354` keyed evaluation positions have a traderKey that appeared in the
training window. Thus `prior_campaigns` is numerically available, but it is
zero for most evaluation rows. The Family G features are also numerically
populated through the population fallback/shrinkage path, but for roughly
79% of evaluation positions they cannot be trader-specific because there is no
prior keyed appearance. This is a major viability constraint on interpreting
`trader_prior_tilt`, `trader_prior_sl_discipline`, and
`trader_prior_survival` under the common split.

## 3. C66 check

| campaign | raw rows/fills | positions | distinct accounts | status |
|---:|---:|---:|---:|---|
| C66 | 1,911 | 1 | 1 | still an n=1 test campaign |

C66 is inside the mandated evaluation window but remains a one-position test
campaign after the replacement file was loaded and collapsed.

## 4. Feature distribution shift

Statistics use the 28 frozen Stage 2 features in `features_v2.csv`. Means and
standard deviations treat boolean features as `0/1`. `challenge_type` is
categorical, so its mean/std are not defined; its coverage is still reported.
Coverage is the non-NaN fraction. A coverage collapse is flagged when
evaluation coverage falls by at least 10 percentage points from training.

| feature | train mean | train std | train coverage | eval mean | eval std | eval coverage | flag |
|---|---:|---:|---:|---:|---:|---:|---|
| `loss_streak` | 0.110951 | 0.349101 | 100.00% | 0.572080 | 0.980635 | 100.00% | — |
| `win_streak` | 0.119597 | 0.411020 | 100.00% | 0.530153 | 0.971312 | 100.00% | — |
| `pnl_ewm` | -4.527752 | 84.697104 | 100.00% | -5.238281 | 55.207234 | 100.00% | — |
| `lot_zscore` | 0.317002 | 2.764533 | 1.30% | 0.259038 | 2.813655 | 36.12% | — |
| `amount` | 5.839726 | 8.508853 | 100.00% | 0.683073 | 5.720951 | 100.00% | — |
| `size_after_loss_delta` | -0.463889 | 3.896691 | 1.30% | -0.005554 | 0.562081 | 19.99% | — |
| `has_sl` | 0.985591 | 0.119256 | 100.00% | 0.761659 | 0.426101 | 100.00% | — |
| `has_tp` | 0.988473 | 0.106822 | 100.00% | 0.800395 | 0.399734 | 100.00% | — |
| `sl_distance_pct` | 0.001346 | 0.002820 | 98.56% | 0.001365 | 0.012901 | 76.17% | **COLLAPSE (-22.39pp)** |
| `sl_usage_rate_5` | 1.000000 | 0.000000 | 1.30% | 0.777089 | 0.278768 | 36.53% | — |
| `manual_exit_rate_5` | 0.740741 | 0.277778 | 1.30% | 0.680076 | 0.275501 | 36.53% | — |
| `pnl_pct` | -0.002747 | 0.062301 | 100.00% | -0.008029 | 0.065596 | 100.00% | — |
| `dd_from_peak_pct` | 0.011929 | 0.047850 | 100.00% | 0.028506 | 0.059969 | 100.00% | — |
| `trade_index` | 1.260807 | 0.595551 | 100.00% | 4.066839 | 4.774123 | 100.00% | — |
| `log_dt_close` | 2.774739 | 4.084370 | 19.60% | 3.647188 | 3.645036 | 67.83% | — |
| `trades_per_hour` | 48.870503 | 23.073053 | 100.00% | 26.707837 | 28.516718 | 100.00% | — |
| `prior_campaigns` | 0.498559 | 1.057849 | 100.00% | 1.732797 | 2.388472 | 100.00% | — |
| `prior_campaigns_x_loss_streak_ge_2` | 0.007205 | 0.125782 | 100.00% | 0.249430 | 1.101809 | 100.00% | — |
| `shared_ip` | 0.949568 | 0.218993 | 100.00% | 0.855233 | 0.351892 | 100.00% | — |
| `ip_cluster_size` | 22.530523 | 18.833189 | 99.14% | 12.350944 | 16.101419 | 99.77% | — |
| `challenge_type` | n/a | n/a | 100.00% | n/a | n/a | 100.00% | categorical |
| `gold_vol_prev_day` | 0.030031 | 0.021350 | 100.00% | 0.023012 | 0.009961 | 100.00% | — |
| `sl_widening_delta` | -0.000235 | 0.000803 | 1.30% | 0.000216 | 0.001877 | 23.73% | — |
| `same_direction_reentry` | 0.053314 | 0.224821 | 100.00% | 0.202187 | 0.401662 | 100.00% | — |
| `size_delta_ratio` | 2.673328 | 14.104503 | 19.60% | 1.808017 | 5.628128 | 67.83% | — |
| `trader_prior_tilt` | 40.382546 | 1.722521 | 100.00% | 43.239310 | 49.989286 | 100.00% | — |
| `trader_prior_sl_discipline` | 0.001349 | 0.000159 | 100.00% | 0.001389 | 0.003554 | 100.00% | — |
| `trader_prior_survival` | 1.928955 | 0.303000 | 100.00% | 2.066229 | 0.756484 | 100.00% | — |

The only formal coverage collapse is `sl_distance_pct`, reflecting the
documented stop-loss usage break. Several sequential-history features have
low training coverage and higher evaluation coverage because the prelude
training window contains far fewer prior positions per account; this is a
support shift, not a coverage collapse.

## 5. Regime-break cost: ridge composite

The composite is the existing Stage 3 M3 ridge specification: all 28 frozen
features, target `gross_loss_per_lot`, training-target winsorisation at the 1st
and 99th percentiles, median imputation, numeric standardisation, categorical
one-hot encoding, and Ridge regression. Alpha is selected only by chronological
inner campaign validation inside the training window.

This is a split-viability comparison using the existing M3 specification; it
does not silently remove the SL/TP-derived features classified as contaminated
in the separate leakage audit.

For the within-primary comparison, “early C53+” is defined as C53-C58 and
“later C53+” as C59-C66. The matched late-window comparison is included because
the mandated model evaluates the entire C53-C66 window while the within-break
model necessarily starts evaluating later.

| model | fit campaigns | eval campaigns | alpha | eval n | Spearman | MAE | flagged mean gross loss/lot | flagged mean rP/lot | flagged coverage | flagged n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mandated | C33-C52 | C53-C66 | 0.3162 | 6,583 | 0.00546 | 410.3280 | 20.4926 | 13.4926 | 48.85% | 3,216 |
| mandated, late subset | C33-C52 | C59-C66 | 0.3162 | 3,597 | -0.01365 | 398.7674 | 5.9324 | -1.0676 | 42.84% | 1,541 |
| within-break | C53-C58 | C59-C66 | 1,000.0000 | 3,597 | 0.02591 | 328.1869 | 18.2055 | 11.2055 | 69.53% | 2,501 |

The like-for-like later-window gap, within-break minus mandated-prelude, is:

| metric | gap |
|---|---:|
| Spearman | +0.03955 |
| MAE | -70.5806 |
| flagged mean gross loss/lot | +12.2731 |
| flagged mean rP/lot | +12.2731 |
| flagged coverage | +26.69 percentage points |
| flagged count | +960 |

Training across the C52/C53 break therefore costs about `$12.27/lot` in the
model's flagged late-window gross-loss signal relative to fitting on early
C53+ data. The mandated prelude-trained model's full-window flagged mean is
higher because it includes the more favorable early C53-C58 evaluation rows;
the matched late-window comparison isolates the regime-break cost.

## 6. Exact P&L identity assertions

The repaired position table was checked on all `7,277` rows. The code assertion
is equivalent to:

```python
gross_loss_per_lot = -profit / amount
reverse_profit_per_lot = gross_loss_per_lot - 7.0
assert reverse_profit_per_lot == reverseProfit / amount  # numerical tolerance
```

Results:

| assertion | result |
|---|---:|
| rows checked | 7,277 |
| max absolute deviation: `gross_loss_per_lot - (-profit/amount)` | 0.0 |
| max absolute deviation: `reverse_profit_per_lot - (gross_loss_per_lot - 7)` | 0.0 |
| max absolute deviation: `reverse_profit_per_lot - reverseProfit/amount` | `9.094947017729282e-13` |
| rows exceeding `1e-9` tolerance | 0 |

The exact-once `$7` subtraction assertion was also added to
`tests/test_ingest.py`; the complete suite passes after the addition.

## 7. CLEAN-feature coverage and split-cost sensitivity

This follow-up removes the four now-inadmissible SL/TP-derived columns
`sl_distance_pct`, `sl_widening_delta`, `has_sl`, and `has_tp`. The resulting
CLEAN set has 24 features. Coverage is the non-NaN fraction; means and sample
standard deviations are calculated over non-NaN values. `challenge_type` is
categorical, so its mean and standard deviation are not defined.

| feature | train mean | train std | train cov. | C53-C65 mean | C53-C65 std | C53-C65 cov. | C53-C66 mean | C53-C66 std | C53-C66 cov. | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `loss_streak` | 0.110951 | 0.349101 | 100.00% | 0.572167 | 0.980684 | 100.00% | 0.572080 | 0.980635 | 100.00% | — |
| `win_streak` | 0.119597 | 0.411020 | 100.00% | 0.530234 | 0.971364 | 100.00% | 0.530153 | 0.971312 | 100.00% | — |
| `pnl_ewm` | -4.527752 | 84.697104 | 100.00% | -5.239077 | 55.211390 | 100.00% | -5.238281 | 55.207234 | 100.00% | — |
| `lot_zscore` | 0.317002 | 2.764533 | 1.30% | 0.259038 | 2.813655 | 36.13% | 0.259038 | 2.813655 | 36.12% | **<50%** |
| `amount` | 5.839726 | 8.508853 | 100.00% | 0.612940 | 0.591376 | 100.00% | 0.683073 | 5.720951 | 100.00% | — |
| `size_after_loss_delta` | -0.463889 | 3.896691 | 1.30% | -0.005554 | 0.562081 | 19.99% | -0.005554 | 0.562081 | 19.99% | **<50%** |
| `sl_usage_rate_5` | 1.000000 | 0.000000 | 1.30% | 0.777089 | 0.278768 | 36.54% | 0.777089 | 0.278768 | 36.53% | **<50%** |
| `manual_exit_rate_5` | 0.740741 | 0.277778 | 1.30% | 0.680076 | 0.275501 | 36.54% | 0.680076 | 0.275501 | 36.53% | **<50%** |
| `pnl_pct` | -0.002747 | 0.062301 | 100.00% | -0.008030 | 0.065601 | 100.00% | -0.008029 | 0.065596 | 100.00% | — |
| `dd_from_peak_pct` | 0.011929 | 0.047850 | 100.00% | 0.028510 | 0.059973 | 100.00% | 0.028506 | 0.059969 | 100.00% | — |
| `trade_index` | 1.260807 | 0.595551 | 100.00% | 4.067305 | 4.774336 | 100.00% | 4.066839 | 4.774123 | 100.00% | — |
| `log_dt_close` | 2.774739 | 4.084370 | 19.60% | 3.647188 | 3.645036 | 67.84% | 3.647188 | 3.645036 | 67.83% | — |
| `trades_per_hour` | 48.870503 | 23.073053 | 100.00% | 26.702779 | 28.515931 | 100.00% | 26.707837 | 28.516718 | 100.00% | — |
| `prior_campaigns` | 0.498559 | 1.057849 | 100.00% | 1.732908 | 2.388637 | 100.00% | 1.732797 | 2.388472 | 100.00% | — |
| `prior_campaigns_x_loss_streak_ge_2` | 0.007205 | 0.125782 | 100.00% | 0.249468 | 1.101888 | 100.00% | 0.249430 | 1.101809 | 100.00% | — |
| `shared_ip` | 0.949568 | 0.218993 | 100.00% | 0.855211 | 0.351915 | 100.00% | 0.855233 | 0.351892 | 100.00% | — |
| `ip_cluster_size` | 22.530523 | 18.833189 | 99.14% | 12.352520 | 16.102138 | 99.77% | 12.350944 | 16.101419 | 99.77% | — |
| `challenge_type` | n/a | n/a | 100.00% | n/a | n/a | 100.00% | n/a | n/a | 100.00% | categorical |
| `gold_vol_prev_day` | 0.030031 | 0.021350 | 100.00% | 0.023011 | 0.009962 | 100.00% | 0.023012 | 0.009961 | 100.00% | — |
| `same_direction_reentry` | 0.053314 | 0.224821 | 100.00% | 0.202218 | 0.401685 | 100.00% | 0.202187 | 0.401662 | 100.00% | — |
| `size_delta_ratio` | 2.673328 | 14.104503 | 19.60% | 1.808017 | 5.628128 | 67.84% | 1.808017 | 5.628128 | 67.83% | — |
| `trader_prior_tilt` | 40.382546 | 1.722521 | 100.00% | 43.232667 | 49.990178 | 100.00% | 43.239310 | 49.989286 | 100.00% | — |
| `trader_prior_sl_discipline` | 0.001349 | 0.000159 | 100.00% | 0.001389 | 0.003554 | 100.00% | 0.001389 | 0.003554 | 100.00% | — |
| `trader_prior_survival` | 1.928955 | 0.303000 | 100.00% | 2.066332 | 0.756495 | 100.00% | 2.066229 | 0.756484 | 100.00% | — |

The features below 50% evaluation coverage are `lot_zscore`,
`size_after_loss_delta`, `sl_usage_rate_5`, and `manual_exit_rate_5`. The
coverage result is unchanged in substance when C66 is included; its one row
changes the displayed percentages only in the third decimal place.

## 8. Cold-start impact on CLEAN history features

The keyed cold-start rate is 79.39% in C53-C66 (5,214 of 6,568 keyed rows);
15 rows have no `traderKey`, giving a strict unavailable rate of 79.43%.
The C53-C65 values are 5,213 of 6,567 keyed rows, 79.38%, and 79.43%
strictly unavailable.

| feature | C53-C65 non-NaN coverage | C53-C66 non-NaN coverage | usable as a numeric field? | trader-specific under mandated split? |
|---|---:|---:|---|---|
| `prior_campaigns` | 100.00% (6,582) | 100.00% (6,583) | Yes; cold starts are coded as zero | Only for rows with prior keyed history |
| `prior_campaigns_x_loss_streak_ge_2` | 100.00% (6,582) | 100.00% (6,583) | Yes; zero for cold starts | Only for rows with prior keyed history |
| `trader_prior_tilt` | 100.00% (6,582) | 100.00% (6,583) | Yes, via fallback/shrinkage | No for roughly 79.39% cold keyed rows |
| `trader_prior_sl_discipline` | 100.00% (6,582) | 100.00% (6,583) | Yes, via fallback/shrinkage | No for roughly 79.39% cold keyed rows |
| `trader_prior_survival` | 100.00% (6,582) | 100.00% (6,583) | Yes, via fallback/shrinkage | No for roughly 79.39% cold keyed rows |

Thus these fields are computable, but “non-NaN” must not be read as “identified
trader history.” For Family G, most evaluation values are population fallback
or shrinkage values rather than evidence about the current trader. The fields
remain usable as a cold-start-aware baseline covariate; they are not usable as
trader-specific signals for the cold-start majority.

## 9. C66 sensitivity: every headline metric on both evaluation windows

C66 contributes exactly 1,911 fills collapsing to one position and one account.
That account is already present in C53-C65, so adding C66 increases the
evaluation account count by zero. The following table reports both windows;
the fit window is identical in both cases.

| metric | C53-C65 | C53-C66 |
|---|---:|---:|
| raw fills | 19,444 | 21,355 |
| positions | 6,582 | 6,583 |
| distinct accounts | 496 | 496 |
| campaigns | 13 | 14 |
| keyed positions | 6,567 | 6,568 |
| cold keyed positions | 5,213 | 5,214 |
| cold rate among keyed | 79.38% | 79.39% |
| missing `traderKey` | 15 | 15 |
| strict unavailable rate | 79.43% | 79.43% |
| mean gross loss/lot | 12.436357 | 12.434210 |
| mean reverseProfit/lot | 5.436357 | 5.434210 |

For completeness, the published M3 ridge composite was evaluated under both
tracks without changing the C33-C52 fit. Track B is the published common-split
specification (`alpha=0.3162`); Track A is included as a sensitivity.

| track | metric | C53-C65 | C53-C66 |
|---|---|---:|---:|
| B | alpha | 0.3162 | 0.3162 |
| B | Spearman | 0.005463 | 0.005460 |
| B | MAE | 410.3690 | 410.3280 |
| B | flagged mean gross loss/lot | 20.4995 | 20.4926 |
| B | flagged mean reverseProfit/lot | 13.4995 | 13.4926 |
| B | flagged coverage | 48.85% | 48.85% |
| B | flagged n | 3,215 | 3,216 |
| A | alpha | 1,000.0 | 1,000.0 |
| A | Spearman | 0.009917 | 0.009917 |
| A | MAE | 351.6181 | 351.5785 |
| A | flagged mean gross loss/lot | 32.9683 | 32.9468 |
| A | flagged mean reverseProfit/lot | 25.9683 | 25.9468 |
| A | flagged coverage | 24.46% | 24.47% |
| A | flagged n | 1,610 | 1,611 |

The model, alpha selection, and training data are identical; only the one C66
row is added to evaluation. The changes in aggregate means and model metrics
are therefore the single-position delta, not a new regime result. The P&L
identity checks also remain exact in both windows: `gross_loss_per_lot` equals
`-profit/amount`, and `reverse_profit_per_lot` equals `reverseProfit/amount`
within the existing `9.1e-13` maximum floating-point deviation.

## 10. Training-set adequacy

The mandated training set contains 694 positions, 330 accounts, and 24 CLEAN
features: **28.92 positions per CLEAN feature**. The evaluation set contains
6,583 positions, so the fit/evaluation imbalance is approximately 1:9.49.

The training mean cluster size is 694/330 = 2.103 positions per account. Using
the primary-era ICCs from `reports/design_annex_stats.md` and applying them to
that training cluster size gives the following account-sized approximation:

| ICC sensitivity | ICC | training DEFF | design-effect-adjusted n |
|---|---:|---:|---:|
| traderKey | 0.162328 | 1.1791 | 588.6 positions |
| ipClusterId | 0.096472 | 1.1064 | 627.3 positions |

For the requested MDE calculation, the published primary-era design effects
are used directly in the stated formula. The robust planning sigma is the
1%-99% winsorized primary-era sigma, 482.4515 dollars/lot; the raw-sigma
figures are a heavier-tail sensitivity. With `z_(1-alpha/2)+z_(1-beta) =
2.801585`, `alpha=0.05`, and power 0.80:

| clustering scheme | published DEFF | design-effect-adjusted n (`694/DEFF`) | MDE, winsorized sigma | MDE, raw sigma |
|---|---:|---:|---:|---:|
| traderKey | 1.753221 | 395.8 | $67.94/lot | $78.20/lot |
| ipClusterId | 1.615386 | 429.6 | $65.21/lot | $75.06/lot |

These are minimum detectable absolute edges under the stated assumptions, not
guarantees of model performance. Plainly, 694 training positions is not large
enough to reliably detect plausible small or moderate edges around the $7
hurdle, $10, $20, or even $40 per lot after clustering. It has useful power
only for very large effects on the order of $65-$78 per lot. The mandated
split is therefore structurally underpowered for subtle behavioral edges, and
the 79.39% cold-start rate makes the trader-history features even less
informative than their nominal non-NaN coverage suggests.
