# Family G Value

## Pre-Committed Interpretation

Track B is expected to outperform Track A for `M3` specifically. This is mechanical: identity overlap is information, and Family G is built to use it, not evidence of superiority. Any `Track B > Track A` gap on `M3` is reported here as expected, not as a finding.

## Decision Rule

Include Family G in the Stage 3 composite if `M3` beats `M2` on **Track B pooled Spearman** and does **not** degrade the **Track A pooled economic metric** by more than 10%.

## Modeling Setup

- Ridge regression on `gross_loss_per_lot`.
- Target winsorized at the 1st and 99th percentiles using the outer training fold only.
- `alpha` selected by inner expanding campaign CV within each outer training fold.
- Metrics are evaluated on raw validation targets; no validation-row statistics are used in fitting or clipping.

Feature sets:

- `M1`: `loss_streak`, `win_streak`, `pnl_ewm`, `lot_zscore`, `amount`, `size_after_loss_delta`, `has_sl`, `has_tp`, `sl_distance_pct`, `sl_usage_rate_5`, `manual_exit_rate_5`, `pnl_pct`, `dd_from_peak_pct`, `trade_index`, `log_dt_close`, `trades_per_hour`, `prior_campaigns`, `shared_ip`, `ip_cluster_size`, `challenge_type`, `gold_vol_prev_day`
- `M2`: `M1` + `sl_widening_delta`, `same_direction_reentry`, `size_delta_ratio`
- `M3`: `M2` + `trader_prior_tilt`, `trader_prior_sl_discipline`, `trader_prior_survival`, `prior_campaigns_x_loss_streak_ge_2`

## Track A

| model | fold | n_rows | alpha | spearman_rho | mae | flagged_mean_loss_per_lot | flagged_coverage | n_flagged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M1` | Fold 1 | 371 | 0.003162 | 0.0044 | 382.0806 | 81.0818 | 35.31% | 131 |
| `M2` | Fold 1 | 371 | 0.03162 | 0.0171 | 384.0076 | 65.3926 | 39.89% | 148 |
| `M3` | Fold 1 | 371 | 0.3162 | 0.0184 | 382.4897 | 51.0570 | 43.67% | 162 |
| `M1` | Fold 2 | 454 | 0.03162 | -0.0071 | 412.4875 | 72.7481 | 78.41% | 356 |
| `M2` | Fold 2 | 454 | 0.03162 | 0.0232 | 413.3344 | 72.6580 | 77.09% | 350 |
| `M3` | Fold 2 | 454 | 0.1 | 0.0243 | 413.8854 | 65.9595 | 78.19% | 355 |
| `M1` | Fold 3 | 464 | 10 | -0.0481 | 241.8985 | -22.0927 | 82.11% | 381 |
| `M2` | Fold 3 | 464 | 0.03162 | -0.0424 | 243.9287 | -24.3135 | 79.53% | 369 |
| `M3` | Fold 3 | 464 | 0.1 | -0.0500 | 244.3626 | -21.2953 | 81.25% | 377 |
| `M1` | Fold 4 | 901 | 10 | 0.0685 | 319.3673 | 6.3957 | 77.80% | 701 |
| `M2` | Fold 4 | 901 | 316.2 | 0.0309 | 324.1702 | 8.8441 | 72.81% | 656 |
| `M3` | Fold 4 | 901 | 1000 | 0.0456 | 322.7609 | 12.7747 | 74.92% | 675 |
| `M1` | Pooled | 2190 |  | 0.0028 | 332.8822 | 20.7687 | 71.64% | 1569 |
| `M2` | Pooled | 2190 |  | 0.0051 | 335.7904 | 20.9708 | 69.54% | 1523 |
| `M3` | Pooled | 2190 |  | 0.0079 | 335.1596 | 20.5745 | 71.64% | 1569 |

## Track B

| model | fold | n_rows | alpha | spearman_rho | mae | flagged_mean_loss_per_lot | flagged_coverage | n_flagged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `M1` | Fold 1 | 949 | 1000 | 0.0356 | 359.3851 | 30.6819 | 20.34% | 193 |
| `M2` | Fold 1 | 949 | 1000 | 0.0366 | 360.2844 | 48.1718 | 21.60% | 205 |
| `M3` | Fold 1 | 949 | 1000 | 0.0519 | 362.1174 | 45.9476 | 28.77% | 273 |
| `M1` | Fold 2 | 1033 | 1000 | 0.0462 | 406.7130 | 65.2103 | 59.05% | 610 |
| `M2` | Fold 2 | 1033 | 1000 | 0.0692 | 406.2814 | 70.5836 | 60.12% | 621 |
| `M3` | Fold 2 | 1033 | 1000 | 0.0692 | 406.6147 | 67.6684 | 63.31% | 654 |
| `M1` | Fold 3 | 973 | 1000 | -0.0097 | 256.2302 | -0.6202 | 69.89% | 680 |
| `M2` | Fold 3 | 973 | 1000 | 0.0006 | 257.1990 | 7.0488 | 67.42% | 656 |
| `M3` | Fold 3 | 973 | 1000 | -0.0112 | 258.4914 | 0.4620 | 68.45% | 666 |
| `M1` | Fold 4 | 1590 | 1000 | 0.0322 | 310.5683 | 0.6552 | 65.35% | 1039 |
| `M2` | Fold 4 | 1590 | 1000 | 0.0226 | 313.6847 | 6.4037 | 63.02% | 1002 |
| `M3` | Fold 4 | 1590 | 1000 | 0.0336 | 313.7611 | 3.3269 | 65.97% | 1049 |
| `M1` | Pooled | 4545 |  | 0.0255 | 330.9806 | 18.2232 | 55.49% | 2522 |
| `M2` | Pooled | 4545 |  | 0.0314 | 332.3679 | 26.0661 | 54.65% | 2484 |
| `M3` | Pooled | 4545 |  | 0.0341 | 333.1297 | 22.9358 | 58.13% | 2642 |

## Inclusion Decision

Decision: **INCLUDE** Family G in the Stage 3 composite.

- `Track B pooled Spearman`: `M2=0.0314`, `M3=0.0341`.
- `Track A pooled economic metric` (mean realized gross loss/lot on flagged positions): `M2=20.9708`, `M3=20.5745`.
- `Track A` economic retention versus the 90% floor: `98.11%` retained (threshold: `90.00%`).
