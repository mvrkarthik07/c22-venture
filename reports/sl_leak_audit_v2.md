# Stop-loss leakage audit v2

Date: 20 Aug 2026  
Data: repaired ingestion (`46,520` fills -> `7,277` positions)  
Primary era: C53-C65 (`6,582` positions, `496` active accounts, `13` campaigns)

The earlier `sl_leak_audit.md` is invalid for position-level conclusions: it
was generated while every fill was being treated as a position. In particular,
its fill-recovery comparison had no multi-fill groups. Every result below was
rerun after restoring the collapse key and cardinality. The overall corpus
contains `46,520 / 7,277 = 6.39` fills per collapsed position.

## Executive findings

- In the primary era, `4,543` of `6,582` positions have more than one fill.
  `slPrice` changes between the first and last fill in `73.12%` of them;
  `tpPrice` changes in `79.84%`.
- The collapse code uses `first` after sorting by `closeDateTime`. Pandas'
  `GroupBy.first` skips nulls, so the retained value is the first non-null
  value in close-time order, not necessarily the literal first fill and not
  the last or maximum.
- A literal first-fill `slPrice` is directionally cleaner than the last-fill
  value (`11.98%` versus `16.51%` violations), so an audit-only
  `sl_distance_pct_at_open` reconstruction is possible. Its pooled signal
  passes both tracks, but neither Track-4 cell clears both clustered CIs.
- Direction violations are associated with profitable outcomes: current
  collapsed-side violators have mean gross loss per lot `-68.53` and a
  `57.12%` win rate, versus `45.78` and `45.51%` for non-violators. This is
  confirmation that the violation flag is exposed to close-time stop movement.
- Four current-position features are contaminated by this ambiguity:
  `has_sl`, `has_tp`, `sl_distance_pct`, and `sl_widening_delta`. Three
  history features are temporally clean but semantically suspect because their
  prior values are close-time-derived: `sl_usage_rate_5`,
  `manual_exit_rate_5`, and `trader_prior_sl_discipline`.

## 1. Fill-level recovery

### First/last comparison

Fills were ordered by `closeDateTime`, with original file order as the tie
breaker. The comparison is restricted to primary-era positions with `n_fills >
1`.

| field | multi-fill positions | first/last differ | fraction differ | both values non-null | first null -> last set | first set -> last null |
|---|---:|---:|---:|---:|---:|---:|
| `slPrice` | 4,543 | 3,322 | 73.12% | 1,029 | 1,605 | 691 |
| `tpPrice` | 4,543 | 3,627 | 79.84% | 1,279 | 1,827 | 524 |

For rows where both values are non-null, the change is `last - first`:

| field | n | mean change | p01 | p25 | median | p75 | p99 | minimum | maximum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `slPrice` | 1,029 | -0.9818 | -60.4644 | -6.8200 | 0.0000 | 6.0800 | 44.1356 | -226.8400 | 246.9100 |
| `tpPrice` | 1,279 | 0.8296 | -85.8644 | -13.0000 | -0.6100 | 13.6150 | 82.4186 | -120.0000 | 298.5900 |

### Current aggregation

`to_positions()` sorts by `closeDateTime` and applies:

```python
"slPrice": "first", "tpPrice": "first"
```

Therefore the aggregation is **first**, with the important pandas null
semantics that `first` skips nulls. It is not last and not max. In primary-era
groups, the consequence is:

| field | literal first-fill value non-null | any fill non-null | literal last-fill value non-null | current collapsed non-null |
|---|---:|---:|---:|---:|
| `slPrice` | 2,800 | 5,013 | 3,714 | 5,013 |
| `tpPrice` | 2,996 | 5,268 | 4,299 | 5,268 |

Thus current `has_sl` and `has_tp` are equivalent to “a non-null value existed
at some point in the fill sequence,” not “the opening ticket had an SL/TP.”
The source does not contain an opening-ticket snapshot or modification
timestamp, so an opening-ticket interpretation cannot be certified from these
exports.

### Direction validity: first versus last

Under the recorded-side convention (`BUY`: `slPrice < openPrice`; `SELL`:
`slPrice > openPrice`), the rates for multi-fill positions are:

| value used | non-null SL rows | violations | violation rate |
|---|---:|---:|---:|
| literal first-fill `slPrice` | 1,720 | 206 | 11.98% |
| literal last-fill `slPrice` | 2,634 | 435 | 16.51% |

The first-fill value violates `4.54` percentage points less often. This supports
the first fill as the best available opening-time proxy, but does not prove it
was captured on the opening ticket: `1,605` groups have a null first fill and a
later SL value.

### Recovered `sl_distance_pct_at_open`

I reconstructed `sl_distance_pct_at_open` as:

```text
abs(openPrice - literal_first_fill_slPrice) / openPrice
```

with null output when the literal first fill has no `slPrice`. It was evaluated
through the full four-fold, two-track walk-forward engine with the pinned
`n_boot=2,000`, `seed=7` clustered bootstrap. Results are reverseProfit per lot.

| track | fold | n selected | rP/lot | trader CI | IP CI | PASS |
|---|---|---:|---:|---|---|---|
| A | Fold 4 | 65 | 150.1536 | [-81.1137, 376.2305] | [-76.9711, 366.3324] | No |
| A | Pooled | 149 | 281.8090 | [115.2207, 437.2017] | [121.3344, 448.0951] | Yes |
| B | Fold 4 | 115 | 73.0605 | [-106.6694, 244.4720] | [-122.2813, 251.4532] | No |
| B | Pooled | 353 | 209.2194 | [108.1296, 310.8124] | [103.8307, 319.0290] | Yes |

The pooled result is a recoverable signal, but the fold-4 cells are too
uncertain to support a stable holdout claim.

## 2. Trailing-stop hypothesis

The following uses primary-era collapsed positions with a non-null current
`slPrice` (5,013 rows). `gross_loss_per_lot = -profit / amount`; therefore a
negative mean indicates profitable trades. The violation flag uses the
recorded side and the current collapsed value, i.e. the first non-null
close-time value.

| group | n | mean gross_loss_per_lot | win rate |
|---|---:|---:|---:|
| direction violation | 1,390 | -68.5318 | 57.12% |
| no direction violation | 3,623 | 45.7808 | 45.51% |

Violating rows are systematically more profitable. This confirms that the
direction violation is not a harmless side-label artifact: it is consistent
with an SL being moved or removed after the trade has been in profit, so the
observed value is close-time/final-state exposed.

## 3. Exit-type split

`manual_exit_rate_5` derives from the `exit_type` field generated by
`infer_exit_type()`. There is no source exit-type column. The inference marks a
position `sl_hit` when close price is within the configured tolerance of the
retained `slPrice`, then marks `tp_hit` when close price is within tolerance of
`tpPrice` and not already an SL hit; remaining rows are `manual`.

The table below is primary era, at position level. R² is from an OLS linear fit
of `gross_loss_per_lot` on `sl_distance_pct`, using rows non-null for both
variables.

| inferred exit type | n positions | mean `sl_distance_pct` | mean `gross_loss_per_lot` | regression n | R² |
|---|---:|---:|---:|---:|---:|
| `manual` | 4,553 | 0.0013701 | 4.1381 | 3,113 | 0.0068 |
| `sl_hit` | 1,357 | 0.0008139 | 227.6214 | 1,357 | 0.6491 |
| `tp_hit` | 672 | 0.0027108 | -365.8732 | 543 | 0.0002 |

### Stop-out distance versus realized loss

For `sl_hit` rows, the planned stop distance per lot is:

```text
abs(openPrice - slPrice) * 100
```

The comparison ratio below is realized `gross_loss_per_lot` divided by that
planned stop-distance dollar value. It is signed; profitable stop-out-labelled
rows therefore have negative ratios.

| stop-out subset | n | ratio n | p05 | p25 | median | p75 | p95 | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all `sl_hit` | 1,357 | 1,354 | -2.0307 | -0.1930 | 0.8282 | 1.0157 | 1.8958 | 0.1737 |
| actual gross losses only (`gross_loss_per_lot > 0`) | 961 | 960 | 0.1570 | 0.7431 | 0.9879 | 1.0479 | 2.2869 | 1.2682 |

There are `395` profitable and `1` zero-gross-loss rows among the inferred
stop-outs. On actual loss rows, the median realized/planned ratio is close to
`1.0`, with a right tail from partial closes, slippage, and close-time field
changes.

## 4. Feature blast radius

Classification uses these definitions:

- **CLEAN**: no current-position close-time SL/TP/exit field is read, or the
  feature uses only prior closed positions/campaigns that are available before
  the current open.
- **CONTAMINATED**: directly reads current-position `slPrice`, `tpPrice`, or a
  current-position derivative whose value can change during the trade.
- **SUSPECT**: temporally causal because it uses prior closed positions, but
  the underlying prior SL/exit values are semantically final/close-time values
  rather than verified opening-ticket snapshots. SUSPECT does not mean current
  trade lookahead.

| classification | frozen features |
|---|---|
| CLEAN (21) | `loss_streak`, `win_streak`, `pnl_ewm`, `lot_zscore`, `amount`, `size_after_loss_delta`, `pnl_pct`, `dd_from_peak_pct`, `trade_index`, `log_dt_close`, `trades_per_hour`, `prior_campaigns`, `prior_campaigns_x_loss_streak_ge_2`, `shared_ip`, `ip_cluster_size`, `challenge_type`, `gold_vol_prev_day`, `same_direction_reentry`, `size_delta_ratio`, `trader_prior_tilt`, `trader_prior_survival` |
| CONTAMINATED (4) | `has_sl`, `has_tp`, `sl_distance_pct`, `sl_widening_delta` |
| SUSPECT (3) | `sl_usage_rate_5`, `manual_exit_rate_5`, `trader_prior_sl_discipline` |

### Prior-history timing confirmation

The three SUSPECT features are computed only from prior state:

- `sl_usage_rate_5` reads the deque of prior `has_sl` values before the current
  position is processed.
- `manual_exit_rate_5` reads the deque of prior inferred exit types before the
  current position is processed.
- `trader_prior_sl_discipline` is computed from completed prior campaigns; the
  current campaign is added only after its positions have been processed.

Therefore close-time values from prior closed positions are legitimately known
before the current trade opens. Their timing is clean; their semantic meaning
is only suspect because the historical SL/exit fields may reflect later
modification.

### Walk-forward after removing contaminated features

The full four-fold, two-track walk-forward was rerun after removing exactly the
four CONTAMINATED features. The SUSPECT history features were retained because
they use prior closed positions only.

Pooled PASS results:

| track | feature | n | rP/lot | trader CI | IP CI |
|---|---|---:|---:|---|---|
| A | `ip_cluster_size` | 369 | 67.7748 | [10.4028, 143.3167] | [8.1179, 144.4523] |
| A | `loss_streak` | 297 | 50.5244 | [2.8124, 100.1245] | [1.8325, 100.3607] |
| A | `manual_exit_rate_5` | 121 | 64.9123 | [5.1787, 120.6894] | [8.0552, 124.0516] |
| A | `pnl_ewm` | 1,086 | 41.0764 | [2.0047, 82.8330] | [2.6997, 82.2106] |
| A | `pnl_pct` | 1,102 | 49.0180 | [9.6677, 89.7553] | [9.7754, 88.4893] |
| A | `trader_prior_survival` | 374 | 69.9336 | [4.2307, 137.6970] | [3.8667, 143.0321] |
| A | `trades_per_hour` | 936 | 47.4105 | [5.4981, 89.3123] | [6.3158, 92.7390] |
| B | `ip_cluster_size` | 835 | 43.7181 | [5.2036, 89.9204] | [6.1015, 87.4156] |
| B | `pnl_ewm` | 2,172 | 30.9601 | [2.6545, 56.6419] | [5.8841, 56.8484] |
| B | `pnl_pct` | 2,169 | 36.8565 | [8.2186, 64.3898] | [11.3820, 63.1741] |
| B | `trader_prior_survival` | 955 | 41.5299 | [4.0038, 81.1146] | [2.0836, 81.2294] |
| B | `trades_per_hour` | 1,790 | 37.6032 | [7.9945, 67.8172] | [10.9772, 67.5290] |

Fold 4 has `901` Track-A validation rows and `1,590` Track-B validation rows.
No retained CLEAN or SUSPECT feature passes both clustered CIs in either
fold-4 cell. The highest point estimate in Track A is
`trader_prior_survival` (`n=12`, `231.8919` rP/lot) but its CIs are
`[-316.0755, 502.7235]` and `[-329.0605, 467.3187]`; the highest in Track B
is `manual_exit_rate_5` (`n=111`, `36.5931` rP/lot) with CIs
`[-17.3807, 87.5415]` and `[-15.5170, 90.6667]`. Both are underpowered, not
PASS.

## 5. Stage 2 figure verification

The fixed-input `feature_checks_walkforward.py` run reproduced the submitted
Stage 2 results. C41 and C66 remain outside C53-C65, with unchanged source row
counts of 1,227 and 1,911 respectively. The six features that PASS on both
tracks are shown below.
Track A also has two additional PASS features (`loss_streak` and
`manual_exit_rate_5`); they are not in the six-feature intersection.

| feature | track | n | rP/lot | trader CI | IP CI |
|---|---|---:|---:|---|---|
| `sl_distance_pct` | A | 354 | 163.2110 | [86.4453, 243.8121] | [90.1269, 240.3502] |
| `sl_distance_pct` | B | 711 | 122.8115 | [68.3875, 178.5113] | [67.3195, 182.7826] |
| `ip_cluster_size` | A | 369 | 67.7748 | [10.4028, 143.3167] | [8.1179, 144.4523] |
| `ip_cluster_size` | B | 835 | 43.7181 | [5.2036, 89.9204] | [6.1015, 87.4156] |
| `trader_prior_survival` | A | 374 | 69.9336 | [4.2307, 137.6970] | [3.8667, 143.0321] |
| `trader_prior_survival` | B | 955 | 41.5299 | [4.0038, 81.1146] | [2.0836, 81.2294] |
| `trades_per_hour` | A | 936 | 47.4105 | [5.4981, 89.3123] | [6.3158, 92.7390] |
| `trades_per_hour` | B | 1,790 | 37.6032 | [7.9945, 67.8172] | [10.9772, 67.5290] |
| `pnl_pct` | A | 1,102 | 49.0180 | [9.6677, 89.7553] | [9.7754, 88.4893] |
| `pnl_pct` | B | 2,169 | 36.8565 | [8.2186, 64.3898] | [11.3820, 63.1741] |
| `pnl_ewm` | A | 1,086 | 41.0764 | [2.0047, 82.8330] | [2.6997, 82.2106] |
| `pnl_ewm` | B | 2,172 | 30.9601 | [2.6545, 56.6419] | [5.8841, 56.8484] |

The fixed small-size holdout is unchanged:

| track | fold | n | rP/lot | trader CI | IP-cluster CI | verdict |
|---|---|---:|---:|---|---|---|
| A | Fold 3 | 8 | 250.8906 | [-115.1906, 857.4100] | [-115.1688, 825.0389] | FAIL |
| A | Fold 4 | 29 | -50.4870 | [-291.9270, 149.1037] | [-275.9735, 152.7298] | FAIL |
| B | Fold 3 | 23 | 135.1914 | [-36.3545, 356.7395] | [-35.8105, 350.5125] | FAIL |
| B | Fold 4 | 58 | -54.6879 | [-231.0837, 112.6846] | [-242.2970, 113.5926] | FAIL |

The final column in the holdout table is the overall PASS verdict; the two CI
columns are trader-clustered and IP-clustered respectively.

The remaining submitted figures also reproduce from the repaired positions:

| metric | verified value |
|---|---:|
| primary-era positions / active accounts / campaigns | 6,582 / 496 / 13 |
| size-weighted baseline rP/lot | -3.001388 -> -3.00 |
| equal-weighted baseline rP/lot | 5.436357 -> +5.44 |
| commission regression intercept | 0.001953 -> 0.0020 |
| commission regression slope | 34.991712 -> 34.9917 |
| commission regression R² | 0.999836 -> 0.9998 |

The same fixed run retained the expected fold sizes: raw validation rows
`949 / 1,033 / 973 / 1,590` and purged rows `371 / 454 / 464 / 901`.

Conclusion: the Stage 2 figures reproduce after the ingestion repair, but the
current-position SL/TP features must not be described as opening-ticket
features. The six common PASS features remain numerically intact; the SL
distance result is a close-time-exposed feature unless replaced by the
first-fill reconstruction, whose pooled signal is positive but whose fold-4
evidence is not conclusive.
