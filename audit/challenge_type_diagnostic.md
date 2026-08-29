# `challenge_type` diagnostic for frozen V2

Date: 2026-08-24  
Scope: frozen V2 artifact and `predict()` path; collapsed position rows  
Primary performance window: C53–C65 (`n=6,582`); C66 is excluded from dollar
totals  
Acted subset: `n=177` in C53–C65; C66 has one additional acted position in the
C53–C66 evaluation window

No V2 refit was performed. The ablation was fit only in the separate
`stage3-tp-remediation` worktree.

## Part 1 — encoding facts

Drop-first: **No; both fitted levels are retained as dummy columns alongside a separate intercept.**

Ridge intercept penalty: **No; `Ridge(fit_intercept=True)` fits the intercept separately from the penalized coefficient vector.**

Dummy scaling: **No; dummy values are appended as 0/1 columns without the numeric mean/scale transformation; dummy means/scales are not defined.**

Unseen `challenge_type`: **`_canonical_category()` returns `str(value)`; `_transform()` compares it only with fitted categories, so all fitted dummy columns are 0 and no exception is raised (`stage3_model.py:104-112`, `stage3_model.py:219-223`).**

NULL/absent `challenge_type`: **Absent: `_state_config()` defaults through `row.get("challenge_type", row.get("challenge_type_id", "unknown"))`; NULL: `TraderState` canonicalizes missing to `"unknown"`; `_transform()` activates `cat__challenge_type=unknown` (`stage3_model.py:395-410`, `features.py:165-167`, `stage3_model.py:104-112`, `stage3_model.py:219-223`).**

Fitted level absent from new data: **The artifact's fitted category loop still appends that column for every new frame; equality is false for every row, so the column remains present and is all 0 (`stage3_model.py:219-223`).**

The two fitted categorical levels are `11` and `unknown`. Missingness is
therefore represented by the explicit canonical `unknown` level, not by a
separate missingness indicator.

## Part 2 — distribution and regime confound

The source loader produced `46,520` fills collapsed to `7,277` positions. The
tables below count positions, because that is the row unit consumed by the
backtest and `predict()`. `unknown` is the canonicalized missing/absent raw
metadata value. The “other raw” column is calculated before one-hot encoding;
it is zero in every campaign.

### All campaigns, C1–C66

| campaign | n trades | % level 11 | % unknown | % other raw | n other |
|---:|---:|---:|---:|---:|---:|
| C1 | 0 | — | — | — | 0 |
| C2 | 0 | — | — | — | 0 |
| C3 | 0 | — | — | — | 0 |
| C4 | 0 | — | — | — | 0 |
| C5 | 0 | — | — | — | 0 |
| C6 | 0 | — | — | — | 0 |
| C7 | 0 | — | — | — | 0 |
| C8 | 0 | — | — | — | 0 |
| C9 | 0 | — | — | — | 0 |
| C10 | 0 | — | — | — | 0 |
| C11 | 0 | — | — | — | 0 |
| C12 | 0 | — | — | — | 0 |
| C13 | 0 | — | — | — | 0 |
| C14 | 0 | — | — | — | 0 |
| C15 | 0 | — | — | — | 0 |
| C16 | 0 | — | — | — | 0 |
| C17 | 0 | — | — | — | 0 |
| C18 | 0 | — | — | — | 0 |
| C19 | 0 | — | — | — | 0 |
| C20 | 0 | — | — | — | 0 |
| C21 | 0 | — | — | — | 0 |
| C22 | 0 | — | — | — | 0 |
| C23 | 0 | — | — | — | 0 |
| C24 | 0 | — | — | — | 0 |
| C25 | 0 | — | — | — | 0 |
| C26 | 0 | — | — | — | 0 |
| C27 | 0 | — | — | — | 0 |
| C28 | 0 | — | — | — | 0 |
| C29 | 0 | — | — | — | 0 |
| C30 | 0 | — | — | — | 0 |
| C31 | 0 | — | — | — | 0 |
| C32 | 0 | — | — | — | 0 |
| C33 | 33 | 0.00% | 100.00% | 0.00% | 0 |
| C34 | 41 | 0.00% | 100.00% | 0.00% | 0 |
| C35 | 33 | 0.00% | 100.00% | 0.00% | 0 |
| C36 | 41 | 0.00% | 100.00% | 0.00% | 0 |
| C37 | 32 | 0.00% | 100.00% | 0.00% | 0 |
| C38 | 39 | 0.00% | 100.00% | 0.00% | 0 |
| C39 | 35 | 0.00% | 100.00% | 0.00% | 0 |
| C40 | 43 | 0.00% | 100.00% | 0.00% | 0 |
| C41 | 1 | 0.00% | 100.00% | 0.00% | 0 |
| C42 | 39 | 0.00% | 100.00% | 0.00% | 0 |
| C43 | 27 | 0.00% | 100.00% | 0.00% | 0 |
| C44 | 31 | 100.00% | 0.00% | 0.00% | 0 |
| C45 | 35 | 100.00% | 0.00% | 0.00% | 0 |
| C46 | 30 | 100.00% | 0.00% | 0.00% | 0 |
| C47 | 38 | 100.00% | 0.00% | 0.00% | 0 |
| C48 | 43 | 100.00% | 0.00% | 0.00% | 0 |
| C49 | 35 | 100.00% | 0.00% | 0.00% | 0 |
| C50 | 40 | 100.00% | 0.00% | 0.00% | 0 |
| C51 | 39 | 100.00% | 0.00% | 0.00% | 0 |
| C52 | 39 | 100.00% | 0.00% | 0.00% | 0 |
| C53 | 519 | 100.00% | 0.00% | 0.00% | 0 |
| C54 | 509 | 100.00% | 0.00% | 0.00% | 0 |
| C55 | 485 | 100.00% | 0.00% | 0.00% | 0 |
| C56 | 524 | 100.00% | 0.00% | 0.00% | 0 |
| C57 | 511 | 0.00% | 100.00% | 0.00% | 0 |
| C58 | 438 | 0.00% | 100.00% | 0.00% | 0 |
| C59 | 552 | 100.00% | 0.00% | 0.00% | 0 |
| C60 | 481 | 0.00% | 100.00% | 0.00% | 0 |
| C61 | 564 | 0.00% | 100.00% | 0.00% | 0 |
| C62 | 409 | 0.00% | 100.00% | 0.00% | 0 |
| C63 | 584 | 0.00% | 100.00% | 0.00% | 0 |
| C64 | 496 | 0.00% | 100.00% | 0.00% | 0 |
| C65 | 510 | 0.00% | 100.00% | 0.00% | 0 |
| C66 | 1 | 0.00% | 100.00% | 0.00% | 0 |

### C53 regime shift

| window | unknown n | non-unknown n | total n | % unknown |
|---|---:|---:|---:|---:|
| C1–C52 | 364 | 330 | 694 | 52.4496% |
| C53–C66 | 3,994 | 2,589 | 6,583 | 60.6714% |

The Pearson chi-square test on the 2×2 table `[[364,330],[3994,2589]]` gives
`chi2(1)=17.6667`, `p=0.00002632`. The equivalent two-proportion test gives
`z=-4.2032`, two-sided `p=0.00002632`; the unknown share changes by
`+8.2219` percentage points. This is a distributional regime shift, but the
challenge type is also nearly campaign-blocked: C44–C56 and C59 are level 11,
while C33–C43, C57–C58, and C60–C66 are unknown.

### Distribution restricted to the 177 acted trades

This table uses the frozen V2 decisions in C53–C65 only; C66 is not part of the
177-row acted subset.

| campaign | n acted | % level 11 | % unknown | % other raw | n other |
|---:|---:|---:|---:|---:|---:|
| C1 | 0 | — | — | — | 0 |
| C2 | 0 | — | — | — | 0 |
| C3 | 0 | — | — | — | 0 |
| C4 | 0 | — | — | — | 0 |
| C5 | 0 | — | — | — | 0 |
| C6 | 0 | — | — | — | 0 |
| C7 | 0 | — | — | — | 0 |
| C8 | 0 | — | — | — | 0 |
| C9 | 0 | — | — | — | 0 |
| C10 | 0 | — | — | — | 0 |
| C11 | 0 | — | — | — | 0 |
| C12 | 0 | — | — | — | 0 |
| C13 | 0 | — | — | — | 0 |
| C14 | 0 | — | — | — | 0 |
| C15 | 0 | — | — | — | 0 |
| C16 | 0 | — | — | — | 0 |
| C17 | 0 | — | — | — | 0 |
| C18 | 0 | — | — | — | 0 |
| C19 | 0 | — | — | — | 0 |
| C20 | 0 | — | — | — | 0 |
| C21 | 0 | — | — | — | 0 |
| C22 | 0 | — | — | — | 0 |
| C23 | 0 | — | — | — | 0 |
| C24 | 0 | — | — | — | 0 |
| C25 | 0 | — | — | — | 0 |
| C26 | 0 | — | — | — | 0 |
| C27 | 0 | — | — | — | 0 |
| C28 | 0 | — | — | — | 0 |
| C29 | 0 | — | — | — | 0 |
| C30 | 0 | — | — | — | 0 |
| C31 | 0 | — | — | — | 0 |
| C32 | 0 | — | — | — | 0 |
| C33 | 0 | — | — | — | 0 |
| C34 | 0 | — | — | — | 0 |
| C35 | 0 | — | — | — | 0 |
| C36 | 0 | — | — | — | 0 |
| C37 | 0 | — | — | — | 0 |
| C38 | 0 | — | — | — | 0 |
| C39 | 0 | — | — | — | 0 |
| C40 | 0 | — | — | — | 0 |
| C41 | 0 | — | — | — | 0 |
| C42 | 0 | — | — | — | 0 |
| C43 | 0 | — | — | — | 0 |
| C44 | 0 | — | — | — | 0 |
| C45 | 0 | — | — | — | 0 |
| C46 | 0 | — | — | — | 0 |
| C47 | 0 | — | — | — | 0 |
| C48 | 0 | — | — | — | 0 |
| C49 | 0 | — | — | — | 0 |
| C50 | 0 | — | — | — | 0 |
| C51 | 0 | — | — | — | 0 |
| C52 | 0 | — | — | — | 0 |
| C53 | 5 | 100.00% | 0.00% | 0.00% | 0 |
| C54 | 14 | 100.00% | 0.00% | 0.00% | 0 |
| C55 | 14 | 100.00% | 0.00% | 0.00% | 0 |
| C56 | 10 | 100.00% | 0.00% | 0.00% | 0 |
| C57 | 9 | 0.00% | 100.00% | 0.00% | 0 |
| C58 | 17 | 0.00% | 100.00% | 0.00% | 0 |
| C59 | 21 | 100.00% | 0.00% | 0.00% | 0 |
| C60 | 10 | 0.00% | 100.00% | 0.00% | 0 |
| C61 | 26 | 0.00% | 100.00% | 0.00% | 0 |
| C62 | 11 | 0.00% | 100.00% | 0.00% | 0 |
| C63 | 14 | 0.00% | 100.00% | 0.00% | 0 |
| C64 | 14 | 0.00% | 100.00% | 0.00% | 0 |
| C65 | 12 | 0.00% | 100.00% | 0.00% | 0 |
| C66 | 0 | — | — | — | 0 |

## Part 3 — decision contribution

For each transformed column, contribution is the realized transformed matrix
value multiplied by its frozen artifact coefficient. The intercept is excluded
because the requested ranking is across the 21 columns. Values below are mean
absolute contribution per trade, in score units.

The groups are:

- `acted`: final V2 `FADE`, C53–C65, `n=177`.
- `score cleared`: score `> 0` (the effective hurdle), C53–C65, `n=183`.
- `abstained`: final V2 `ABSTAIN`, C53–C65, `n=6,405`.

The last two groups overlap by `n=6`: those trades cleared the score hurdle but
were abstained by one of the two frozen overrides.

| Rank acted | Column | Mean |contribution| acted | Rank score-cleared | Mean |contribution| score-cleared | Rank abstained | Mean |contribution| abstained |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `num__prior_campaigns_x_loss_streak_ge_2` | 56.319323 | 1 | 55.858365 | 7 | 1.223690 |
| 2 | `num__trade_index` | 14.596853 | 2 | 14.420265 | 1 | 11.298408 |
| 3 | `num__lot_zscore` | 8.141448 | 3 | 7.923278 | 4 | 3.431782 |
| 4 | `num__manual_exit_rate_5` | 5.413071 | 4 | 5.325451 | 5 | 2.865086 |
| 5 | `num__log_dt_close` | 5.182884 | 5 | 5.085896 | 3 | 5.042338 |
| 6 | `num__trades_per_hour` | 3.455542 | 6 | 3.428402 | 6 | 2.550800 |
| 7 | `num__same_direction_reentry` | 1.611883 | 7 | 1.603191 | 13 | 0.603083 |
| 8 | `num__pnl_pct` | 1.601328 | 8 | 1.580733 | 9 | 0.876819 |
| 9 | `num__pnl_ewm` | 1.400832 | 9 | 1.385845 | 12 | 0.660539 |
| 10 | `num__win_streak` | 1.258388 | 10 | 1.255621 | 2 | 5.733760 |
| 11 | `cat__challenge_type=unknown` | 1.205258 | 11 | 1.207006 | 8 | 1.143635 |
| 12 | `num__loss_streak` | 1.055618 | 12 | 1.047932 | 16 | 0.241103 |
| 13 | `cat__challenge_type=11` | 0.682624 | 13 | 0.680875 | 11 | 0.744247 |
| 14 | `num__amount` | 0.555960 | 14 | 0.556181 | 15 | 0.553883 |
| 15 | `num__ip_cluster_size` | 0.506641 | 15 | 0.509069 | 14 | 0.591634 |
| 16 | `num__gold_vol_prev_day` | 0.246085 | 16 | 0.245465 | 17 | 0.236370 |
| 17 | `num__size_after_loss_delta` | 0.234997 | 17 | 0.231366 | 18 | 0.107555 |
| 18 | `num__shared_ip` | 0.210124 | 18 | 0.210124 | 10 | 0.767522 |
| 19 | `num__dd_from_peak_pct` | 0.031427 | 19 | 0.030916 | 20 | 0.014421 |
| 20 | `num__size_delta_ratio` | 0.023756 | 20 | 0.023424 | 19 | 0.026490 |
| 21 | `num__sl_usage_rate_5` | 0.000000 | 21 | 0.000000 | 21 | 0.000000 |

The challenge-type columns rank **11th** (`unknown`) and **13th** (`11`) on
the 177 acted trades. On score-cleared trades they rank **11th** and **13th**;
on final abstentions they rank **8th** and **11th**. Their absolute effects are
not small because the dummy values are unscaled: each active level contributes
approximately `+1.887882` for level 11 or `-1.887882` for unknown. The mean
absolute values differ by group because the level mix differs.

## Part 4 — challenge-type ablation

### Branch and procedure

The ablation was run only in the separate worktree on branch
`stage3-tp-remediation`:

`[/tmp/catch22_stage3_tp_remediation/artifacts/stage3_v3_challengetype_ablation.json](/tmp/catch22_stage3_tp_remediation/artifacts/stage3_v3_challengetype_ablation.json)`

The branch-only diagnostic removed `challenge_type` from `V2_FEATURES` and
disabled the categorical transform. The Ridge estimator, alpha grid, expanding
campaign CV, training threshold selection, hurdle `0`, and both abstain overrides
were unchanged; the pinned seed constant remains `_BOOT_SEED=7`. The frozen submission worktree remains on
`stage3-submission`; `artifacts/stage3_v2.json` was not overwritten.

The ablation artifact has 19 raw features, 19 transformed columns, and 19
coefficients. Alpha selection was unchanged:

| quantity | current V2 | no `challenge_type` ablation |
|---|---:|---:|
| CV-selected alpha | 1,000.000000 | 1,000.000000 |
| frozen alpha | 3,162.27766017 | 3,162.27766017 |
| selected score threshold | -10.000 | -12.000 |
| effective execution hurdle | 0.000 | 0.000 |

### Aggregate performance, C53–C65

EW/lot is the equal-weighted mean realized reverseProfit per lot. SW/lot is
the amount-weighted realized reverseProfit per lot. Dollar totals exclude C66.

| model | n acted | coverage | EW/lot | SW/lot | dollar total |
|---|---:|---:|---:|---:|---:|
| Frozen V2 | 177 | 2.6892% | 10.4327 | -33.8486 | -$3,556.81 |
| No `challenge_type` | 188 | 2.8563% | -0.8740 | -34.6854 | -$3,960.73 |
| Delta | +11 | +0.1671 pp | -11.3067 | -0.8368 | -$403.92 |

**SIGN-FLIP FLAG: EW/lot flips from positive (`+10.4327`) to negative
(`-0.8740`). SW/lot remains negative (`-33.8486` to `-34.6854`) and does not
flip sign.**

### Per-campaign performance and deltas

| campaign | V2 n | Abl n | Δn | V2 EW | Abl EW | ΔEW | V2 SW | Abl SW | ΔSW | V2 $ | Abl $ | Δ$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C53 | 5 | 4 | -1 | 173.557 | 186.835 | +13.278 | 103.021 | 100.472 | -2.550 | 145.26 | 123.58 | -21.68 |
| C54 | 14 | 14 | 0 | 45.775 | 45.775 | +0.000 | 11.617 | 11.617 | +0.000 | 88.17 | 88.17 | +0.00 |
| C55 | 14 | 14 | 0 | -6.592 | -6.592 | +0.000 | 81.985 | 81.985 | +0.000 | 501.75 | 501.75 | +0.00 |
| C56 | 10 | 10 | 0 | 144.503 | 144.503 | +0.000 | 91.955 | 91.955 | +0.000 | 432.19 | 432.19 | +0.00 |
| C57 | 9 | 9 | 0 | -33.607 | -33.607 | +0.000 | -49.385 | -49.385 | +0.000 | -180.75 | -180.75 | +0.00 |
| C58 | 17 | 18 | +1 | -43.661 | -52.285 | -8.624 | -145.371 | -149.056 | -3.685 | -1,868.02 | -2,056.97 | -188.95 |
| C59 | 21 | 21 | 0 | -99.990 | -99.990 | +0.000 | -87.301 | -87.301 | +0.000 | -1,577.53 | -1,577.53 | +0.00 |
| C60 | 10 | 11 | +1 | -19.361 | -206.095 | -186.733 | -45.824 | -78.192 | -32.368 | -395.46 | -685.74 | -290.28 |
| C61 | 26 | 28 | +2 | -24.816 | -33.054 | -8.238 | -42.242 | -51.747 | -9.506 | -515.77 | -693.93 | -178.16 |
| C62 | 11 | 11 | 0 | 44.010 | 44.010 | +0.000 | -18.184 | -18.184 | +0.000 | -133.11 | -133.11 | +0.00 |
| C63 | 14 | 16 | +2 | -110.691 | -96.207 | +14.484 | -83.173 | -64.869 | +18.304 | -596.35 | -542.95 | +53.40 |
| C64 | 14 | 16 | +2 | 147.154 | 128.801 | -18.353 | -0.253 | -0.416 | -0.163 | -2.09 | -4.42 | -2.33 |
| C65 | 12 | 16 | +4 | 164.495 | 164.067 | -0.428 | 76.963 | 73.097 | -3.866 | 544.90 | 768.98 | +224.08 |

C66 had one acted position under V2 and one under the ablation; it is excluded
from the dollar total and from the 177-row primary acted comparison.
