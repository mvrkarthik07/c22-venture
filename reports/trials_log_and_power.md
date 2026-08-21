# Stage 3 trials log, multiple testing, power, and narrow conditional search

Date: 20 Aug 2026  
Data: repaired ingestion, `46,520` fills -> `7,277` positions  
Mandated split: fit/select on `C33-C52` (`694` positions, `330` accounts); evaluate on
`C53-C66` (`6,583` positions, `496` accounts).  
Target: `reverseProfit per lot = gross_loss_per_lot - 7.00`; the `$7` cost is already
inside the target and is subtracted exactly once. Hurdle: `0.00`.

## 1. Admissibility and uncertainty convention

The admissible set has 24 features. The following four are excluded as close-time
contaminated: `sl_distance_pct`, `sl_widening_delta`, `has_sl`, and `has_tp`.
The attempted recovery feature `sl_distance_pct_at_open` is also excluded: the
recovery audit disproved it (first-fill direction violations `11.98%`, stop values
changed mid-trade in `73.12%` of positions, and violating rows were profitable at
`-68.53/lot` with a `57.12%` win rate). `sl_usage_rate_5`,
`manual_exit_rate_5`, and `trader_prior_sl_discipline` remain admissible because
they use only prior closed positions.

All intervals and bootstrap p-values below use `n_boot=2,000`, seed `7`, and
cluster resampling by `traderKey` with the existing campaign-account fallback for
missing keys. `ipClusterId` clustering is shown as a secondary robustness check.
The p-value is the requested two-sided bootstrap value:
`max(2 * fraction(bootstrap mean <= 0), 1/n_boot)`, capped at `1`.

## 2. Trials log

The repository reconstruction used the Stage 1 `condition_masks()`/`checks.py`,
the Stage 2 walk-forward report and `feature_checks_walkforward.py`,
`family_g_value.py`, `FEATURES.md`, and the SL recovery report. The four H5
boundary probes are retained in the ledger as rejected tests: Rule-B breach,
the 4% drawdown boundary, the 8% target boundary, and the ATLSR boundary.

| family of tests | count | what was varied | cumulative count |
|---|---:|---|---:|
| Stage 1 pre-registered behavioral triggers | 10 | no-SL, loss streak, re-entry, sizing, drawdown, and session trigger definitions | 10 |
| Stage 1 rejected H5 boundary tests | 4 | Rule-B, 4% drawdown, 8% target, and ATLSR boundary probes | 14 |
| Stage 2 original walk-forward feature tests | 56 | 28 frozen features x Track A/Track B; 48 remain admissible and 8 are now invalidated | 70 |
| Stage 2 composite trigger tests | 4 | `loss_streak >= 2` and `loss_streak >= 2 AND amount <= 0.2`, each on both tracks | 74 |
| Stage 2 threshold-protocol tests | 4 | unconstrained train-selected versus minimum-support `n>=30`, each on both tracks | 78 |
| Ridge model variants | 6 | M1/M2/M3 x Track A/Track B | 84 |
| `sl_distance_pct_at_open` recovery test | 1 | first-fill recovery attempt and feature check | 85 |
| Stage 3 narrow conditional search | 12 | six pre-registered states x S1/S2 threshold source | 97 |
| Stage 3 cold-start model variants | 4 | V1/V2 x Track A/Track B | 101 |

The running inventory is therefore **101 trials**. The BH family below contains
**90 outcome tests with a defined zero-edge null**: 14 Stage 1 tests, 56
historical Stage 2 feature tests, 4 composites, 4 threshold protocols, and 12
conditional tests. Ridge comparisons, the recovery diagnosis, and V1/V2 are
logged model/diagnostic comparisons rather than scalar mean tests, so assigning
them artificial zero-edge p-values would be misleading; they are not silently
treated as additional null tests. Baselines and the correlation-prune matrix
are benchmarks/screening comparisons, not outcome hypotheses.

The eight invalidated historical Stage 2 feature tests are retained in the
90-test full-log correction but are not part of the admissible correction:

| invalidated feature | Track A raw p | Track B raw p | full-log BH q | status |
|---|---:|---:|---:|---|
| `has_sl` | 1.0000 | 0.8090 | 1.0000 | contaminated; excluded |
| `has_tp` | 1.0000 | 0.9330 | 1.0000 | contaminated; excluded |
| `sl_distance_pct` | 0.0005 | 0.0005 | 0.0225 | contaminated; invalid full-log survivor |
| `sl_widening_delta` | 0.2590 | 0.1070 | 0.4823 | contaminated; excluded |

## 3. Stage 2 BH correction: admissible 24-feature family

BH is applied at `q=0.05` separately within Track A (`24` tests), within Track
B (`24` tests), and jointly across both tracks (`48` tests). No admissible
feature survives any of the three corrections. The table reports account-
clustered p-values and adjusted q-values; IP-clustered intervals are secondary.

| feature | track | n | mean rP/lot | account 95% CI | IP 95% CI | raw p | BH q track | BH q joint | track | joint |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `loss_streak` | A | 297 | 50.524 | [2.812, 100.125] | [1.832, 100.361] | 0.0370 | 0.1371 | 0.1600 | FAIL | FAIL |
| `win_streak` | A | 1956 | 24.215 | [-1.864, 51.372] | [-1.137, 51.737] | 0.0690 | 0.2070 | 0.2366 | FAIL | FAIL |
| `pnl_ewm` | A | 1086 | 41.076 | [2.005, 82.833] | [2.700, 82.211] | 0.0400 | 0.1371 | 0.1600 | FAIL | FAIL |
| `lot_zscore` | A | 129 | 15.115 | [-49.990, 90.278] | [-49.717, 87.412] | 0.7000 | 0.8842 | 0.9600 | FAIL | FAIL |
| `amount` | A | 385 | 1.026 | [-107.716, 109.060] | [-102.458, 112.478] | 0.9650 | 1.0000 | 1.0000 | FAIL | FAIL |
| `size_after_loss_delta` | A | 55 | 43.325 | [-85.239, 179.275] | [-82.910, 182.466] | 0.5420 | 0.7722 | 0.7956 | FAIL | FAIL |
| `sl_usage_rate_5` | A | 257 | 12.500 | [-30.243, 60.045] | [-25.622, 63.089] | 0.5920 | 0.7893 | 0.8358 | FAIL | FAIL |
| `manual_exit_rate_5` | A | 121 | 64.912 | [5.179, 120.689] | [8.055, 124.052] | 0.0340 | 0.1371 | 0.1600 | FAIL | FAIL |
| `pnl_pct` | A | 1102 | 49.018 | [9.668, 89.755] | [9.775, 88.489] | 0.0110 | 0.1371 | 0.1600 | FAIL | FAIL |
| `dd_from_peak_pct` | A | 983 | -9.711 | [-44.241, 25.920] | [-40.317, 23.744] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `trade_index` | A | 350 | -5.672 | [-41.252, 29.605] | [-40.854, 30.680] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `log_dt_close` | A | 473 | 28.227 | [-16.503, 76.557] | [-14.434, 73.875] | 0.1940 | 0.3326 | 0.3880 | FAIL | FAIL |
| `trades_per_hour` | A | 936 | 47.410 | [5.498, 89.312] | [6.316, 92.739] | 0.0300 | 0.1371 | 0.1600 | FAIL | FAIL |
| `prior_campaigns` | A | 2108 | 20.427 | [-5.225, 46.690] | [-3.082, 47.186] | 0.1180 | 0.2400 | 0.3032 | FAIL | FAIL |
| `prior_campaigns_x_loss_streak_ge_2` | A | 2190 | 21.711 | [-2.646, 47.433] | [-1.048, 47.844] | 0.0790 | 0.2107 | 0.2528 | FAIL | FAIL |
| `shared_ip` | A | 652 | -1.787 | [-37.976, 35.146] | [-36.280, 32.348] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `ip_cluster_size` | A | 369 | 67.775 | [10.403, 143.317] | [8.118, 144.452] | 0.0190 | 0.1371 | 0.1600 | FAIL | FAIL |
| `challenge_type` | A | 1607 | -0.043 | [-26.398, 27.925] | [-27.102, 27.246] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `gold_vol_prev_day` | A | 994 | 9.640 | [-23.178, 44.252] | [-23.182, 45.494] | 0.5470 | 0.7722 | 0.7956 | FAIL | FAIL |
| `same_direction_reentry` | A | 1742 | 21.669 | [-6.155, 51.589] | [-5.113, 50.590] | 0.1200 | 0.2400 | 0.3032 | FAIL | FAIL |
| `size_delta_ratio` | A | 271 | 41.114 | [-17.320, 108.951] | [-15.809, 106.421] | 0.1700 | 0.3138 | 0.3673 | FAIL | FAIL |
| `trader_prior_tilt` | A | 2175 | 21.177 | [-3.098, 46.690] | [-1.611, 47.262] | 0.0890 | 0.2136 | 0.2670 | FAIL | FAIL |
| `trader_prior_sl_discipline` | A | 1935 | 14.676 | [-12.406, 42.456] | [-11.172, 42.073] | 0.2780 | 0.4448 | 0.4766 | FAIL | FAIL |
| `trader_prior_survival` | A | 373 | 70.630 | [4.704, 138.501] | [4.340, 144.273] | 0.0370 | 0.1371 | 0.1600 | FAIL | FAIL |
| `loss_streak` | B | 598 | 18.792 | [-13.093, 53.111] | [-12.672, 51.738] | 0.2460 | 0.4929 | 0.4723 | FAIL | FAIL |
| `win_streak` | B | 3988 | 15.018 | [-3.204, 33.252] | [-2.755, 33.330] | 0.1030 | 0.3531 | 0.2908 | FAIL | FAIL |
| `pnl_ewm` | B | 2172 | 30.960 | [2.654, 56.642] | [5.884, 56.848] | 0.0310 | 0.1488 | 0.1600 | FAIL | FAIL |
| `lot_zscore` | B | 346 | -15.794 | [-67.246, 37.217] | [-63.007, 33.086] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `amount` | B | 719 | 44.217 | [-31.295, 127.327] | [-31.329, 120.303] | 0.2640 | 0.4929 | 0.4747 | FAIL | FAIL |
| `size_after_loss_delta` | B | 144 | -5.549 | [-85.102, 78.037] | [-82.926, 73.928] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `sl_usage_rate_5` | B | 568 | -11.136 | [-41.229, 19.918] | [-40.330, 18.921] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `manual_exit_rate_5` | B | 346 | 15.981 | [-29.479, 64.258] | [-30.472, 65.886] | 0.4950 | 0.7920 | 0.7920 | FAIL | FAIL |
| `pnl_pct` | B | 2169 | 36.857 | [8.219, 64.390] | [11.382, 63.174] | 0.0120 | 0.1440 | 0.1600 | FAIL | FAIL |
| `dd_from_peak_pct` | B | 1947 | -11.802 | [-33.984, 9.645] | [-34.203, 12.025] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `trade_index` | B | 780 | 15.011 | [-12.739, 47.700] | [-13.763, 44.371] | 0.2670 | 0.4929 | 0.4747 | FAIL | FAIL |
| `log_dt_close` | B | 1102 | -1.890 | [-29.603, 27.894] | [-31.212, 28.090] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `trades_per_hour` | B | 1790 | 37.603 | [7.994, 67.817] | [10.977, 67.529] | 0.0100 | 0.1440 | 0.1600 | FAIL | FAIL |
| `prior_campaigns` | B | 2568 | 22.250 | [-1.051, 44.162] | [0.085, 45.560] | 0.0650 | 0.2600 | 0.2366 | FAIL | FAIL |
| `prior_campaigns_x_loss_streak_ge_2` | B | 4543 | 12.117 | [-5.019, 29.700] | [-4.874, 30.085] | 0.1580 | 0.4213 | 0.3611 | FAIL | FAIL |
| `shared_ip` | B | 652 | -1.787 | [-36.456, 34.095] | [-36.819, 34.891] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `ip_cluster_size` | B | 835 | 43.718 | [5.204, 89.920] | [6.102, 87.416] | 0.0250 | 0.1488 | 0.1600 | FAIL | FAIL |
| `challenge_type` | B | 3044 | -2.016 | [-20.591, 15.913] | [-20.353, 17.108] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `gold_vol_prev_day` | B | 2014 | -3.447 | [-26.483, 18.472] | [-24.231, 17.520] | 1.0000 | 1.0000 | 1.0000 | FAIL | FAIL |
| `same_direction_reentry` | B | 3655 | 12.965 | [-6.503, 32.619] | [-7.708, 33.038] | 0.1760 | 0.4224 | 0.3673 | FAIL | FAIL |
| `size_delta_ratio` | B | 609 | 14.355 | [-29.635, 60.638] | [-30.274, 56.824] | 0.5300 | 0.7950 | 0.7956 | FAIL | FAIL |
| `trader_prior_tilt` | B | 4039 | 14.543 | [-4.154, 33.486] | [-4.798, 34.049] | 0.1270 | 0.3810 | 0.3048 | FAIL | FAIL |
| `trader_prior_sl_discipline` | B | 2189 | 10.699 | [-14.544, 34.361] | [-13.319, 35.705] | 0.3790 | 0.6497 | 0.6273 | FAIL | FAIL |
| `trader_prior_survival` | B | 897 | 48.597 | [6.667, 92.232] | [6.629, 90.664] | 0.0240 | 0.1488 | 0.1600 | FAIL | FAIL |

No admissible feature survives. At the full 90-test correction, the only
survivors are the two invalidated `sl_distance_pct` tests (`q=0.0225` on each
track); therefore there is **no valid Stage 2 survivor**.

## 4. Stage 1 tests and full-log correction

The Stage 1 trigger results below are reported in the required reverseProfit
units. Their full-log q-values include all 90 outcome tests.

| Stage 1 test | n | mean rP/lot | account 95% CI | raw p | full-log q |
|---|---:|---:|---:|---:|---:|
| no SL set | 1569 | 0.171 | [-34.853, 34.508] | 1.0000 | 1.0000 |
| loss_streak >= 2 | 881 | 33.538 | [4.364, 63.215] | 0.0230 | 0.1636 |
| loss_streak >= 3 | 346 | 30.466 | [-12.817, 72.891] | 0.1740 | 0.4062 |
| same side after SL hit | 537 | 0.659 | [-37.441, 40.854] | 0.9790 | 1.0000 |
| fast re-entry after loss (<=60s) | 1324 | 1.486 | [-20.036, 23.547] | 0.8800 | 1.0000 |
| size escalation (lot_ratio > 1.5) | 1071 | 9.071 | [-14.842, 34.484] | 0.4560 | 0.8208 |
| near rule-B cliff (lot_ratio > 2.0) | 674 | 1.809 | [-23.408, 27.890] | 0.8560 | 1.0000 |
| deep drawdown (dd > 2%) | 1455 | -4.762 | [-26.635, 16.232] | 1.0000 | 1.0000 |
| late session (session_pct > 0.75) | 1219 | 5.374 | [-28.017, 36.729] | 0.7560 | 1.0000 |
| late + underwater | 657 | 14.451 | [-27.918, 58.461] | 0.5460 | 0.8791 |
| H5 Rule-B breach (>2.5x) | 454 | -9.355 | [-41.508, 23.584] | 1.0000 | 1.0000 |
| H5 drawdown boundary (>=4%) | 749 | -2.345 | [-32.874, 25.788] | 1.0000 | 1.0000 |
| H5 target boundary (>=8%) | 76 | -16.176 | [-117.853, 58.923] | 1.0000 | 1.0000 |
| H5 ATLSR boundary (>=2.5x) | 2934 | -4.917 | [-23.889, 13.915] | 1.0000 | 1.0000 |

Stage 2 composites and threshold protocols were also included in the full
correction. Their largest positive cells were `loss_streak>=2 AND amount<=0.2`
at `169.815/lot` on Track A and `108.115/lot` on Track B, but none survives
the full-log q correction. The `n>=30` threshold protocol had raw p-values
`0.025` (Track A) and `0.019` (Track B), but neither survives the full log.

## 5. Power and minimum detectable effect

The design-annex inputs are primary-era raw sigma `555.3263`, winsorized sigma
`482.4515`, traderKey ICC `0.162328` / DEFF `1.753221`, and ipClusterId ICC
`0.096472` / DEFF `1.615386`. The formula is

`MDE = 2.801585 * sigma * sqrt(DEFF / n)`

for two-sided alpha `0.05` and power `0.80`.

| n basis | positions | traderKey raw | traderKey winsorized | ipClusterId raw | ipClusterId winsorized |
|---|---:|---:|---:|---:|---:|
| mandated training | 694.0 | $78.20 | $67.94 | $75.06 | $65.21 |
| evaluation at 5% coverage | 329.2 | $113.55 | $98.65 | $108.99 | $94.69 |
| evaluation at 10% coverage | 658.3 | $80.29 | $69.75 | $77.07 | $66.96 |
| evaluation at 20% coverage | 1316.6 | $56.77 | $49.32 | $54.50 | $47.34 |
| evaluation at 50% coverage | 3291.5 | $35.91 | $31.19 | $34.47 | $29.94 |
| evaluation at 100% coverage | 6583.0 | $25.39 | $22.06 | $24.37 | $21.17 |

The mandated training MDE does **not** exceed the largest observed Stage 1–2
effect (`169.815/lot`), but it is above almost every individual admissible
feature effect. Thus a null on the mandated split would be weak evidence about
small or moderate edges, not evidence that those edges do not exist.

### MDE against every admissible pooled Stage 2 effect

The detection floor for this comparison is the primary account-clustered,
winsorized training MDE: `$67.94/lot`. Only one of 48 admissible pooled
feature-track effects is above it.

| feature | Track A effect | A vs floor | Track B effect | B vs floor |
|---|---:|---|---:|---|
| `loss_streak` | 50.524 | BELOW | 18.792 | BELOW |
| `win_streak` | 24.215 | BELOW | 15.018 | BELOW |
| `pnl_ewm` | 41.076 | BELOW | 30.960 | BELOW |
| `lot_zscore` | 15.115 | BELOW | -15.794 | BELOW |
| `amount` | 1.026 | BELOW | 44.217 | BELOW |
| `size_after_loss_delta` | 43.325 | BELOW | -5.549 | BELOW |
| `sl_usage_rate_5` | 12.500 | BELOW | -11.136 | BELOW |
| `manual_exit_rate_5` | 64.912 | BELOW | 15.981 | BELOW |
| `pnl_pct` | 49.018 | BELOW | 36.857 | BELOW |
| `dd_from_peak_pct` | -9.711 | BELOW | -11.802 | BELOW |
| `trade_index` | -5.672 | BELOW | 15.011 | BELOW |
| `log_dt_close` | 28.227 | BELOW | -1.890 | BELOW |
| `trades_per_hour` | 47.410 | BELOW | 37.603 | BELOW |
| `prior_campaigns` | 20.427 | BELOW | 22.250 | BELOW |
| `prior_campaigns_x_loss_streak_ge_2` | 21.711 | BELOW | 12.117 | BELOW |
| `shared_ip` | -1.787 | BELOW | -1.787 | BELOW |
| `ip_cluster_size` | 67.775 | BELOW | 43.718 | BELOW |
| `challenge_type` | -0.043 | BELOW | -2.016 | BELOW |
| `gold_vol_prev_day` | 9.640 | BELOW | -3.447 | BELOW |
| `same_direction_reentry` | 21.669 | BELOW | 12.965 | BELOW |
| `size_delta_ratio` | 41.114 | BELOW | 14.355 | BELOW |
| `trader_prior_tilt` | 21.177 | BELOW | 14.543 | BELOW |
| `trader_prior_sl_discipline` | 14.676 | BELOW | 10.699 | BELOW |
| `trader_prior_survival` | 70.630 | ABOVE | 48.597 | BELOW |

Observed effects above the mandated training detection floor: **1/48**.

## 6. Pre-registered narrow conditional search

The candidate list was fixed at six states before evaluating results; no state was
added after inspection:

1. `loss_streak >= 2 AND trades_per_hour in [20, 60]`
2. `loss_streak >= 2 AND pnl_pct in [-0.033, 0]`
3. `pnl_ewm in [-31.428, 0] AND trade_index <= 3`
4. `prior_campaigns == 0 AND loss_streak >= 2`
5. `ip_cluster_size <= 3 AND loss_streak >= 2`
6. `loss_streak >= 2 AND manual_exit_rate_5 in [0.25, 0.75]`

The operational `pnl_ewm` band is the slightly-negative Stage 2 bucket edge
(`-31.428` to zero). “Mid manual-exit band” is fixed as `0.25` to `0.75`.
These are all admissible fields.

S1 uses a fixed train-only selector: candidate boundaries were specified before
the evaluation readout and the candidate with the largest training mean rP/lot
was selected, requiring `n>=30` when attainable and falling back to the best
nonempty candidate when the training field had no support. The selected S1
thresholds were: state 1 `(loss>=1, trades/hr 0-40)`, state 2
`(loss>=1, pnl_pct -0.01 to 0)`, state 3 `(pnl_ewm -100 to 10, index<=3)`,
state 4 `loss>=1`, state 5 `(ip size<=15, loss>=1)`, and state 6
`(loss>=1, manual-exit 0.50-0.75)`. S1 is explicitly underpowered: its
training-side MDE is `$65-$78/lot`.

The fixed S1 candidate grid was: loss-streak cut `{1,2,3}`; trades/hour lower
cut `{0,10,20,30,40}` and upper cut `{40,50,60,80,100}`; pnl-percent lower
cut `{-0.05,-0.033,-0.02,-0.01,0}` and upper cut `{0,0.01,0.02}`;
negative-EWM lower cut `{-100,-50,-30,-10,-5,-1}`, upper cut `{0,5,10}`;
trade-index cap `{2,3,4,5}`; IP-size cap `{2,3,5,10,15}`; and manual-exit
lower/upper cuts from `{0,0.25,0.5}` / `{0.5,0.75,1}`. No additional
candidate was introduced after the evaluation results were observed.

S2 carries forward the Stage 1–2 thresholds listed above. These thresholds were
derived using C53-C65, which is the mandated evaluation window; S2 is therefore
**leaky under the mandated split** and is shown only as a provenance disclosure.

| source | state | n | coverage | mean rP/lot | account 95% CI | IP 95% CI | raw p | BH q across 12 | full-log q | account CI clears zero? |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S1 | 1 | 2158 | 32.78% | 9.062 | [-11.646, 29.520] | [-11.258, 29.115] | 0.3890 | 0.5835 | 0.7145 | No |
| S1 | 2 | 357 | 5.42% | -7.794 | [-70.196, 53.299] | [-75.823, 55.570] | 1.0000 | 1.0000 | 1.0000 | No |
| S1 | 3 | 3250 | 49.37% | 21.552 | [-1.915, 45.110] | [-1.029, 43.367] | 0.0660 | 0.2260 | 0.2475 | No |
| S1 | 4 | 1035 | 15.72% | 19.290 | [-11.225, 50.295] | [-11.354, 51.242] | 0.2310 | 0.3960 | 0.5071 | No |
| S1 | 5 | 1718 | 26.10% | 5.620 | [-18.146, 28.810] | [-17.197, 29.560] | 0.6550 | 0.8733 | 1.0000 | No |
| S1 | 6 | 406 | 6.17% | 4.537 | [-35.380, 44.538] | [-36.960, 44.879] | 0.8860 | 0.9665 | 1.0000 | No |
| S2 | 1 | 71 | 1.08% | 67.095 | [-9.536, 169.380] | [-5.384, 164.019] | 0.0920 | 0.2260 | 0.2957 | No |
| S2 | 2 | 203 | 3.08% | 11.177 | [-63.094, 82.632] | [-67.383, 84.801] | 0.7640 | 0.9168 | 1.0000 | No |
| S2 | 3 | 2665 | 40.48% | 34.306 | [7.987, 61.207] | [8.323, 59.628] | 0.0060 | 0.0720 | 0.1636 | Yes |
| S2 | 4 | 391 | 5.94% | 51.961 | [7.689, 94.896] | [5.954, 95.984] | 0.0240 | 0.1440 | 0.1636 | Yes |
| S2 | 5 | 338 | 5.13% | 39.747 | [-11.658, 88.208] | [-12.252, 90.176] | 0.1130 | 0.2260 | 0.3176 | No |
| S2 | 6 | 331 | 5.03% | 36.068 | [-8.622, 79.090] | [-9.443, 82.275] | 0.1100 | 0.2260 | 0.3176 | No |

No state survives the 12-state BH correction or the full-log correction. States
S2-3 and S2-4 clear zero unadjusted under both clustering schemes, so their
campaign breakdowns are shown rather than suppressed.

### Per-campaign breakdown for S2-3

| campaign | n | mean rP/lot |
|---:|---:|---:|
| C53 | 219 | 158.909 |
| C54 | 217 | 26.596 |
| C55 | 189 | -70.580 |
| C56 | 203 | -52.052 |
| C57 | 181 | 93.872 |
| C58 | 175 | 78.315 |
| C59 | 229 | 83.356 |
| C60 | 216 | 103.348 |
| C61 | 231 | 31.464 |
| C62 | 195 | -0.397 |
| C63 | 201 | -3.964 |
| C64 | 210 | 10.183 |
| C65 | 198 | -29.654 |
| C66 | 1 | -8.694 |

This is not a one-campaign result: several campaigns are positive, but C55,
C56, C62-C65 are negative or near zero and the account-cluster interval still
has substantial uncertainty.

### Per-campaign breakdown for S2-4

| campaign | n | mean rP/lot |
|---:|---:|---:|
| C53 | 46 | 54.121 |
| C54 | 30 | 123.696 |
| C55 | 28 | 109.918 |
| C56 | 33 | 22.949 |
| C57 | 31 | 53.539 |
| C58 | 7 | -231.774 |
| C59 | 34 | 57.234 |
| C60 | 22 | 126.938 |
| C61 | 35 | 84.013 |
| C62 | 19 | 14.098 |
| C63 | 46 | -8.527 |
| C64 | 33 | 34.152 |
| C65 | 27 | 57.862 |

The result is not carried by one campaign, but it is visibly fragile: C58 has
only seven rows and a large negative mean, while C63 is negative. This is an
unadjusted S2 result and remains leaky by construction.

### MDE at each conditional-state coverage

| source | state | n | coverage | trader raw | trader winsorized | IP raw | IP winsorized |
|---|---:|---:|---:|---:|---:|---:|---:|
| S1 | 1 | 2158 | 32.78% | $44.34 | $38.53 | $42.57 | $36.98 |
| S1 | 2 | 357 | 5.42% | $109.03 | $94.72 | $104.65 | $90.92 |
| S1 | 3 | 3250 | 49.37% | $36.14 | $31.39 | $34.69 | $30.13 |
| S1 | 4 | 1035 | 15.72% | $64.03 | $55.63 | $61.46 | $53.40 |
| S1 | 5 | 1718 | 26.10% | $49.70 | $43.18 | $47.71 | $41.45 |
| S1 | 6 | 406 | 6.17% | $102.24 | $88.82 | $98.14 | $85.26 |
| S2 | 1 | 71 | 1.08% | $244.48 | $212.40 | $234.67 | $203.88 |
| S2 | 2 | 203 | 3.08% | $144.58 | $125.61 | $138.78 | $120.57 |
| S2 | 3 | 2665 | 40.48% | $39.90 | $34.67 | $38.30 | $33.28 |
| S2 | 4 | 391 | 5.94% | $104.18 | $90.51 | $100.00 | $86.88 |
| S2 | 5 | 338 | 5.13% | $112.05 | $97.35 | $107.56 | $93.44 |
| S2 | 6 | 331 | 5.03% | $113.23 | $98.37 | $108.69 | $94.42 |

## 7. Amendment A: mandated-training correlation prune

The unchanged pre-committed rule `|rho| > 0.90` was rerun on the mandated
training rows (`C33-C52`, `n=694`) over the 24 admissible features plus a
restored `is_cold_start` indicator. `challenge_type` is categorical and is not
in the Spearman matrix. `sl_usage_rate_5` has no variation in the training
rows where it is observed, so its correlations are undefined.

| pair | Spearman rho | action under the frozen rule |
|---|---:|---|
| `loss_streak` / `dd_from_peak_pct` | 0.9562 | drop `dd_from_peak_pct`; retain older streak feature |
| `pnl_ewm` / `pnl_pct` | 0.9627 | drop `pnl_pct`; retain older EWM feature |
| `lot_zscore` / `size_after_loss_delta` | 1.0000 | drop `size_after_loss_delta`; retain older sizing feature |
| `trade_index` / `trades_per_hour` | -0.9751 | drop `trades_per_hour`; retain older index feature |
| `prior_campaigns` / `is_cold_start` | -0.9870 | drop `is_cold_start`; retain `prior_campaigns` |

The last correlation is materially stronger than the `-0.9026` value from the
C53-C65 fold-training calculation. The mandated prelude therefore changes the
mechanical prune outcome: applying the unchanged rule to this split drops five
features (`dd_from_peak_pct`, `pnl_pct`, `size_after_loss_delta`,
`trades_per_hour`, and `is_cold_start`). Pairs between `|rho|=0.74` and `0.90`
remain retained for regularization.

Full numeric correlation matrix (training rows, Spearman rho; `n/a` means
constant/insufficient observed variation):

| feature | `loss_streak` | `win_streak` | `pnl_ewm` | `lot_zscore` | `amount` | `size_after_loss_delta` | `sl_usage_rate_5` | `manual_exit_rate_5` | `pnl_pct` | `dd_from_peak_pct` | `trade_index` | `log_dt_close` | `trades_per_hour` | `prior_campaigns` | `prior_campaigns_x_loss_streak_ge_2` | `shared_ip` | `ip_cluster_size` | `gold_vol_prev_day` | `same_direction_reentry` | `size_delta_ratio` | `trader_prior_tilt` | `trader_prior_sl_discipline` | `trader_prior_survival` | `is_cold_start` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `loss_streak` | 1.000 | -0.108 | -0.689 | -0.284 | -0.065 | -0.548 | n/a | -0.652 | -0.667 | 0.956 | 0.667 | 0.048 | -0.651 | 0.099 | 0.216 | 0.034 | 0.003 | -0.054 | 0.708 | -0.043 | 0.000 | -0.066 | 0.019 | -0.104 |
| `win_streak` | -0.108 | 1.000 | 0.667 | -0.009 | -0.106 | n/a | n/a | 0.495 | 0.624 | -0.023 | 0.665 | -0.096 | -0.655 | 0.010 | -0.021 | -0.064 | -0.031 | 0.006 | -0.077 | 0.069 | 0.000 | -0.021 | -0.032 | -0.020 |
| `pnl_ewm` | -0.689 | 0.667 | 1.000 | 0.150 | -0.029 | 0.083 | n/a | 0.748 | 0.963 | -0.676 | -0.017 | -0.041 | 0.014 | -0.048 | -0.161 | 0.003 | 0.000 | 0.036 | -0.504 | 0.027 | 0.000 | 0.044 | -0.044 | 0.044 |
| `lot_zscore` | -0.284 | -0.009 | 0.150 | 1.000 | 0.150 | 1.000 | n/a | 0.160 | 0.150 | -0.288 | -0.274 | 0.548 | 0.300 | 0.173 | -0.548 | -0.414 | 0.193 | -0.008 | 0.274 | 0.783 | n/a | -0.201 | -0.347 | -0.173 |
| `amount` | -0.065 | -0.106 | -0.029 | 0.150 | 1.000 | 0.550 | n/a | 0.169 | -0.020 | -0.064 | -0.124 | -0.191 | 0.139 | 0.086 | 0.016 | 0.061 | 0.112 | -0.142 | -0.038 | 0.473 | 0.015 | -0.011 | 0.063 | -0.091 |
| `size_after_loss_delta` | -0.548 | n/a | 0.083 | 1.000 | 0.550 | 1.000 | n/a | 0.500 | 0.083 | -0.067 | 0.183 | -0.274 | 0.233 | 0.087 | -0.548 | n/a | -0.319 | -0.375 | 0.725 | -0.050 | n/a | -0.647 | 0.122 | -0.087 |
| `sl_usage_rate_5` | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `manual_exit_rate_5` | -0.652 | 0.495 | 0.748 | 0.160 | 0.169 | 0.500 | n/a | 1.000 | 0.811 | -0.634 | 0.366 | -0.146 | -0.045 | 0.046 | -0.512 | 0.221 | -0.052 | -0.125 | -0.146 | 0.303 | n/a | -0.078 | -0.351 | -0.046 |
| `pnl_pct` | -0.667 | 0.624 | 0.963 | 0.150 | -0.020 | 0.083 | n/a | 0.811 | 1.000 | -0.690 | -0.033 | -0.044 | 0.028 | -0.048 | -0.162 | 0.004 | 0.006 | 0.034 | -0.475 | 0.039 | 0.000 | 0.041 | -0.021 | 0.039 |
| `dd_from_peak_pct` | 0.956 | -0.023 | -0.676 | -0.288 | -0.064 | -0.067 | n/a | -0.634 | -0.690 | 1.000 | 0.707 | 0.047 | -0.684 | 0.098 | 0.207 | -0.011 | -0.014 | -0.039 | 0.677 | -0.031 | 0.000 | -0.057 | 0.001 | -0.102 |
| `trade_index` | 0.667 | 0.665 | -0.017 | -0.274 | -0.124 | 0.183 | n/a | 0.366 | -0.033 | 0.707 | 1.000 | -0.188 | -0.975 | 0.085 | 0.157 | -0.026 | -0.020 | -0.038 | 0.464 | 0.310 | 0.000 | -0.062 | -0.010 | -0.097 |
| `log_dt_close` | 0.048 | -0.096 | -0.041 | 0.548 | -0.191 | -0.274 | n/a | -0.146 | -0.044 | 0.047 | -0.188 | 1.000 | -0.509 | 0.077 | -0.103 | -0.026 | -0.097 | 0.024 | 0.053 | -0.212 | n/a | -0.107 | 0.094 | -0.036 |
| `trades_per_hour` | -0.651 | -0.655 | 0.014 | 0.300 | 0.139 | 0.233 | n/a | -0.045 | 0.028 | -0.684 | -0.975 | -0.509 | 1.000 | -0.086 | -0.148 | 0.028 | 0.031 | 0.046 | -0.448 | 0.320 | 0.000 | 0.069 | 0.003 | 0.095 |
| `prior_campaigns` | 0.099 | 0.010 | -0.048 | 0.173 | 0.086 | 0.087 | n/a | 0.046 | -0.048 | 0.098 | 0.085 | 0.077 | -0.086 | 1.000 | 0.104 | 0.141 | 0.147 | -0.120 | 0.110 | 0.038 | 0.000 | -0.427 | 0.221 | -0.987 |
| `prior_campaigns_x_loss_streak_ge_2` | 0.216 | -0.021 | -0.161 | -0.548 | 0.016 | -0.548 | n/a | -0.512 | -0.162 | 0.207 | 0.157 | -0.103 | -0.148 | 0.104 | 1.000 | 0.015 | 0.019 | 0.000 | 0.180 | 0.003 | 0.000 | -0.023 | 0.130 | -0.107 |
| `shared_ip` | 0.034 | -0.064 | 0.003 | -0.414 | 0.061 | n/a | n/a | 0.221 | 0.004 | -0.011 | -0.026 | -0.026 | 0.028 | 0.141 | 0.015 | 1.000 | 0.317 | 0.013 | 0.055 | -0.053 | 0.000 | -0.060 | 0.025 | -0.143 |
| `ip_cluster_size` | 0.003 | -0.031 | 0.000 | 0.193 | 0.112 | -0.319 | n/a | -0.052 | 0.006 | -0.014 | -0.020 | -0.097 | 0.031 | 0.147 | 0.019 | 0.317 | 1.000 | 0.058 | -0.001 | 0.120 | -0.027 | 0.034 | 0.100 | -0.143 |
| `gold_vol_prev_day` | -0.054 | 0.006 | 0.036 | -0.008 | -0.142 | -0.375 | n/a | -0.125 | 0.034 | -0.039 | -0.038 | 0.024 | 0.046 | -0.120 | 0.000 | 0.013 | 0.058 | 1.000 | -0.084 | 0.049 | -0.023 | 0.180 | -0.021 | 0.119 |
| `same_direction_reentry` | 0.708 | -0.077 | -0.504 | 0.274 | -0.038 | 0.725 | n/a | -0.146 | -0.475 | 0.677 | 0.464 | 0.053 | -0.448 | 0.110 | 0.180 | 0.055 | -0.001 | -0.084 | 1.000 | -0.062 | 0.000 | -0.124 | -0.002 | -0.111 |
| `size_delta_ratio` | -0.043 | 0.069 | 0.027 | 0.783 | 0.473 | -0.050 | n/a | 0.303 | 0.039 | -0.031 | 0.310 | -0.212 | 0.320 | 0.038 | 0.003 | -0.053 | 0.120 | 0.049 | -0.062 | 1.000 | n/a | -0.008 | 0.029 | -0.055 |
| `trader_prior_tilt` | 0.000 | 0.000 | 0.000 | n/a | 0.015 | n/a | n/a | n/a | 0.000 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 0.000 | 0.000 | -0.027 | -0.023 | 0.000 | n/a | 1.000 | 0.107 | -0.002 | 0.000 |
| `trader_prior_sl_discipline` | -0.066 | -0.021 | 0.044 | -0.201 | -0.011 | -0.647 | n/a | -0.078 | 0.041 | -0.057 | -0.062 | -0.107 | 0.069 | -0.427 | -0.023 | -0.060 | 0.034 | 0.180 | -0.124 | -0.008 | 0.107 | 1.000 | -0.198 | 0.420 |
| `trader_prior_survival` | 0.019 | -0.032 | -0.044 | -0.347 | 0.063 | 0.122 | n/a | -0.351 | -0.021 | 0.001 | -0.010 | 0.094 | 0.003 | 0.221 | 0.130 | 0.025 | 0.100 | -0.021 | -0.002 | 0.029 | -0.002 | -0.198 | 1.000 | -0.174 |
| `is_cold_start` | -0.104 | -0.020 | 0.044 | -0.173 | -0.091 | -0.087 | n/a | -0.046 | 0.039 | -0.102 | -0.097 | -0.036 | 0.095 | -0.987 | -0.107 | -0.143 | -0.143 | 0.119 | -0.111 | -0.055 | 0.000 | 0.420 | -0.174 | 1.000 |

## 8. Amendment B: cold-start impact and model variants

At the boundary entering C53-C66, `1,354/6,583 = 20.57%` of evaluation rows
carry a traderKey that appeared in C33-C52; `5,229/6,583 = 79.43%` are
strictly unavailable because they are cold keyed rows or lack a traderKey. The
four history fields below are therefore measured against the pre-evaluation
training-history definition of “trader-specific.” Their full-column variance
includes population fallback values.

| feature | trader-specific rows | fraction | full variance | variance on trader-specific rows |
|---|---:|---:|---:|---:|
| `prior_campaigns` | 1,354 | 20.57% | 5.704799 | 8.504443 |
| `trader_prior_tilt` | 1,354 | 20.57% | 2,498.928677 | 6,590.845033 |
| `trader_prior_sl_discipline` | 1,354 | 20.57% | 0.000012632 | 0.000000122 |
| `trader_prior_survival` | 1,354 | 20.57% | 0.572269 | 0.723767 |

This is the split-entry diagnostic. If causal online updating is allowed within
the evaluation stream, later evaluation campaigns can legitimately acquire
history: `3,613/6,583 = 54.88%` of realized evaluation rows have
`prior_campaigns > 0`. That online update does not change the 79.39% cold-start
rate at the mandated boundary and does not make the initial cold rows
trader-specific.

Two mandated-split ridge variants were run using the 24 admissible fields:

- V1 includes the four history fields and restores `is_cold_start` explicitly
  (25 inputs).
- V2 drops the four history fields (`prior_campaigns` plus the three
  `trader_prior_*` columns) but retains the interaction
  `prior_campaigns_x_loss_streak_ge_2` (20 inputs).

| variant | track | alpha | Spearman | MAE | flagged n | flagged coverage | flagged mean gross loss/lot | flagged mean rP/lot |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| V1 history + cold indicator | A | 1000.0 | 0.02553 | 350.0714 | 463 | 7.03% | 4.0087 | -2.9913 |
| V1 history + cold indicator | B | 1000.0 | 0.02553 | 350.0714 | 463 | 7.03% | 4.0087 | -2.9913 |
| V2 history dropped | A | 1000.0 | 0.02804 | 349.8118 | 385 | 5.85% | -1.6903 | -8.6903 |
| V2 history dropped | B | 1000.0 | 0.02804 | 349.8118 | 385 | 5.85% | -1.6903 | -8.6903 |

At this stage this is only a provisional model comparison. Neither variant is a
confirmed edge: both are evaluated after an underpowered training split, not as
BH-surviving hypothesis tests. The V1 recommendation is revisited in Section
11 after checking whether its apparent advantage is actually history-driven.

## 9. Required baselines

DO NOTHING is `0.00/lot` by construction and has no sampling interval: it is a
policy that takes no fade exposure. FADE EVERYTHING is evaluated on all rows
(`n` and coverage are both 100%). The equal-weighted value is the arithmetic
mean of reverseProfit/lot; the size-weighted value is
`-sum(profit)/sum(amount) - 7`, with the `$7` cost subtracted once.

| window | baseline | n | coverage | mean rP/lot | account 95% CI | IP 95% CI |
|---|---|---:|---:|---:|---:|---:|
| C53-C65 | DO NOTHING | 6,582 | 100% | 0.000 | [0.000, 0.000] by construction | [0.000, 0.000] by construction |
| C53-C65 | FADE EVERYTHING, equal-weighted | 6,582 | 100% | 5.436 | [-9.067, 20.258] | [-9.089, 20.217] |
| C53-C65 | FADE EVERYTHING, size-weighted | 6,582 | 100% | -3.001 | [-11.037, 5.574] | [-11.504, 5.214] |
| C53-C66 | DO NOTHING | 6,583 | 100% | 0.000 | [0.000, 0.000] by construction | [0.000, 0.000] by construction |
| C53-C66 | FADE EVERYTHING, equal-weighted | 6,583 | 100% | 5.434 | [-9.067, 20.254] | [-9.089, 20.208] |
| C53-C66 | FADE EVERYTHING, size-weighted | 6,583 | 100% | -3.587 | [-10.681, 4.427] | [-11.197, 4.244] |

C66 contributes exactly one position. It changes the evaluation mean and the
size-weighted baseline, but not the 496-account count. Any deployed model must
beat both fade-everything baselines on the same weighting convention; a
flagged-subset result alone is not a replacement for this policy comparison.

## 10. Interpretation and freeze decision

The evidence is consistent with a real but difficult-to-detect behavioral
signal: the strongest admissible pooled feature effect is `70.63/lot` for
`trader_prior_survival` on Track A, just above the robust training MDE, while
all other admissible pooled effects are below the training detection floor.
The Stage 1 loss-streak result is positive unadjusted but fails the 90-test
correction, and the narrow S2 positives are explicitly leaky because their
thresholds were learned from the evaluation era.

The V1 freeze recommendation is superseded by the decision audit below. Do not
freeze any threshold from S2 as a clean common-split discovery.

## 11. V1 versus V2 decision audit

The prior recommendation was tested directly. V1 is the 24-feature model plus
`is_cold_start`; V2 removes the four history fields
(`prior_campaigns` and the three `trader_prior_*` fields) while retaining the
pre-specified `prior_campaigns_x_loss_streak_ge_2` interaction. Both use the
same alpha (`1000`) and the same winsorized training target. All intervals in
this section are 2,000-resample bootstrap intervals clustered by account
(`traderKey`, with the existing campaign-account fallback).

### Coefficient magnitude

The V1 coefficients below are on the standardized numeric scale, so their
magnitudes are comparable within this ridge fit. `is_cold_start` is much larger
than every one of the four history coefficients: approximately 231x
`prior_campaigns`, 43x `trader_prior_tilt`, 5.7x
`trader_prior_sl_discipline`, and 4.9x `trader_prior_survival`. It is not the
largest coefficient in the entire model, but relative to the history fields it
dominates. The retained loss-streak/history interaction is also large.

| V1 input | standardized coefficient | absolute magnitude |
|---|---:|---:|
| `is_cold_start` | -2.7052 | 2.7052 |
| `prior_campaigns` | 0.0117 | 0.0117 |
| `trader_prior_tilt` | -0.0623 | 0.0623 |
| `trader_prior_sl_discipline` | 0.4768 | 0.4768 |
| `trader_prior_survival` | -0.5473 | 0.5473 |
| `prior_campaigns_x_loss_streak_ge_2` (context) | 2.7427 | 2.7427 |

Thus V1 is primarily learning the cold-start/repeat-trader partition, not
demonstrably extracting the four history values.

### Common-split evaluation

| variant | flagged n | coverage | mean rP/lot | account-clustered 95% CI |
|---|---:|---:|---:|---:|
| V1 | 463 | 7.03% | -2.991 | [-49.442, 43.162] |
| V2 | 385 | 5.85% | -8.690 | [-58.429, 37.922] |

The intervals overlap substantially. Under the pre-registered decision rule,
this means the extra history fields have not demonstrated a separable benefit;
V2 is preferred on parsimony rather than on a claim that its point estimate is
proven better.

### Rows carrying trader-specific history

There are `1,354/6,583 = 20.57%` evaluation rows whose `traderKey` appeared in
the C33-C52 training era. Restricting evaluation to those rows—the only rows
where the four history fields can carry trader-specific information—does not
rescue V1:

| variant | flagged n | coverage within history-bearing rows | mean rP/lot | account-clustered 95% CI |
|---|---:|---:|---:|---:|
| V1 | 182 | 13.44% | -2.579 | [-62.526, 62.035] |
| V2 | 155 | 11.45% | 10.031 | [-52.813, 78.831] |

The intervals overlap, but V1 does not beat V2 on the subset where history
could help. This is the key result against keeping the original V1 rationale.

### Fold-4 analogue

Fold 4 evaluates C63-C65. The global causal cold-start indicator is 86.24% in
Track A (the unseen-trader floor) and 48.93% in Track B (the returning-trader
production analogue).

| track | variant | validation n | flagged n | coverage | mean rP/lot | account-clustered 95% CI |
|---|---|---:|---:|---:|---:|---:|
| A | V1 | 901 | 714 | 79.25% | 2.403 | [-41.110, 41.251] |
| A | V2 | 901 | 636 | 70.59% | 8.786 | [-37.942, 50.144] |
| B | V1 | 1,590 | 1,063 | 66.86% | -3.528 | [-37.651, 31.008] |
| B | V2 | 1,590 | 1,038 | 65.28% | -4.545 | [-39.313, 29.589] |

There is no consistent fold-4 winner: V2 is higher on Track A, while V1 is
slightly higher on Track B, and all intervals overlap zero and each other. In
the high-cold-start Track A analogue, V2 does not degrade relative to V1; in
the returning-trader Track B analogue, V1's small point advantage is not
identified. The robust conclusion is therefore structural, not score-based:
V1's indicator dominates its history coefficients, its history-bearing subset
does not favor V1, and its overall advantage is not distinguishable from zero.

### Revised recommendation

Freeze **V2** for Stage 4: the admissible non-SL/TP feature set with the four
history fields removed, while retaining the pre-specified interaction. The
reason is parsimony under overlapping account-clustered intervals and the
absence of a history-specific advantage—not a claim that V2 has established a
positive trading edge. Keep `is_cold_start` as a monitoring/reporting field,
but do not give it model weight by default. Revisit the history fields only
after Stage 4 supplies genuinely new, sufficiently repeated trader history.
