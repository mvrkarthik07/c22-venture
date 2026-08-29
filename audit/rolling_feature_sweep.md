# V2 rolling/expanding/account-history feature sweep

## Scope and verdict

The frozen artifact contains these 20 V2 feature names, in artifact/predict order
(stage3_model.py:34-55). Fifteen are history-dependent: they use a rolling,
expanding, or account/campaign-history state. Five are entry/context fields and
do not aggregate prior trades.

Under the requested rule—contaminated if a history-dependent feature consumes at
least one close-time field—**11 of 20 are CONTAMINATED and 9 of 20 are CLEAN**.
Therefore **9/20 survive** this audit.

For prior-trade columns, the classifications below use the requested C22 policy:
slPrice and tpPrice are treated as CLOSE-TIME fields. The exact source code
updates history only after the current feature row is produced
(stage3_model.py:497-515; features.py:414-462).

## Feature-to-prior-column map

| V2 feature | Aggregates prior trades? | Prior-trade columns/state consumed | Classification | Verdict |
|---|---|---|---|---|
| loss_streak | Yes; consecutive prior outcome suffix | netProfit (fallback: profit, commission, swap) | CLOSE-TIME | **CONTAMINATED** — realised outcome |
| win_streak | Yes; consecutive prior outcome suffix | netProfit (fallback: profit, commission, swap) | CLOSE-TIME | **CONTAMINATED** — realised outcome |
| pnl_ewm | Yes; expanding recursive history | netProfit (fallback: profit, commission, swap) | CLOSE-TIME | **CONTAMINATED** — realised outcome |
| lot_zscore | Yes; expanding prior amount statistics | prior amount | OPEN-TIME | **CLEAN** |
| amount | No; current trade only | none | current OPEN-TIME amount | **CLEAN** |
| size_after_loss_delta | Yes; prior amount mean plus prior loss-state history | prior amount; prior netProfit (fallback fields) to establish the loss streak | amount OPEN-TIME; outcome fields CLOSE-TIME | **CONTAMINATED** — prior realised outcome |
| sl_usage_rate_5 | Yes; last 3–5 prior updates in a max-5 deque | prior slPrice | CLOSE-TIME under the audit rule | **CONTAMINATED** — slPrice |
| manual_exit_rate_5 | Yes; last 3–5 prior updates in a max-5 deque | prior exit_type; inferred from closePrice, slPrice, and tpPrice when absent | CLOSE-TIME | **CONTAMINATED** — exit type and close/SL/TP inputs |
| pnl_pct | Yes; expanding cumulative history | prior netProfit (fallback fields) | CLOSE-TIME | **CONTAMINATED** — cumulative realised P&L |
| dd_from_peak_pct | Yes; expanding cumulative/peak history | prior netProfit (fallback fields) | CLOSE-TIME | **CONTAMINATED** — cumulative realised P&L |
| trade_index | Yes; count of prior state updates | prior row/update count; no prior column value | OPEN-TIME state count | **CLEAN** |
| log_dt_close | Yes; most recent prior close | prior closeDateTime | CLOSE-TIME | **CONTAMINATED** — closeDateTime |
| trades_per_hour | Yes; prior row count and first prior open timestamp | prior row/update count; earliest prior openDateTime; current openDateTime | OPEN-TIME | **CLEAN** |
| prior_campaigns_x_loss_streak_ge_2 | Yes; account/trader campaign history plus prior loss state | prior netProfit (fallback fields) via loss_streak; traderKey/campaignId account-history metadata | netProfit CLOSE-TIME; metadata OPEN-TIME | **CONTAMINATED** — prior realised outcome |
| shared_ip | No; current entry metadata only | none | current entry/context metadata | **CLEAN** |
| ip_cluster_size | No; current entry metadata only | none | current entry/context metadata | **CLEAN** |
| challenge_type | No; current entry metadata only | none | current OPEN-TIME/context metadata | **CLEAN** |
| gold_vol_prev_day | No; prior-day market context, not prior-trade history | none | known before entry; not a prior-trade column | **CLEAN** |
| same_direction_reentry | Yes; immediately preceding prior update | prior netProfit (fallback fields); prior side | netProfit CLOSE-TIME; side OPEN-TIME | **CONTAMINATED** — prior realised outcome |
| size_delta_ratio | Yes; immediately preceding prior amount | prior amount | OPEN-TIME | **CLEAN** |

The state dependencies are visible in features.py: prior outcomes update
loss_streak, win_streak, cumulative P&L, and pnl_ewm (features.py:429-451);
prior amounts update the amount statistics (features.py:453-470); and prior
close/exit fields update last_close_time, last_net_profit, and the two rolling
deques (features.py:414-462).

## Overlap rate for each contaminated feature's own window

For each row, I counted prior state-update rows in that feature's actual
dependency support with closeDateTime > current openDateTime. The rate is
overlap >= 1 / computed n. This is not a uniform five-row calculation:

- streak features use the immediately preceding consecutive streak, plus the
  immediately preceding reset row when the current streak is zero;
- pnl_ewm, pnl_pct, and dd_from_peak_pct use all prior state updates;
- size_after_loss_delta uses the union of prior amount history and prior
  loss-state history; for computed rows this spans all prior updates up to the
  current row;
- sl_usage_rate_5 and manual_exit_rate_5 use the most recent 3–5 prior updates,
  with a minimum of 3;
- log_dt_close and same_direction_reentry use the immediately preceding prior
  update;
- prior_campaigns_x_loss_streak_ge_2 uses the loss-streak support for its
  close-time dependency; its campaign-count component is account metadata.

| feature | support window summary | full: computed n | full: overlap >=1 n (%) | <=C52: n, overlap n (%) | C53-C66: n, overlap n (%) | 177 acted: n, overlap n (%) |
|---|---|---:|---:|---:|---:|---:|
| loss_streak | prior loss suffix/reset; support size 0–9, median 1 | 7,277 | 2,112 (29.02%) | 694, 91 (13.11%) | 6,583, 2,021 (30.70%) | 177, 123 (69.49%) |
| win_streak | prior win suffix/reset; support size 0–10, median 1 | 7,277 | 2,102 (28.89%) | 694, 92 (13.26%) | 6,583, 2,010 (30.53%) | 177, 110 (62.15%) |
| pnl_ewm | all prior outcomes; support size 0–56, median 1 | 7,277 | 2,601 (35.74%) | 694, 92 (13.26%) | 6,583, 2,509 (38.11%) | 177, 128 (72.32%) |
| size_after_loss_delta | prior amount plus loss-state history; computed n=1,325 | 1,325 | 869 (65.58%) | 9, 7 (77.78%) | 1,316, 862 (65.50%) | 88, 66 (75.00%) |
| sl_usage_rate_5 | most recent 3–5 prior updates | 2,414 | 1,529 (63.34%) | 9, 8 (88.89%) | 2,405, 1,521 (63.24%) | 123, 89 (72.36%) |
| manual_exit_rate_5 | most recent 3–5 prior updates | 2,414 | 1,529 (63.34%) | 9, 8 (88.89%) | 2,405, 1,521 (63.24%) | 123, 89 (72.36%) |
| pnl_pct | all prior outcomes; support size 0–56, median 1 | 7,277 | 2,601 (35.74%) | 694, 92 (13.26%) | 6,583, 2,509 (38.11%) | 177, 128 (72.32%) |
| dd_from_peak_pct | all prior outcomes; support size 0–56, median 1 | 7,277 | 2,601 (35.74%) | 694, 92 (13.26%) | 6,583, 2,509 (38.11%) | 177, 128 (72.32%) |
| log_dt_close | immediately preceding prior close; support size 1 | 4,601 | 1,999 (43.45%) | 136, 91 (66.91%) | 4,465, 1,908 (42.73%) | 177, 110 (62.15%) |
| prior_campaigns_x_loss_streak_ge_2 | loss-streak support; campaign count is metadata | 7,277 | 2,112 (29.02%) | 694, 91 (13.11%) | 6,583, 2,021 (30.70%) | 177, 123 (69.49%) |
| same_direction_reentry | immediately preceding outcome/direction; support size 0–1 | 7,277 | 1,999 (27.47%) | 694, 91 (13.11%) | 6,583, 1,908 (28.98%) | 177, 110 (62.15%) |

The full-dataset rates are the primary rates for this sweep. Eval and acted
columns are included because their history lengths and overlap patterns differ.

## Why only 2,414 five-trade windows were computed

The 2,414 figure is not the full dataset size. It is the denominator of
currently non-missing sl_usage_rate_5 and manual_exit_rate_5 values:

- full frozen position stream passed to predict(): n=7,277 positions;
- rows with either five-trade feature computed: n=2,414;
- rows without either feature: 7,277 - 2,414 = 4,863;
- missing-account rows: n=0;
- missing openDateTime, closeDateTime, or netProfit rows in the loaded position
  stream: n=0 each;
- rows filtered before this stream: n=0 for this audit.

The missing 4,863 rows are absent because their campaign/account state had
fewer than the minimum three prior updates. The frozen code checks
len(last5_has_sl) >= 3 and len(last5_manual_exit) >= 3 (features.py:352-358),
while the deque itself has maximum length five. The same result holds exactly
for both fields: computed values have lookback sizes 3 (n=547), 4 (n=410), or
5 (n=1,457).

For the eval-only denominator, C53–C66 contains n=6,583 positions and n=2,405
five-trade values; n=4,178 are absent for the same insufficient-history reason.
The 177 acted set contains n=123 computed five-trade values; the other 54 acted
rows are not missing due account or timestamp data—they simply have fewer than
three prior campaign/account updates.

## Final count

**CONTAMINATED: 11 features. CLEAN: 9 features. V2 survivors under the
close-time overlap rule: 9/20.**
