# TP/SL admissibility audit

Date: 2026-08-24  
Scope: the frozen `predict()` path on branch `stage3-submission`  
Source state: tag `stage3-submission-2026-08-21`

## Verdict

**CONTAMINATED: 2 features listed below**

The two features with transitive SL/TP-derived provenance are:

1. `sl_usage_rate_5` — consumes prior-position `slPrice` presence.
2. `manual_exit_rate_5` — consumes prior `exit_type`; in the standard position
   loader that label is derived from `closePrice`, `slPrice`, and `tpPrice`, and
   the public runtime has a fallback that derives it from those same columns.

There is also a feature-count discrepancy that must be resolved before claiming
that the submission uses 24 features: the source code used by `predict()` has
20, not 24, V2 features. `stage3_model.py:34-55` defines the contract,
`compute_v2_features()` returns exactly those fields (`features.py:381-412`),
and `_feature_frame()` projects exactly that list (`stage3_model.py:157-162`).
The four Stage 2 fields `prior_campaigns`, `trader_prior_tilt`,
`trader_prior_sl_discipline`, and `trader_prior_survival` are not in the
`predict()` feature contract. This report audits the 20 actually used fields.

## 1. Features actually used by `predict()`

The ordered source list is:

```text
loss_streak
win_streak
pnl_ewm
lot_zscore
amount
size_after_loss_delta
sl_usage_rate_5
manual_exit_rate_5
pnl_pct
dd_from_peak_pct
trade_index
log_dt_close
trades_per_hour
prior_campaigns_x_loss_streak_ge_2
shared_ip
ip_cluster_size
challenge_type
gold_vol_prev_day
same_direction_reentry
size_delta_ratio
```

`predict()` computes features first and calls `_update_position()` only after
decision preparation (`stage3_model.py:497-515`; `stage3_model.py:1381-1390`).
That ordering prevents the current row's outcome from updating state before its
own feature vector, but it does not remove close-time provenance from prior
state used by later rows.

## 2. Feature to raw-column map

Notation used below:

- `NP*` means `netProfit`, with the runtime fallback
  `profit + commission + swap` when `netProfit` is missing.
- `CLOSE*` means `closeDateTime` (or the runtime alias `closeTime`) used to
  decide whether the prior row can update state.
- A `prior` column means the value from an earlier closed position in the same
  `(campaignId, accountId)` state, not the current row.
- Metadata and daily-market fields are included with their raw provenance;
  their raw values are never emitted here.

| Feature | Raw columns consumed or transitive source | Close-time / TP-SL flag |
|---|---|---|
| `loss_streak` | prior `NP*`; prior `CLOSE*` update gate | Prior outcome-derived; no TP/SL |
| `win_streak` | prior `NP*`; prior `CLOSE*` update gate | Prior outcome-derived; no TP/SL |
| `pnl_ewm` | prior `NP*`; prior `CLOSE*` update gate | Prior outcome-derived; no TP/SL |
| `lot_zscore` | current `amount`; prior `amount`; prior `NP*` and `CLOSE*` update gate | Historical-state gate only; no TP/SL |
| `amount` | current `amount` | Clean; entry-time size |
| `size_after_loss_delta` | current `amount`; prior `amount`; prior `NP*` and `CLOSE*` update gate | Prior outcome-derived; no TP/SL |
| `sl_usage_rate_5` | prior `slPrice`; prior `NP*` and `CLOSE*` update gate | **SL-derived; contaminated** |
| `manual_exit_rate_5` | prior `exit_type` / `exitType`; if absent, prior `closePrice`, `slPrice`, `tpPrice`; prior `NP*` and `CLOSE*` update gate | **Exit label can be TP/SL-derived; contaminated** |
| `pnl_pct` | prior `NP*`; prior `CLOSE*` update gate; fixed artifact `start_balance` | Prior outcome-derived; no TP/SL |
| `dd_from_peak_pct` | prior `NP*`; prior `CLOSE*` update gate; fixed artifact `start_balance` | Prior outcome-derived; no TP/SL |
| `trade_index` | prior `NP*` and `CLOSE*` update gate | Prior close-gated count; no TP/SL |
| `log_dt_close` | current `openDateTime`; prior `closeDateTime` | Prior close-time timestamp; no TP/SL |
| `trades_per_hour` | current `openDateTime`; prior `openDateTime`; prior `NP*` and `CLOSE*` update gate for state count/first-open state | Prior close-gated state; no TP/SL |
| `prior_campaigns_x_loss_streak_ge_2` | current `campaignId`, current/prior `traderKey` for campaign history; prior `NP*` for loss streak; prior `CLOSE*` update gate | Prior outcome-derived component; no TP/SL |
| `shared_ip` | runtime `sharedIpFlag` or `shared_ip`; sanitized origin is trader-file `ip_address` and `account` | Metadata; no TP/SL |
| `ip_cluster_size` | runtime `ip_cluster_size` or `ipClusterSize`; sanitized origin is trader-file `ipClusterId`, derived from `ip_address`, and active `accountId`/`account` counts | Metadata; no TP/SL |
| `challenge_type` | runtime `challenge_type` or `challenge_type_id`; raw trader-file `challenge_type_id` | Metadata; no TP/SL |
| `gold_vol_prev_day` | runtime precomputed `gold_vol_prev_day`; standard build origin is `campaignDate` plus prior-day OHLC `high`, `low`, `close` | Prior-day market data; no TP/SL |
| `same_direction_reentry` | current `side`; prior `side` and prior `NP*`; prior `CLOSE*` update gate | Prior outcome-derived; no TP/SL |
| `size_delta_ratio` | current `amount`; prior `amount`; prior `NP*` and `CLOSE*` update gate | Prior outcome-derived; no TP/SL |

The state-update sources are visible in `stage3_model.py:431-465` and
`features.py:414-462`. In particular, `features.py:457-458` appends prior
`slPrice` presence and prior inferred/manual exit status to the deques read by
the two flagged features.

## 3. Close-time fields identified

| Field | Raw-schema status | Evidence and use in the predictor path |
|---|---|---|
| `closeDateTime` | Raw trade schema | Required by the raw schema (`pipeline.py:52-78`); gates `_update_position()` and becomes `last_close_time` (`stage3_model.py:431-434`, `features.py:416`, `features.py:459`). |
| `netProfit` | Raw trade schema | Used to update streaks, EWM, cumulative P&L, and prior outcome state (`stage3_model.py:435-443`; `features.py:418`, `features.py:429-461`). |
| `profit` | Raw trade schema | Fallback source for `netProfit` when `netProfit` is missing (`stage3_model.py:435-442`). |
| `commission` | Raw trade schema | Fallback component of `netProfit` (`stage3_model.py:436-441`). |
| `swap` | Raw trade schema | Fallback component of `netProfit` (`stage3_model.py:436-441`). |
| `closePrice` | Raw trade schema | Used for fallback exit inference against SL/TP (`stage3_model.py:444-454`); also used by the standard loader's `infer_exit_type()` (`pipeline.py:281-287`). |
| `slPrice` | Raw trade schema | Stored in prior state for `sl_usage_rate_5`; used in fallback and standard exit inference (`stage3_model.py:446-463`; `pipeline.py:281-287`). |
| `tpPrice` | Raw trade schema | Used in fallback and standard exit inference; therefore reaches prior `manual_exit_rate_5` through the exit label (`stage3_model.py:446-454`; `pipeline.py:281-287`). |
| `exit_type` | Derived position column, not a raw fill-schema field | `build_features.load_positions()` creates it from `closePrice`, `slPrice`, and `tpPrice` (`build_features.py:116-120`); `_update_position()` consumes it when present (`stage3_model.py:444-445`). |
| `exitType` | Alternate runtime input alias, not a raw fill-schema field | Read as an alternate to `exit_type` (`stage3_model.py:444-445`). |

The raw schema also contains close/outcome columns such as `reverseProfit`,
`durationSec`, `closeTradeId`, `closeOrderId`, and `closeTradeCrossPrice`.
They are not read by the `predict()` feature path. `reverseProfit` is not used
to update state; the runtime uses `netProfit` or its fallback instead.

The position collapse itself retains `closeDateTime` as the maximum and
aggregates `slPrice` and `tpPrice` with `first` after sorting by
`closeDateTime` (`pipeline.py:247-275`). The standard exit label then compares
collapsed `closePrice` with collapsed SL/TP (`pipeline.py:281-287`). Thus the
two flagged features inherit the source's close-time/position-collapse
semantics even though their values are consumed only on later rows.

## 4. Direct versus transitive contamination

### Current-row direct reads

There are **0** direct current-row TP/SL reads in `compute_v2_features()`.
`_entry_position()` projects only `campaignId`, `accountId`, `openDateTime`,
`amount`, `openPrice`, `side`, and the computed campaign count
(`stage3_model.py:414-428`). `compute_v2_features()` reads only those projected
entry values and prior state (`features.py:329-412`).

### Prior-state transitive reads

There are **2** features with TP/SL-derived provenance:

- `sl_usage_rate_5`: `TraderState.update()` appends
  `not is_missing(position["slPrice"])` to `last5_has_sl`; the feature is the
  mean of that deque (`features.py:352-354`, `features.py:457`).
- `manual_exit_rate_5`: `TraderState.update()` appends whether the prior
  `exit_type` is `manual`; the runtime derives a missing label by comparing
  `closePrice` to `slPrice` and then `tpPrice` (`stage3_model.py:444-454`,
  `features.py:356-358`, `features.py:457-458`). The normal position loader
  performs the same inference before `predict()`'s backtest path
  (`build_features.py:116-120`, `pipeline.py:281-287`).

Fourteen of the 20 features also use prior close-time outcome state through
`netProfit` or `closeDateTime`; those dependencies are listed in the map. They
are temporally prior to the current open and are distinct from TP/SL-derived
provenance. This report does not silently relabel those historical behavioral
state variables as entry-ticket TP/SL fields.

The static `_assert_no_feature_leakage()` check only rejects forbidden names if
they appear directly in `V2_FEATURES` and rejects them from the entry projection
(`stage3_model.py:147-154`). It does not inspect transitive dependencies inside
`TraderState.update()` or `infer_exit_type()`, which is why that guard does not
clear the two flagged features.

## 5. Implicit TP/SL reconstruction scan

No V2 feature computes a reward-to-risk ratio, target distance, expected R, or
profit-target percentage. The only ratio involving a trader-controlled value in
`compute_v2_features()` is:

```text
size_delta_ratio = current amount / prior amount
```

That is a position-size ratio and contains no price, SL, or TP term. The
`gold_vol_prev_day` ratio is the prior-day market range `(high - low) / close`,
not a trader target or stop distance. No V2 feature reads `openPrice` in its
formula, so no price-distance ratio can reconstruct a TP/SL level implicitly.

The TP/SL-derived path is categorical/history-based rather than an implicit
reward-to-risk ratio: `sl_usage_rate_5` uses SL presence, and
`manual_exit_rate_5` uses an exit label whose construction can compare the
close price with SL and TP.
