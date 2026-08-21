# Feature Checks Walk-Forward

All reported outcomes in this document are **reverseProfit per lot**, defined via `reverse_profit_per_lot(gross_loss_per_lot, cost_per_lot=7.00)`, so the C22 hurdle is exactly `0.00`.

The frozen v2.1 feature set remains **28 features**. `pnl_pct` and `dd_from_peak_pct` are now normalized on the confirmed `STARTING_BALANCE = 5,000.00`. The export at `features_v2.csv` also includes appended balance-derived columns: `cum_pnl_usd`, `dd_from_peak_usd`, `breach_proximity_usd`, and `target_proximity_usd`.

Method:

- Primary-era validation scope is campaigns `C53-C65` only.
- Fold structure is the existing 4-fold expanding walk-forward split on both Track A and Track B.
- Threshold/bucket selection happens on each fold's training campaigns only.
- Numeric features use train-side quantile buckets (falling back to equal-width bins when needed); categorical and binary features use exact observed values.
- Clustered bootstrap CIs reuse the pinned Stage 1 helper with `seed=7` and `n_boot=2000`.
- PASS means the pooled CI lower bound is above `0.00` under both traderKey-clustered and ipClusterId-clustered bootstraps.

## Monotone Rescaling Check

The old assumed normalization (`10,000.00`) and the confirmed normalization (`5,000.00`) were compared directly for `pnl_pct` and `dd_from_peak_pct`. Because the dollar paths are unchanged and the rescaling is monotone, bucket row membership is identical everywhere below; only numeric bucket edges move.

| track | fold | feature | legacy_bucket_10000 | current_bucket_5000 | train_membership_changed | val_membership_changed | legacy_train_bucket_n | current_train_bucket_n | legacy_train_mean_reverse_profit_per_lot | current_train_mean_reverse_profit_per_lot | results_identical_by_membership |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | pnl_pct | bucket (-0.013, 0.0] | bucket (-0.026, 0.0] | 0 | 0 | 933 | 933 | 16.0062 | 16.0062 | PASS |
| A | Fold 1 | dd_from_peak_pct | bucket (0.0196, 0.221] | bucket (0.0392, 0.443] | 0 | 0 | 408 | 408 | 1.6180 | 1.6180 | PASS |
| A | Fold 2 | pnl_pct | bucket (-0.015, 0.0] | bucket (-0.0299, 0.0] | 0 | 0 | 1381 | 1381 | 30.1920 | 30.1920 | PASS |
| A | Fold 2 | dd_from_peak_pct | bucket (0.0212, 0.221] | bucket (0.0424, 0.443] | 0 | 0 | 597 | 597 | 21.1073 | 21.1073 | PASS |
| A | Fold 3 | pnl_pct | bucket (-0.0155, 0.0] | bucket (-0.031, 0.0] | 0 | 0 | 1910 | 1910 | 44.0758 | 44.0758 | PASS |
| A | Fold 3 | dd_from_peak_pct | bucket (-0.001, 0.00365] | bucket (-0.001, 0.0073] | 0 | 0 | 2411 | 2411 | 21.2240 | 21.2240 | PASS |
| A | Fold 4 | pnl_pct | bucket (-0.0156, 0.0] | bucket (-0.0312, 0.0] | 0 | 0 | 2412 | 2412 | 39.7181 | 39.7181 | PASS |
| A | Fold 4 | dd_from_peak_pct | bucket (-0.001, 0.00344] | bucket (-0.001, 0.00688] | 0 | 0 | 2995 | 2995 | 12.3652 | 12.3652 | PASS |
| B | Fold 1 | pnl_pct | bucket (-0.013, 0.0] | bucket (-0.026, 0.0] | 0 | 0 | 933 | 933 | 16.0062 | 16.0062 | PASS |
| B | Fold 1 | dd_from_peak_pct | bucket (0.0196, 0.221] | bucket (0.0392, 0.443] | 0 | 0 | 408 | 408 | 1.6180 | 1.6180 | PASS |
| B | Fold 2 | pnl_pct | bucket (-0.015, 0.0] | bucket (-0.0299, 0.0] | 0 | 0 | 1381 | 1381 | 30.1920 | 30.1920 | PASS |
| B | Fold 2 | dd_from_peak_pct | bucket (0.0212, 0.221] | bucket (0.0424, 0.443] | 0 | 0 | 597 | 597 | 21.1073 | 21.1073 | PASS |
| B | Fold 3 | pnl_pct | bucket (-0.0155, 0.0] | bucket (-0.031, 0.0] | 0 | 0 | 1910 | 1910 | 44.0758 | 44.0758 | PASS |
| B | Fold 3 | dd_from_peak_pct | bucket (-0.001, 0.00365] | bucket (-0.001, 0.0073] | 0 | 0 | 2411 | 2411 | 21.2240 | 21.2240 | PASS |
| B | Fold 4 | pnl_pct | bucket (-0.0156, 0.0] | bucket (-0.0312, 0.0] | 0 | 0 | 2412 | 2412 | 39.7181 | 39.7181 | PASS |
| B | Fold 4 | dd_from_peak_pct | bucket (-0.001, 0.00344] | bucket (-0.001, 0.00688] | 0 | 0 | 2995 | 2995 | 12.3652 | 12.3652 | PASS |

## Frozen 28 — Pooled Ranking Track A

| track | name | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | sl_distance_pct | 354 | 163.2110 | 86.4453 | 243.8121 | 90.1269 | 240.3502 | PASS |
| A | size_after_loss_delta | 54 | 85.2296 | -41.7730 | 234.5714 | -41.5042 | 228.3097 | FAIL |
| A | trader_prior_survival | 374 | 69.9336 | 4.2307 | 137.6970 | 3.8667 | 143.0321 | PASS |
| A | ip_cluster_size | 369 | 67.7748 | 10.4028 | 143.3167 | 8.1179 | 144.4523 | PASS |
| A | manual_exit_rate_5 | 121 | 64.9123 | 5.1787 | 120.6894 | 8.0552 | 124.0516 | PASS |
| A | loss_streak | 297 | 50.5244 | 2.8124 | 100.1245 | 1.8325 | 100.3607 | PASS |
| A | pnl_pct | 1102 | 49.0180 | 9.6677 | 89.7553 | 9.7754 | 88.4893 | PASS |
| A | trades_per_hour | 936 | 47.4105 | 5.4981 | 89.3123 | 6.3158 | 92.7390 | PASS |
| A | sl_widening_delta | 113 | 43.8169 | -31.8623 | 119.7032 | -31.4422 | 121.9822 | FAIL |
| A | size_delta_ratio | 271 | 41.1140 | -17.3202 | 108.9514 | -15.8091 | 106.4209 | FAIL |
| A | pnl_ewm | 1086 | 41.0764 | 2.0047 | 82.8330 | 2.6997 | 82.2106 | PASS |
| A | log_dt_close | 473 | 28.2265 | -16.5033 | 76.5571 | -14.4343 | 73.8746 | FAIL |
| A | win_streak | 1956 | 24.2154 | -1.8642 | 51.3718 | -1.1372 | 51.7375 | FAIL |
| A | prior_campaigns_x_loss_streak_ge_2 | 2190 | 21.7109 | -2.6464 | 47.4330 | -1.0475 | 47.8438 | FAIL |
| A | same_direction_reentry | 1742 | 21.6692 | -6.1546 | 51.5890 | -5.1135 | 50.5901 | FAIL |
| A | trader_prior_tilt | 2175 | 21.1768 | -3.0976 | 46.6904 | -1.6107 | 47.2618 | FAIL |
| A | prior_campaigns | 2108 | 20.4275 | -5.2246 | 46.6902 | -3.0822 | 47.1857 | FAIL |
| A | trader_prior_sl_discipline | 1937 | 15.1767 | -11.7609 | 42.9369 | -10.7336 | 42.4778 | FAIL |
| A | lot_zscore | 129 | 15.1153 | -49.9901 | 90.2783 | -49.7172 | 87.4123 | FAIL |
| A | sl_usage_rate_5 | 257 | 12.5003 | -30.2427 | 60.0451 | -25.6217 | 63.0892 | FAIL |
| A | gold_vol_prev_day | 994 | 9.6399 | -23.1782 | 44.2516 | -23.1820 | 45.4935 | FAIL |
| A | amount | 379 | 4.0593 | -105.4311 | 112.6533 | -100.9868 | 117.1144 | FAIL |
| A | challenge_type | 1607 | -0.0428 | -26.3977 | 27.9249 | -27.1017 | 27.2464 | FAIL |
| A | shared_ip | 652 | -1.7865 | -37.9764 | 35.1465 | -36.2795 | 32.3479 | FAIL |
| A | has_tp | 565 | -4.9935 | -63.9357 | 55.4529 | -61.1395 | 57.3400 | FAIL |
| A | trade_index | 350 | -5.6716 | -41.2521 | 29.6047 | -40.8536 | 30.6805 | FAIL |
| A | dd_from_peak_pct | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |
| A | has_sl | 752 | -14.7715 | -60.2301 | 31.8823 | -61.2996 | 32.3872 | FAIL |

## Frozen 28 — Pooled Ranking Track B

| track | name | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | sl_distance_pct | 711 | 122.8115 | 68.3875 | 178.5113 | 67.3195 | 182.7826 | PASS |
| B | sl_widening_delta | 239 | 64.2225 | -10.7240 | 144.6479 | -16.1136 | 143.7137 | FAIL |
| B | amount | 710 | 45.3809 | -30.9703 | 128.4606 | -30.8359 | 121.7489 | FAIL |
| B | ip_cluster_size | 835 | 43.7181 | 5.2036 | 89.9204 | 6.1015 | 87.4156 | PASS |
| B | trader_prior_survival | 955 | 41.5299 | 4.0038 | 81.1146 | 2.0836 | 81.2294 | PASS |
| B | trades_per_hour | 1790 | 37.6032 | 7.9945 | 67.8172 | 10.9772 | 67.5290 | PASS |
| B | pnl_pct | 2169 | 36.8565 | 8.2186 | 64.3898 | 11.3820 | 63.1741 | PASS |
| B | pnl_ewm | 2172 | 30.9601 | 2.6545 | 56.6419 | 5.8841 | 56.8484 | PASS |
| B | prior_campaigns | 2568 | 22.2502 | -1.0509 | 44.1620 | 0.0855 | 45.5597 | FAIL |
| B | loss_streak | 598 | 18.7916 | -13.0933 | 53.1114 | -12.6723 | 51.7376 | FAIL |
| B | manual_exit_rate_5 | 346 | 15.9814 | -29.4786 | 64.2584 | -30.4717 | 65.8857 | FAIL |
| B | win_streak | 3988 | 15.0182 | -3.2041 | 33.2520 | -2.7554 | 33.3305 | FAIL |
| B | trade_index | 780 | 15.0112 | -12.7391 | 47.6999 | -13.7627 | 44.3712 | FAIL |
| B | size_delta_ratio | 609 | 14.3551 | -29.6350 | 60.6375 | -30.2738 | 56.8237 | FAIL |
| B | trader_prior_tilt | 4095 | 13.5658 | -4.8834 | 32.6031 | -5.4944 | 33.0676 | FAIL |
| B | same_direction_reentry | 3655 | 12.9654 | -6.5032 | 32.6190 | -7.7084 | 33.0382 | FAIL |
| B | prior_campaigns_x_loss_streak_ge_2 | 4543 | 12.1167 | -5.0187 | 29.6998 | -4.8739 | 30.0853 | FAIL |
| B | trader_prior_sl_discipline | 2227 | 10.1399 | -15.3824 | 35.7106 | -15.0703 | 36.8145 | FAIL |
| B | has_sl | 1632 | 4.2202 | -26.2744 | 34.7161 | -27.3623 | 35.3478 | FAIL |
| B | size_after_loss_delta | 142 | 3.6573 | -73.3450 | 83.2552 | -76.1405 | 84.1979 | FAIL |
| B | has_tp | 925 | 1.5115 | -41.9972 | 43.4064 | -42.9248 | 44.6221 | FAIL |
| B | shared_ip | 652 | -1.7865 | -36.4565 | 34.0950 | -36.8194 | 34.8910 | FAIL |
| B | log_dt_close | 1102 | -1.8901 | -29.6029 | 27.8939 | -31.2117 | 28.0903 | FAIL |
| B | challenge_type | 3044 | -2.0156 | -20.5906 | 15.9126 | -20.3529 | 17.1078 | FAIL |
| B | gold_vol_prev_day | 2014 | -3.4468 | -26.4825 | 18.4723 | -24.2313 | 17.5196 | FAIL |
| B | sl_usage_rate_5 | 568 | -11.1358 | -41.2285 | 19.9185 | -40.3296 | 18.9212 | FAIL |
| B | dd_from_peak_pct | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |
| B | lot_zscore | 346 | -15.7941 | -67.2458 | 37.2168 | -63.0070 | 33.0864 | FAIL |

## Frozen 28 — Failed Features

| track | name | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | size_after_loss_delta | 54 | 85.2296 | -41.7730 | 234.5714 | -41.5042 | 228.3097 |
| A | sl_widening_delta | 113 | 43.8169 | -31.8623 | 119.7032 | -31.4422 | 121.9822 |
| A | size_delta_ratio | 271 | 41.1140 | -17.3202 | 108.9514 | -15.8091 | 106.4209 |
| A | log_dt_close | 473 | 28.2265 | -16.5033 | 76.5571 | -14.4343 | 73.8746 |
| A | win_streak | 1956 | 24.2154 | -1.8642 | 51.3718 | -1.1372 | 51.7375 |
| A | prior_campaigns_x_loss_streak_ge_2 | 2190 | 21.7109 | -2.6464 | 47.4330 | -1.0475 | 47.8438 |
| A | same_direction_reentry | 1742 | 21.6692 | -6.1546 | 51.5890 | -5.1135 | 50.5901 |
| A | trader_prior_tilt | 2175 | 21.1768 | -3.0976 | 46.6904 | -1.6107 | 47.2618 |
| A | prior_campaigns | 2108 | 20.4275 | -5.2246 | 46.6902 | -3.0822 | 47.1857 |
| A | trader_prior_sl_discipline | 1937 | 15.1767 | -11.7609 | 42.9369 | -10.7336 | 42.4778 |
| A | lot_zscore | 129 | 15.1153 | -49.9901 | 90.2783 | -49.7172 | 87.4123 |
| A | sl_usage_rate_5 | 257 | 12.5003 | -30.2427 | 60.0451 | -25.6217 | 63.0892 |
| A | gold_vol_prev_day | 994 | 9.6399 | -23.1782 | 44.2516 | -23.1820 | 45.4935 |
| A | amount | 379 | 4.0593 | -105.4311 | 112.6533 | -100.9868 | 117.1144 |
| A | challenge_type | 1607 | -0.0428 | -26.3977 | 27.9249 | -27.1017 | 27.2464 |
| A | shared_ip | 652 | -1.7865 | -37.9764 | 35.1465 | -36.2795 | 32.3479 |
| A | has_tp | 565 | -4.9935 | -63.9357 | 55.4529 | -61.1395 | 57.3400 |
| A | trade_index | 350 | -5.6716 | -41.2521 | 29.6047 | -40.8536 | 30.6805 |
| A | dd_from_peak_pct | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 |
| A | has_sl | 752 | -14.7715 | -60.2301 | 31.8823 | -61.2996 | 32.3872 |
| B | sl_widening_delta | 239 | 64.2225 | -10.7240 | 144.6479 | -16.1136 | 143.7137 |
| B | amount | 710 | 45.3809 | -30.9703 | 128.4606 | -30.8359 | 121.7489 |
| B | prior_campaigns | 2568 | 22.2502 | -1.0509 | 44.1620 | 0.0855 | 45.5597 |
| B | loss_streak | 598 | 18.7916 | -13.0933 | 53.1114 | -12.6723 | 51.7376 |
| B | manual_exit_rate_5 | 346 | 15.9814 | -29.4786 | 64.2584 | -30.4717 | 65.8857 |
| B | win_streak | 3988 | 15.0182 | -3.2041 | 33.2520 | -2.7554 | 33.3305 |
| B | trade_index | 780 | 15.0112 | -12.7391 | 47.6999 | -13.7627 | 44.3712 |
| B | size_delta_ratio | 609 | 14.3551 | -29.6350 | 60.6375 | -30.2738 | 56.8237 |
| B | trader_prior_tilt | 4095 | 13.5658 | -4.8834 | 32.6031 | -5.4944 | 33.0676 |
| B | same_direction_reentry | 3655 | 12.9654 | -6.5032 | 32.6190 | -7.7084 | 33.0382 |
| B | prior_campaigns_x_loss_streak_ge_2 | 4543 | 12.1167 | -5.0187 | 29.6998 | -4.8739 | 30.0853 |
| B | trader_prior_sl_discipline | 2227 | 10.1399 | -15.3824 | 35.7106 | -15.0703 | 36.8145 |
| B | has_sl | 1632 | 4.2202 | -26.2744 | 34.7161 | -27.3623 | 35.3478 |
| B | size_after_loss_delta | 142 | 3.6573 | -73.3450 | 83.2552 | -76.1405 | 84.1979 |
| B | has_tp | 925 | 1.5115 | -41.9972 | 43.4064 | -42.9248 | 44.6221 |
| B | shared_ip | 652 | -1.7865 | -36.4565 | 34.0950 | -36.8194 | 34.8910 |
| B | log_dt_close | 1102 | -1.8901 | -29.6029 | 27.8939 | -31.2117 | 28.0903 |
| B | challenge_type | 3044 | -2.0156 | -20.5906 | 15.9126 | -20.3529 | 17.1078 |
| B | gold_vol_prev_day | 2014 | -3.4468 | -26.4825 | 18.4723 | -24.2313 | 17.5196 |
| B | sl_usage_rate_5 | 568 | -11.1358 | -41.2285 | 19.9185 | -40.3296 | 18.9212 |
| B | dd_from_peak_pct | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 |
| B | lot_zscore | 346 | -15.7941 | -67.2458 | 37.2168 | -63.0070 | 33.0864 |

## Appended Balance-Derived Checks

| track | name | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | cum_pnl_usd | 1102 | 49.0180 | 9.6677 | 89.7553 | 9.7754 | 88.4893 | PASS |
| A | target_proximity_usd | 910 | 13.2280 | -30.0540 | 58.5875 | -28.9008 | 56.2392 | FAIL |
| A | dd_from_peak_usd | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |
| A | breach_proximity_usd | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |

| track | name | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | cum_pnl_usd | 2169 | 36.8565 | 8.2186 | 64.3898 | 11.3820 | 63.1741 | PASS |
| B | target_proximity_usd | 1772 | 17.9210 | -9.6103 | 46.8645 | -9.6272 | 48.8923 | FAIL |
| B | dd_from_peak_usd | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |
| B | breach_proximity_usd | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |

## Composite Trigger Holdout

The `loss_streak >= 2 AND amount <= 0.2` trigger does not survive the folds 3-4 holdout on either track.

| track | fold | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 3 | 8 | 250.8906 | -115.1906 | 857.4100 | -115.1688 | 825.0389 | FAIL |
| A | Fold 4 | 29 | -50.4870 | -291.9270 | 149.1037 | -275.9735 | 152.7298 | FAIL |
| A | Pooled | 64 | 169.8147 | 11.9212 | 359.3799 | 7.4024 | 356.3593 | PASS |
| B | Fold 3 | 23 | 135.1914 | -36.3545 | 356.7395 | -35.8105 | 350.5125 | FAIL |
| B | Fold 4 | 58 | -54.6879 | -231.0837 | 112.6846 | -242.2970 | 113.5926 | FAIL |
| B | Pooled | 146 | 108.1155 | 5.5769 | 211.6230 | 7.1164 | 203.8199 | PASS |

## Holdout Diagnosis

The tables below separate underpowered positives from genuine decay by showing folds `3` and `4` individually on both tracks. `UNDERPOWERED` means the point estimate stays positive but at least one clustered CI still crosses `0.00`; `GENUINE_DECAY` means the point estimate is at or below `0.00`.

### Fixed Small-Size Interaction: `loss_streak >= 2 AND amount <= 0.2`

| track | fold | n_positions | n_distinct_traderKey | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 3 | 8 | 7 | 250.8906 | -115.1906 | 857.4100 | -115.1688 | 825.0389 | UNDERPOWERED |
| A | Fold 4 | 29 | 18 | -50.4870 | -291.9270 | 149.1037 | -275.9735 | 152.7298 | GENUINE_DECAY |
| B | Fold 3 | 23 | 17 | 135.1914 | -36.3545 | 356.7395 | -35.8105 | 350.5125 | UNDERPOWERED |
| B | Fold 4 | 58 | 33 | -54.6879 | -231.0837 | 112.6846 | -242.2970 | 113.5926 | GENUINE_DECAY |

### Parent Trigger: `loss_streak >= 2`

| track | fold | n_positions | n_distinct_traderKey | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 3 | 67 | 30 | 45.6286 | -29.8614 | 124.9609 | -30.4425 | 131.4516 | UNDERPOWERED |
| A | Fold 4 | 112 | 54 | 21.1374 | -59.5803 | 84.9061 | -62.5464 | 84.2326 | UNDERPOWERED |
| B | Fold 3 | 138 | 60 | 22.3312 | -25.4160 | 71.3796 | -23.7809 | 69.9587 | UNDERPOWERED |
| B | Fold 4 | 205 | 97 | 2.5227 | -64.8678 | 61.5208 | -58.0270 | 53.6787 | UNDERPOWERED |

### Train-Selected Size Threshold Within `loss_streak >= 2`

| track | fold | selected_size_threshold | train_selected_n | train_selected_mean_reverse_profit_per_lot | n_positions | n_distinct_traderKey | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 3 | 0.0100 | 7 | 574.5714 | 1 | 1 | -219.0000 | -219.0000 | -219.0000 | -219.0000 | -219.0000 | GENUINE_DECAY |
| A | Fold 4 | 0.0800 | 47 | 399.5388 | 3 | 3 | 19.0000 | -729.0000 | 1138.0000 | -729.0000 | 1138.0000 | UNDERPOWERED |
| B | Fold 3 | 0.0100 | 7 | 574.5714 | 2 | 2 | -228.0000 | -237.0000 | -219.0000 | -237.0000 | -219.0000 | GENUINE_DECAY |
| B | Fold 4 | 0.0800 | 47 | 399.5388 | 7 | 7 | -329.4286 | -996.1708 | 415.1357 | -1003.0542 | 403.1330 | GENUINE_DECAY |

### Commission Per Lot Context

Primary-era mean trader commission per lot is `35.0149` across `6582` positions. Compared with C22's reverse cost of `7.00` per lot, that is a ratio of `5.0021`.

Verdict: both the parent `loss_streak >= 2` signal and the small-size interaction weaken in the folds 3-4 holdout; the fixed `0.2` fold diagnoses are A Fold 3=UNDERPOWERED, A Fold 4=GENUINE_DECAY, B Fold 3=UNDERPOWERED, B Fold 4=GENUINE_DECAY.

## Composite Trigger Tables

### loss_streak >= 2

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | fixed rule | 283.0000 | 64.6997 | 58 | 59.1898 | -83.5567 | 214.1422 | -81.6822 | 212.2935 | FAIL |
| A | Fold 2 | fixed rule | 409.0000 | 57.6541 | 60 | 102.4705 | -15.1022 | 260.9040 | -19.7436 | 267.2644 | FAIL |
| A | Fold 3 | fixed rule | 538.0000 | 48.2314 | 67 | 45.6286 | -29.8614 | 124.9609 | -30.4425 | 131.4516 | FAIL |
| A | Fold 4 | fixed rule | 676.0000 | 42.9441 | 112 | 21.1374 | -59.5803 | 84.9061 | -62.5464 | 84.2326 | FAIL |
| A | Pooled | fixed rule |  |  | 297 | 50.5244 | 2.8124 | 100.1245 | 1.8325 | 100.3607 | PASS |
| B | Fold 1 | fixed rule | 283.0000 | 64.6997 | 126 | 41.8294 | -39.2050 | 128.6343 | -45.0881 | 133.5704 | FAIL |
| B | Fold 2 | fixed rule | 409.0000 | 57.6541 | 129 | 18.3565 | -55.8805 | 99.8935 | -52.6431 | 91.4206 | FAIL |
| B | Fold 3 | fixed rule | 538.0000 | 48.2314 | 138 | 22.3312 | -25.4160 | 71.3796 | -23.7809 | 69.9587 | FAIL |
| B | Fold 4 | fixed rule | 676.0000 | 42.9441 | 205 | 2.5227 | -64.8678 | 61.5208 | -58.0270 | 53.6787 | FAIL |
| B | Pooled | fixed rule |  |  | 598 | 18.7916 | -13.0933 | 53.1114 | -12.6723 | 51.7376 | FAIL |

### loss_streak >= 2 AND amount <= 0.2

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | fixed rule | 105.0000 | 107.4673 | 7 | 575.8571 | -2.9067 | 1241.1667 | -3.7357 | 1265.3833 | FAIL |
| A | Fold 2 | fixed rule | 130.0000 | 160.3249 | 20 | 314.7069 | 22.6646 | 721.9190 | 5.6229 | 770.1490 | PASS |
| A | Fold 3 | fixed rule | 170.0000 | 159.5966 | 8 | 250.8906 | -115.1906 | 857.4100 | -115.1688 | 825.0389 | FAIL |
| A | Fold 4 | fixed rule | 193.0000 | 156.6882 | 29 | -50.4870 | -291.9270 | 149.1037 | -275.9735 | 152.7298 | FAIL |
| A | Pooled | fixed rule |  |  | 64 | 169.8147 | 11.9212 | 359.3799 | 7.4024 | 356.3593 | PASS |
| B | Fold 1 | fixed rule | 105.0000 | 107.4673 | 25 | 382.3267 | 139.6282 | 654.1081 | 132.9962 | 646.5732 | PASS |
| B | Fold 2 | fixed rule | 130.0000 | 160.3249 | 40 | 157.2297 | -59.1407 | 381.9937 | -40.9986 | 354.9013 | FAIL |
| B | Fold 3 | fixed rule | 170.0000 | 159.5966 | 23 | 135.1914 | -36.3545 | 356.7395 | -35.8105 | 350.5125 | FAIL |
| B | Fold 4 | fixed rule | 193.0000 | 156.6882 | 58 | -54.6879 | -231.0837 | 112.6846 | -242.2970 | 113.5926 | FAIL |
| B | Pooled | fixed rule |  |  | 146 | 108.1155 | 5.5769 | 211.6230 | 7.1164 | 203.8199 | PASS |

## Frozen 28 Per-Feature Tables

### loss_streak

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (1.0, 9.0] | 283.0000 | 64.6997 | 58 | 59.1898 | -83.5567 | 214.1422 | -81.6822 | 212.2935 | FAIL |
| A | Fold 2 | bucket (1.0, 9.0] | 409.0000 | 57.6541 | 60 | 102.4705 | -15.1022 | 260.9040 | -19.7436 | 267.2644 | FAIL |
| A | Fold 3 | bucket (1.0, 9.0] | 538.0000 | 48.2314 | 67 | 45.6286 | -29.8614 | 124.9609 | -30.4425 | 131.4516 | FAIL |
| A | Fold 4 | bucket (1.0, 9.0] | 676.0000 | 42.9441 | 112 | 21.1374 | -59.5803 | 84.9061 | -62.5464 | 84.2326 | FAIL |
| A | Pooled | Fold 1: bucket (1.0, 9.0]; Fold 2: bucket (1.0, 9.0]; Fold 3: bucket (1.0, 9.0]; Fold 4: bucket (1.0, 9.0] |  |  | 297 | 50.5244 | 2.8124 | 100.1245 | 1.8325 | 100.3607 | PASS |
| B | Fold 1 | bucket (1.0, 9.0] | 283.0000 | 64.6997 | 126 | 41.8294 | -39.2050 | 128.6343 | -45.0881 | 133.5704 | FAIL |
| B | Fold 2 | bucket (1.0, 9.0] | 409.0000 | 57.6541 | 129 | 18.3565 | -55.8805 | 99.8935 | -52.6431 | 91.4206 | FAIL |
| B | Fold 3 | bucket (1.0, 9.0] | 538.0000 | 48.2314 | 138 | 22.3312 | -25.4160 | 71.3796 | -23.7809 | 69.9587 | FAIL |
| B | Fold 4 | bucket (1.0, 9.0] | 676.0000 | 42.9441 | 205 | 2.5227 | -64.8678 | 61.5208 | -58.0270 | 53.6787 | FAIL |
| B | Pooled | Fold 1: bucket (1.0, 9.0]; Fold 2: bucket (1.0, 9.0]; Fold 3: bucket (1.0, 9.0]; Fold 4: bucket (1.0, 9.0] |  |  | 598 | 18.7916 | -13.0933 | 53.1114 | -12.6723 | 51.7376 | FAIL |

### win_streak

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 1.0] | 1791.0000 | -0.1962 | 344 | 83.8008 | 19.1407 | 156.5870 | 16.4065 | 159.0515 | PASS |
| A | Fold 2 | bucket (-0.001, 1.0] | 2610.0000 | 9.4722 | 409 | 56.2638 | -14.4910 | 131.6203 | -21.4329 | 136.7942 | FAIL |
| A | Fold 3 | bucket (-0.001, 1.0] | 3530.0000 | 17.5716 | 418 | -18.0358 | -60.4303 | 19.5476 | -55.8020 | 20.2567 | FAIL |
| A | Fold 4 | bucket (-0.001, 1.0] | 4404.0000 | 14.4963 | 785 | 3.9044 | -34.2352 | 37.7407 | -34.2932 | 39.5911 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 1.0]; Fold 2: bucket (-0.001, 1.0]; Fold 3: bucket (-0.001, 1.0]; Fold 4: bucket (-0.001, 1.0] |  |  | 1956 | 24.2154 | -1.8642 | 51.3718 | -1.1372 | 51.7375 | FAIL |
| B | Fold 1 | bucket (-0.001, 1.0] | 1791.0000 | -0.1962 | 819 | 30.6152 | -11.1488 | 73.4047 | -8.7650 | 75.1602 | FAIL |
| B | Fold 2 | bucket (-0.001, 1.0] | 2610.0000 | 9.4722 | 920 | 40.5494 | -4.5122 | 84.8216 | -5.7595 | 89.0552 | FAIL |
| B | Fold 3 | bucket (-0.001, 1.0] | 3530.0000 | 17.5716 | 874 | 2.0754 | -23.8975 | 30.4219 | -23.9665 | 27.3963 | FAIL |
| B | Fold 4 | bucket (-0.001, 1.0] | 4404.0000 | 14.4963 | 1375 | -3.1277 | -31.1049 | 24.7848 | -30.0823 | 21.8959 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 1.0]; Fold 2: bucket (-0.001, 1.0]; Fold 3: bucket (-0.001, 1.0]; Fold 4: bucket (-0.001, 1.0] |  |  | 3988 | 15.0182 | -3.2041 | 33.2520 | -2.7554 | 33.3305 | FAIL |

### pnl_ewm

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-27.905, 0.0] | 957.0000 | 17.4406 | 194 | 120.9451 | 25.9440 | 224.1494 | 18.4596 | 225.6460 | PASS |
| A | Fold 2 | bucket (-29.565, 0.0] | 1400.0000 | 35.4604 | 247 | 80.3750 | -22.6181 | 180.7763 | -27.3888 | 192.3479 | FAIL |
| A | Fold 3 | bucket (-30.033, 0.0] | 1937.0000 | 46.4420 | 230 | -8.7807 | -59.8494 | 40.6251 | -57.7124 | 43.9504 | FAIL |
| A | Fold 4 | bucket (-30.031, 0.0] | 2437.0000 | 40.1767 | 415 | 7.9821 | -52.1830 | 66.8737 | -53.5855 | 66.9675 | FAIL |
| A | Pooled | Fold 1: bucket (-27.905, 0.0]; Fold 2: bucket (-29.565, 0.0]; Fold 3: bucket (-30.033, 0.0]; Fold 4: bucket (-30.031, 0.0] |  |  | 1086 | 41.0764 | 2.0047 | 82.8330 | 2.6997 | 82.2106 | PASS |
| B | Fold 1 | bucket (-27.905, 0.0] | 957.0000 | 17.4406 | 416 | 70.1742 | 8.6084 | 133.9302 | 14.8893 | 132.7547 | PASS |
| B | Fold 2 | bucket (-29.565, 0.0] | 1400.0000 | 35.4604 | 526 | 80.3813 | 16.8401 | 144.7157 | 15.0150 | 149.6663 | PASS |
| B | Fold 3 | bucket (-30.033, 0.0] | 1937.0000 | 46.4420 | 500 | 15.9051 | -21.4646 | 55.6989 | -21.7222 | 52.3116 | FAIL |
| B | Fold 4 | bucket (-30.031, 0.0] | 2437.0000 | 40.1767 | 730 | -16.6851 | -60.2007 | 24.0077 | -58.5804 | 21.5451 | FAIL |
| B | Pooled | Fold 1: bucket (-27.905, 0.0]; Fold 2: bucket (-29.565, 0.0]; Fold 3: bucket (-30.033, 0.0]; Fold 4: bucket (-30.031, 0.0] |  |  | 2172 | 30.9601 | 2.6545 | 56.6419 | 5.8841 | 56.8484 | PASS |

### lot_zscore

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.991, -0.556] | 146.0000 | 54.0992 | 17 | 254.6349 | 16.5470 | 704.1220 | 16.5018 | 728.8223 | PASS |
| A | Fold 2 | bucket (-0.988, -0.543] | 221.0000 | 60.5456 | 25 | -54.3877 | -242.7794 | 82.6594 | -259.2644 | 82.4203 | FAIL |
| A | Fold 3 | bucket (-0.987, -0.559] | 291.0000 | 34.8603 | 14 | -44.5388 | -191.8502 | 50.3709 | -182.9815 | 49.5045 | FAIL |
| A | Fold 4 | bucket (-0.987, -0.528] | 356.0000 | 27.5912 | 73 | -5.4203 | -93.1214 | 79.7005 | -90.0674 | 80.2696 | FAIL |
| A | Pooled | Fold 1: bucket (-0.991, -0.556]; Fold 2: bucket (-0.988, -0.543]; Fold 3: bucket (-0.987, -0.559]; Fold 4: bucket (-0.987, -0.528] |  |  | 129 | 15.1153 | -49.9901 | 90.2783 | -49.7172 | 87.4123 | FAIL |
| B | Fold 1 | bucket (-0.991, -0.556] | 146.0000 | 54.0992 | 72 | 63.5422 | -45.6146 | 207.3199 | -44.1632 | 200.1383 | FAIL |
| B | Fold 2 | bucket (-0.988, -0.543] | 221.0000 | 60.5456 | 82 | -45.3995 | -193.3755 | 103.2828 | -195.1134 | 117.5317 | FAIL |
| B | Fold 3 | bucket (-0.987, -0.559] | 291.0000 | 34.8603 | 41 | 20.9480 | -74.5296 | 107.5575 | -71.4091 | 111.0960 | FAIL |
| B | Fold 4 | bucket (-0.987, -0.528] | 356.0000 | 27.5912 | 151 | -47.5226 | -120.0219 | 15.8475 | -111.0424 | 12.0460 | FAIL |
| B | Pooled | Fold 1: bucket (-0.991, -0.556]; Fold 2: bucket (-0.988, -0.543]; Fold 3: bucket (-0.987, -0.559]; Fold 4: bucket (-0.987, -0.528] |  |  | 346 | -15.7941 | -67.2458 | 37.2168 | -63.0070 | 33.0864 | FAIL |

### amount

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.009000000000000001, 0.1] | 417.0000 | 64.9399 | 51 | 312.3922 | -14.2354 | 715.4104 | -39.4765 | 699.3721 | FAIL |
| A | Fold 2 | bucket (0.009000000000000001, 0.11] | 607.0000 | 87.4738 | 89 | 12.9161 | -251.0891 | 309.3155 | -277.0054 | 302.0223 | FAIL |
| A | Fold 3 | bucket (0.009000000000000001, 0.12] | 820.0000 | 82.8790 | 47 | -2.1610 | -247.2933 | 221.6912 | -235.8460 | 227.2603 | FAIL |
| A | Fold 4 | bucket (0.009000000000000001, 0.15] | 1056.0000 | 72.4655 | 192 | -80.4245 | -202.9428 | 36.4440 | -206.4981 | 43.3437 | FAIL |
| A | Pooled | Fold 1: bucket (0.009000000000000001, 0.1]; Fold 2: bucket (0.009000000000000001, 0.11]; Fold 3: bucket (0.009000000000000001, 0.12]; Fold 4: bucket (0.009000000000000001, 0.15] |  |  | 379 | 4.0593 | -105.4311 | 112.6533 | -100.9868 | 117.1144 | FAIL |
| B | Fold 1 | bucket (0.009000000000000001, 0.1] | 417.0000 | 64.9399 | 133 | 201.4330 | 19.9830 | 401.9961 | 26.7904 | 402.1672 | PASS |
| B | Fold 2 | bucket (0.009000000000000001, 0.11] | 607.0000 | 87.4738 | 174 | 94.4057 | -91.4108 | 297.3266 | -98.7517 | 273.4152 | FAIL |
| B | Fold 3 | bucket (0.009000000000000001, 0.12] | 820.0000 | 82.8790 | 103 | 47.5086 | -122.1658 | 219.5694 | -116.5085 | 210.2515 | FAIL |
| B | Fold 4 | bucket (0.009000000000000001, 0.15] | 1056.0000 | 72.4655 | 300 | -52.9672 | -154.4456 | 59.1693 | -161.6766 | 52.8605 | FAIL |
| B | Pooled | Fold 1: bucket (0.009000000000000001, 0.1]; Fold 2: bucket (0.009000000000000001, 0.11]; Fold 3: bucket (0.009000000000000001, 0.12]; Fold 4: bucket (0.009000000000000001, 0.15] |  |  | 710 | 45.3809 | -30.9703 | 128.4606 | -30.8359 | 121.7489 | FAIL |

### size_after_loss_delta

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.0995, 0.0] | 89.0000 | 68.2225 | 10 | 311.4844 | -172.8354 | 754.6044 | -120.0325 | 749.2875 | FAIL |
| A | Fold 2 | bucket (-0.09, 0.00574] | 123.0000 | 88.6285 | 9 | 26.6296 | -427.4583 | 243.0741 | -427.4583 | 241.6296 | FAIL |
| A | Fold 3 | bucket (-0.101, 0.0] | 162.0000 | 29.2921 | 9 | -42.0018 | -281.2907 | 173.8851 | -288.8329 | 182.0636 | FAIL |
| A | Fold 4 | bucket (-0.1, 0.0103] | 195.0000 | 15.1389 | 26 | 62.5348 | -89.8394 | 267.1912 | -95.5486 | 282.3971 | FAIL |
| A | Pooled | Fold 1: bucket (-0.0995, 0.0]; Fold 2: bucket (-0.09, 0.00574]; Fold 3: bucket (-0.101, 0.0]; Fold 4: bucket (-0.1, 0.0103] |  |  | 54 | 85.2296 | -41.7730 | 234.5714 | -41.5042 | 228.3097 | FAIL |
| B | Fold 1 | bucket (-0.0995, 0.0] | 89.0000 | 68.2225 | 40 | 50.6081 | -129.1419 | 246.7583 | -118.7291 | 239.9323 | FAIL |
| B | Fold 2 | bucket (-0.09, 0.00574] | 123.0000 | 88.6285 | 22 | -148.9448 | -402.1459 | 54.7331 | -418.2016 | 59.0139 | FAIL |
| B | Fold 3 | bucket (-0.101, 0.0] | 162.0000 | 29.2921 | 28 | 9.7739 | -97.8294 | 153.2261 | -103.2860 | 142.6394 | FAIL |
| B | Fold 4 | bucket (-0.1, 0.0103] | 195.0000 | 15.1389 | 52 | 28.8102 | -70.8117 | 131.6302 | -74.9028 | 125.0865 | FAIL |
| B | Pooled | Fold 1: bucket (-0.0995, 0.0]; Fold 2: bucket (-0.09, 0.00574]; Fold 3: bucket (-0.101, 0.0]; Fold 4: bucket (-0.1, 0.0103] |  |  | 142 | 3.6573 | -73.3450 | 83.2552 | -76.1405 | 84.1979 | FAIL |

### has_sl

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | value == 1 | 1613.0000 | -1.5603 | 252 | 55.4906 | -8.0060 | 126.8669 | -5.6418 | 127.2501 | FAIL |
| A | Fold 2 | value == 0 | 655.0000 | 7.0147 | 140 | -42.8977 | -204.2551 | 117.3574 | -203.9482 | 118.1231 | FAIL |
| A | Fold 3 | value == 0 | 943.0000 | 18.7744 | 109 | -33.2632 | -139.1635 | 65.6631 | -140.2646 | 69.6100 | FAIL |
| A | Fold 4 | value == 0 | 1164.0000 | 15.0860 | 251 | -61.5955 | -132.8796 | 8.4864 | -135.3799 | 14.1460 | FAIL |
| A | Pooled | Fold 1: value == 1; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 752 | -14.7715 | -60.2301 | 31.8823 | -61.2996 | 32.3872 | FAIL |
| B | Fold 1 | value == 1 | 1613.0000 | -1.5603 | 718 | 15.6175 | -24.9690 | 55.8631 | -25.3840 | 59.4804 | FAIL |
| B | Fold 2 | value == 0 | 655.0000 | 7.0147 | 288 | 45.5195 | -60.8822 | 149.8006 | -58.1151 | 154.6804 | FAIL |
| B | Fold 3 | value == 0 | 943.0000 | 18.7744 | 221 | -0.6520 | -64.0819 | 73.7738 | -63.9995 | 67.8031 | FAIL |
| B | Fold 4 | value == 0 | 1164.0000 | 15.0860 | 405 | -42.6951 | -101.2576 | 19.3386 | -110.1947 | 19.4640 | FAIL |
| B | Pooled | Fold 1: value == 1; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 1632 | 4.2202 | -26.2744 | 34.7161 | -27.3623 | 35.3478 | FAIL |

### has_tp

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | value == 0 | 389.0000 | 10.5999 | 97 | 202.5741 | 47.8900 | 409.0449 | 40.6073 | 389.8199 | PASS |
| A | Fold 2 | value == 0 | 562.0000 | 40.3482 | 113 | -58.7355 | -247.3270 | 116.9870 | -236.0984 | 123.0623 | FAIL |
| A | Fold 3 | value == 0 | 759.0000 | 36.3410 | 117 | -40.6800 | -138.0796 | 44.9216 | -140.4056 | 42.2991 | FAIL |
| A | Fold 4 | value == 0 | 956.0000 | 23.3301 | 238 | -46.5309 | -116.5390 | 24.9890 | -118.0242 | 34.0825 | FAIL |
| A | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 565 | -4.9935 | -63.9357 | 55.4529 | -61.1395 | 57.3400 | FAIL |
| B | Fold 1 | value == 0 | 389.0000 | 10.5999 | 173 | 107.2388 | 10.1863 | 224.5128 | 3.0544 | 221.3146 | PASS |
| B | Fold 2 | value == 0 | 562.0000 | 40.3482 | 197 | 24.9092 | -102.1890 | 147.5700 | -101.2720 | 156.9345 | FAIL |
| B | Fold 3 | value == 0 | 759.0000 | 36.3410 | 197 | -26.7978 | -91.0979 | 33.1737 | -89.9948 | 31.1596 | FAIL |
| B | Fold 4 | value == 0 | 956.0000 | 23.3301 | 358 | -46.8774 | -109.5662 | 14.1959 | -112.9411 | 14.6418 | FAIL |
| B | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 925 | 1.5115 | -41.9972 | 43.4064 | -42.9248 | 44.6221 | FAIL |

### sl_distance_pct

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.00161, 0.903] | 323.0000 | 59.1203 | 41 | 369.8157 | 88.5028 | 676.7412 | 84.0746 | 685.0581 | PASS |
| A | Fold 2 | bucket (0.00156, 0.903] | 466.0000 | 102.4295 | 100 | 269.9415 | 130.1013 | 426.9976 | 126.3195 | 428.2035 | PASS |
| A | Fold 3 | bucket (0.00167, 0.903] | 615.0000 | 146.9448 | 62 | -11.7989 | -137.1476 | 111.3388 | -135.1256 | 107.5212 | FAIL |
| A | Fold 4 | bucket (0.00164, 0.903] | 766.0000 | 119.8809 | 151 | 108.2890 | 7.1303 | 211.5904 | 5.7357 | 213.8438 | PASS |
| A | Pooled | Fold 1: bucket (0.00161, 0.903]; Fold 2: bucket (0.00156, 0.903]; Fold 3: bucket (0.00167, 0.903]; Fold 4: bucket (0.00164, 0.903] |  |  | 354 | 163.2110 | 86.4453 | 243.8121 | 90.1269 | 240.3502 | PASS |
| B | Fold 1 | bucket (0.00161, 0.903] | 323.0000 | 59.1203 | 126 | 233.3441 | 84.2618 | 388.5446 | 83.6530 | 386.0600 | PASS |
| B | Fold 2 | bucket (0.00156, 0.903] | 466.0000 | 102.4295 | 216 | 193.0393 | 96.4142 | 296.4069 | 89.3553 | 288.4947 | PASS |
| B | Fold 3 | bucket (0.00167, 0.903] | 615.0000 | 146.9448 | 124 | 5.9652 | -95.1019 | 109.0466 | -92.3444 | 111.1634 | FAIL |
| B | Fold 4 | bucket (0.00164, 0.903] | 766.0000 | 119.8809 | 245 | 63.1897 | -25.0046 | 152.8079 | -27.9827 | 150.3982 | FAIL |
| B | Pooled | Fold 1: bucket (0.00161, 0.903]; Fold 2: bucket (0.00156, 0.903]; Fold 3: bucket (0.00167, 0.903]; Fold 4: bucket (0.00164, 0.903] |  |  | 711 | 122.8115 | 68.3875 | 178.5113 | 67.3195 | 182.7826 | PASS |

### sl_usage_rate_5

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 0.6] | 188.0000 | 29.7118 | 32 | 176.9521 | 50.4368 | 354.3013 | 51.0727 | 356.7976 | PASS |
| A | Fold 2 | bucket (-0.001, 0.6] | 271.0000 | 34.2246 | 48 | -46.7792 | -129.1300 | 159.6942 | -125.9840 | 162.8492 | FAIL |
| A | Fold 3 | bucket (0.8, 1.0] | 814.0000 | 13.5976 | 75 | 27.5388 | -50.6423 | 105.4894 | -47.7382 | 114.2724 | FAIL |
| A | Fold 4 | bucket (0.8, 1.0] | 984.0000 | 13.5977 | 102 | -22.2539 | -82.2007 | 33.6261 | -80.5222 | 33.6577 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 0.6]; Fold 2: bucket (-0.001, 0.6]; Fold 3: bucket (0.8, 1.0]; Fold 4: bucket (0.8, 1.0] |  |  | 257 | 12.5003 | -30.2427 | 60.0451 | -25.6217 | 63.0892 | FAIL |
| B | Fold 1 | bucket (-0.001, 0.6] | 188.0000 | 29.7118 | 83 | 44.4461 | -36.6343 | 148.9521 | -37.9989 | 141.7234 | FAIL |
| B | Fold 2 | bucket (-0.001, 0.6] | 271.0000 | 34.2246 | 88 | -50.2702 | -133.0918 | 47.8802 | -109.6875 | 34.9307 | FAIL |
| B | Fold 3 | bucket (0.8, 1.0] | 814.0000 | 13.5976 | 170 | 13.5981 | -34.8239 | 61.2276 | -33.3830 | 62.4608 | FAIL |
| B | Fold 4 | bucket (0.8, 1.0] | 984.0000 | 13.5977 | 227 | -34.8109 | -78.1957 | 14.0506 | -80.3785 | 15.6706 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 0.6]; Fold 2: bucket (-0.001, 0.6]; Fold 3: bucket (0.8, 1.0]; Fold 4: bucket (0.8, 1.0] |  |  | 568 | -11.1358 | -41.2285 | 19.9185 | -40.3296 | 18.9212 | FAIL |

### manual_exit_rate_5

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 0.4] | 201.0000 | 40.6987 | 10 | -16.0401 | -113.5000 | 23.2311 | -107.3125 | 22.2066 | FAIL |
| A | Fold 2 | bucket (0.4, 0.6] | 192.0000 | 16.1812 | 25 | 106.3878 | -68.7098 | 265.8168 | -91.6023 | 256.4007 | FAIL |
| A | Fold 3 | bucket (0.4, 0.6] | 259.0000 | 44.9338 | 23 | 57.3077 | -62.7493 | 181.8308 | -55.2248 | 192.5725 | FAIL |
| A | Fold 4 | bucket (0.4, 0.6] | 317.0000 | 41.7294 | 63 | 64.0795 | -21.0417 | 146.0202 | -15.8919 | 142.6816 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 0.4]; Fold 2: bucket (0.4, 0.6]; Fold 3: bucket (0.4, 0.6]; Fold 4: bucket (0.4, 0.6] |  |  | 121 | 64.9123 | 5.1787 | 120.6894 | 8.0552 | 124.0516 | PASS |
| B | Fold 1 | bucket (-0.001, 0.4] | 201.0000 | 40.6987 | 110 | -78.6699 | -149.5377 | -4.7376 | -146.7979 | 1.7819 | FAIL |
| B | Fold 2 | bucket (0.4, 0.6] | 192.0000 | 16.1812 | 67 | 127.3293 | -6.9472 | 282.6522 | -8.7387 | 287.4430 | FAIL |
| B | Fold 3 | bucket (0.4, 0.6] | 259.0000 | 44.9338 | 58 | 27.4197 | -32.1637 | 95.5581 | -35.5299 | 95.8629 | FAIL |
| B | Fold 4 | bucket (0.4, 0.6] | 317.0000 | 41.7294 | 111 | 36.5931 | -17.3807 | 87.5415 | -15.5170 | 90.6667 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 0.4]; Fold 2: bucket (0.4, 0.6]; Fold 3: bucket (0.4, 0.6]; Fold 4: bucket (0.4, 0.6] |  |  | 346 | 15.9814 | -29.4786 | 64.2584 | -30.4717 | 65.8857 | FAIL |

### pnl_pct

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.026, 0.0] | 933.0000 | 16.0062 | 198 | 116.5497 | 21.5101 | 223.0899 | 14.9953 | 223.5740 | PASS |
| A | Fold 2 | bucket (-0.0299, 0.0] | 1381.0000 | 30.1920 | 238 | 83.1101 | -22.3059 | 188.8495 | -29.4376 | 199.1378 | FAIL |
| A | Fold 3 | bucket (-0.031, 0.0] | 1910.0000 | 44.0758 | 235 | 2.0499 | -47.2811 | 49.2186 | -43.3648 | 50.3480 | FAIL |
| A | Fold 4 | bucket (-0.0312, 0.0] | 2412.0000 | 39.7181 | 431 | 24.7774 | -33.1798 | 81.6329 | -37.6049 | 80.2527 | FAIL |
| A | Pooled | Fold 1: bucket (-0.026, 0.0]; Fold 2: bucket (-0.0299, 0.0]; Fold 3: bucket (-0.031, 0.0]; Fold 4: bucket (-0.0312, 0.0] |  |  | 1102 | 49.0180 | 9.6677 | 89.7553 | 9.7754 | 88.4893 | PASS |
| B | Fold 1 | bucket (-0.026, 0.0] | 933.0000 | 16.0062 | 410 | 67.2234 | 6.1100 | 130.3179 | 9.3148 | 130.5427 | PASS |
| B | Fold 2 | bucket (-0.0299, 0.0] | 1381.0000 | 30.1920 | 517 | 83.8476 | 20.5713 | 150.3551 | 15.7645 | 152.9465 | PASS |
| B | Fold 3 | bucket (-0.031, 0.0] | 1910.0000 | 44.0758 | 500 | 23.6726 | -13.2593 | 62.6248 | -14.1923 | 60.1212 | FAIL |
| B | Fold 4 | bucket (-0.0312, 0.0] | 2412.0000 | 39.7181 | 742 | -3.7807 | -48.3544 | 36.0774 | -44.8274 | 36.1004 | FAIL |
| B | Pooled | Fold 1: bucket (-0.026, 0.0]; Fold 2: bucket (-0.0299, 0.0]; Fold 3: bucket (-0.031, 0.0]; Fold 4: bucket (-0.0312, 0.0] |  |  | 2169 | 36.8565 | 8.2186 | 64.3898 | 11.3820 | 63.1741 | PASS |

### dd_from_peak_pct

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.0392, 0.443] | 408.0000 | 1.6180 | 79 | 101.5307 | 21.5293 | 204.1624 | 28.9303 | 213.6717 | PASS |
| A | Fold 2 | bucket (0.0424, 0.443] | 597.0000 | 21.1073 | 92 | 30.0263 | -47.8289 | 93.0524 | -48.1618 | 96.3497 | FAIL |
| A | Fold 3 | bucket (-0.001, 0.0073] | 2411.0000 | 21.2240 | 286 | -43.7597 | -93.9914 | 2.0402 | -87.6097 | 3.6666 | FAIL |
| A | Fold 4 | bucket (-0.001, 0.00688] | 2995.0000 | 12.3652 | 526 | -14.8557 | -69.4884 | 38.9524 | -68.6517 | 37.0788 | FAIL |
| A | Pooled | Fold 1: bucket (0.0392, 0.443]; Fold 2: bucket (0.0424, 0.443]; Fold 3: bucket (-0.001, 0.0073]; Fold 4: bucket (-0.001, 0.00688] |  |  | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |
| B | Fold 1 | bucket (0.0392, 0.443] | 408.0000 | 1.6180 | 223 | 56.8699 | 4.1983 | 112.5452 | 9.8061 | 114.4781 | PASS |
| B | Fold 2 | bucket (0.0424, 0.443] | 597.0000 | 21.1073 | 220 | -46.1105 | -107.2713 | 7.8286 | -110.1311 | 13.6831 | FAIL |
| B | Fold 3 | bucket (-0.001, 0.0073] | 2411.0000 | 21.2240 | 597 | -19.4284 | -53.2256 | 16.3088 | -52.5374 | 15.0826 | FAIL |
| B | Fold 4 | bucket (-0.001, 0.00688] | 2995.0000 | 12.3652 | 907 | -15.3455 | -53.7814 | 24.3616 | -53.8641 | 22.6686 | FAIL |
| B | Pooled | Fold 1: bucket (0.0392, 0.443]; Fold 2: bucket (0.0424, 0.443]; Fold 3: bucket (-0.001, 0.0073]; Fold 4: bucket (-0.001, 0.00688] |  |  | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |

### trade_index

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (6.0, 26.0] | 349.0000 | 22.7850 | 40 | 4.4107 | -115.3275 | 64.1759 | -139.4937 | 62.4622 | FAIL |
| A | Fold 2 | bucket (6.0, 26.0] | 543.0000 | 18.2895 | 77 | 22.2984 | -25.2891 | 107.8167 | -27.0410 | 101.8991 | FAIL |
| A | Fold 3 | bucket (6.0, 28.0] | 697.0000 | 30.2914 | 80 | -21.4930 | -107.3466 | 83.7721 | -104.1378 | 98.9620 | FAIL |
| A | Fold 4 | bucket (6.0, 31.0] | 853.0000 | 24.8202 | 153 | -14.1113 | -75.3038 | 35.9221 | -74.2946 | 34.7405 | FAIL |
| A | Pooled | Fold 1: bucket (6.0, 26.0]; Fold 2: bucket (6.0, 26.0]; Fold 3: bucket (6.0, 28.0]; Fold 4: bucket (6.0, 31.0] |  |  | 350 | -5.6716 | -41.2521 | 29.6047 | -40.8536 | 30.6805 | FAIL |
| B | Fold 1 | bucket (6.0, 26.0] | 349.0000 | 22.7850 | 194 | 10.2023 | -47.0362 | 75.4433 | -46.4967 | 80.6126 | FAIL |
| B | Fold 2 | bucket (6.0, 26.0] | 543.0000 | 18.2895 | 152 | 74.5980 | -9.0777 | 181.6934 | -4.2246 | 194.6554 | FAIL |
| B | Fold 3 | bucket (6.0, 28.0] | 697.0000 | 30.2914 | 153 | -1.4944 | -51.5121 | 59.0009 | -49.5246 | 59.1792 | FAIL |
| B | Fold 4 | bucket (6.0, 31.0] | 853.0000 | 24.8202 | 281 | -4.9137 | -41.0800 | 32.0724 | -41.0206 | 32.1830 | FAIL |
| B | Pooled | Fold 1: bucket (6.0, 26.0]; Fold 2: bucket (6.0, 26.0]; Fold 3: bucket (6.0, 28.0]; Fold 4: bucket (6.0, 31.0] |  |  | 780 | 15.0112 | -12.7391 | 47.6999 | -13.7627 | 44.3712 | FAIL |

### log_dt_close

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 5.435] | 839.0000 | -7.0830 | 162 | 51.0158 | -22.8115 | 136.8880 | -20.1230 | 128.9855 | FAIL |
| A | Fold 2 | bucket (-0.001, 5.406] | 1241.0000 | -5.3951 | 165 | 55.8377 | -17.8785 | 154.2655 | -14.9842 | 155.6592 | FAIL |
| A | Fold 3 | bucket (7.747, 10.928] | 546.0000 | 4.0228 | 40 | 50.3501 | -57.0038 | 170.4140 | -57.3259 | 168.3923 | FAIL |
| A | Fold 4 | bucket (7.67, 10.928] | 674.0000 | 5.8530 | 106 | -57.9306 | -170.1710 | 45.9424 | -168.4345 | 47.3063 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 5.435]; Fold 2: bucket (-0.001, 5.406]; Fold 3: bucket (7.747, 10.928]; Fold 4: bucket (7.67, 10.928] |  |  | 473 | 28.2265 | -16.5033 | 76.5571 | -14.4343 | 73.8746 | FAIL |
| B | Fold 1 | bucket (-0.001, 5.435] | 839.0000 | -7.0830 | 407 | -6.7996 | -47.0643 | 32.2169 | -43.4952 | 34.0185 | FAIL |
| B | Fold 2 | bucket (-0.001, 5.406] | 1241.0000 | -5.3951 | 386 | -4.8814 | -60.7301 | 49.1546 | -58.2632 | 50.2099 | FAIL |
| B | Fold 3 | bucket (7.747, 10.928] | 546.0000 | 4.0228 | 112 | -10.4504 | -92.7705 | 67.9983 | -91.0093 | 72.5861 | FAIL |
| B | Fold 4 | bucket (7.67, 10.928] | 674.0000 | 5.8530 | 197 | 18.9809 | -61.6431 | 106.4040 | -64.9943 | 101.7234 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 5.435]; Fold 2: bucket (-0.001, 5.406]; Fold 3: bucket (7.747, 10.928]; Fold 4: bucket (7.67, 10.928] |  |  | 1102 | -1.8901 | -29.6029 | 27.8939 | -31.2117 | 28.0903 | FAIL |

### trades_per_hour

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (20.398, 60.0] | 767.0000 | 18.5504 | 166 | 119.1591 | 19.5834 | 224.0158 | 16.3093 | 227.7098 | PASS |
| A | Fold 2 | bucket (19.78, 60.0] | 1124.0000 | 37.0938 | 222 | 80.4298 | -26.3044 | 184.8595 | -29.6005 | 193.8926 | FAIL |
| A | Fold 3 | bucket (24.39, 60.0] | 1523.0000 | 47.2531 | 201 | -6.5672 | -61.6481 | 46.7341 | -57.1923 | 47.9372 | FAIL |
| A | Fold 4 | bucket (26.22, 60.0] | 1877.0000 | 43.6805 | 347 | 23.2288 | -44.4425 | 88.7499 | -43.0037 | 88.4683 | FAIL |
| A | Pooled | Fold 1: bucket (20.398, 60.0]; Fold 2: bucket (19.78, 60.0]; Fold 3: bucket (24.39, 60.0]; Fold 4: bucket (26.22, 60.0] |  |  | 936 | 47.4105 | 5.4981 | 89.3123 | 6.3158 | 92.7390 | PASS |
| B | Fold 1 | bucket (20.398, 60.0] | 767.0000 | 18.5504 | 351 | 76.2575 | 15.8506 | 145.6369 | 16.7846 | 144.7777 | PASS |
| B | Fold 2 | bucket (19.78, 60.0] | 1124.0000 | 37.0938 | 450 | 84.0788 | 17.9656 | 150.8869 | 12.9128 | 156.1420 | PASS |
| B | Fold 3 | bucket (24.39, 60.0] | 1523.0000 | 47.2531 | 400 | 18.1219 | -20.9902 | 61.2380 | -23.9303 | 59.5662 | FAIL |
| B | Fold 4 | bucket (26.22, 60.0] | 1877.0000 | 43.6805 | 589 | -7.7094 | -58.4532 | 40.4989 | -57.5331 | 36.3755 | FAIL |
| B | Pooled | Fold 1: bucket (20.398, 60.0]; Fold 2: bucket (19.78, 60.0]; Fold 3: bucket (24.39, 60.0]; Fold 4: bucket (26.22, 60.0] |  |  | 1790 | 37.6032 | 7.9945 | 67.8172 | 10.9772 | 67.5290 | PASS |

### prior_campaigns

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 1.0] | 1462.0000 | 0.3729 | 353 | 97.0360 | 33.9953 | 170.3849 | 28.9265 | 170.0241 | PASS |
| A | Fold 2 | bucket (-0.001, 1.0] | 1915.0000 | 17.0333 | 450 | 60.7849 | -6.5110 | 132.7938 | -9.1753 | 136.7631 | FAIL |
| A | Fold 3 | bucket (-0.001, 1.0] | 2508.0000 | 28.0467 | 435 | -16.9897 | -57.0341 | 21.1132 | -52.6820 | 21.7021 | FAIL |
| A | Fold 4 | bucket (-0.001, 1.0] | 3037.0000 | 22.0338 | 870 | -12.8222 | -48.8304 | 21.3436 | -50.6932 | 20.6245 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 1.0]; Fold 2: bucket (-0.001, 1.0]; Fold 3: bucket (-0.001, 1.0]; Fold 4: bucket (-0.001, 1.0] |  |  | 2108 | 20.4275 | -5.2246 | 46.6902 | -3.0822 | 47.1857 | FAIL |
| B | Fold 1 | bucket (-0.001, 1.0] | 1462.0000 | 0.3729 | 453 | 70.8025 | 14.6381 | 131.8469 | 14.8414 | 137.2600 | PASS |
| B | Fold 2 | bucket (-0.001, 1.0] | 1915.0000 | 17.0333 | 593 | 63.6129 | 5.0860 | 123.9474 | 4.5910 | 128.2776 | PASS |
| B | Fold 3 | bucket (-0.001, 1.0] | 2508.0000 | 28.0467 | 529 | -6.4738 | -42.1414 | 30.0394 | -39.4875 | 28.3758 | FAIL |
| B | Fold 4 | bucket (-0.001, 1.0] | 3037.0000 | 22.0338 | 993 | -9.2980 | -44.8105 | 24.3643 | -44.4538 | 24.8989 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 1.0]; Fold 2: bucket (-0.001, 1.0]; Fold 3: bucket (-0.001, 1.0]; Fold 4: bucket (-0.001, 1.0] |  |  | 2568 | 22.2502 | -1.0509 | 44.1620 | 0.0855 | 45.5597 | FAIL |

### prior_campaigns_x_loss_streak_ge_2

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-0.001, 10.0] | 2037.0000 | -9.1643 | 371 | 97.3440 | 37.4858 | 166.4741 | 34.1013 | 167.2310 | PASS |
| A | Fold 2 | bucket (-0.001, 10.0] | 2986.0000 | 4.4512 | 454 | 59.8627 | -6.7448 | 131.7592 | -9.8239 | 135.2898 | FAIL |
| A | Fold 3 | bucket (-0.001, 12.0] | 4019.0000 | 14.5026 | 464 | -17.0781 | -54.1299 | 17.8990 | -50.6750 | 19.2280 | FAIL |
| A | Fold 4 | bucket (-0.001, 12.0] | 4992.0000 | 11.0854 | 901 | -8.6805 | -44.1341 | 24.3377 | -45.5318 | 23.6053 | FAIL |
| A | Pooled | Fold 1: bucket (-0.001, 10.0]; Fold 2: bucket (-0.001, 10.0]; Fold 3: bucket (-0.001, 12.0]; Fold 4: bucket (-0.001, 12.0] |  |  | 2190 | 21.7109 | -2.6464 | 47.4330 | -1.0475 | 47.8438 | FAIL |
| B | Fold 1 | bucket (-0.001, 10.0] | 2037.0000 | -9.1643 | 949 | 33.6765 | -4.5669 | 73.0288 | -5.1586 | 74.1730 | FAIL |
| B | Fold 2 | bucket (-0.001, 10.0] | 2986.0000 | 4.4512 | 1031 | 44.2200 | 4.8894 | 85.1959 | 1.6685 | 89.5541 | PASS |
| B | Fold 3 | bucket (-0.001, 12.0] | 4019.0000 | 14.5026 | 973 | -3.0294 | -27.3938 | 23.9678 | -28.8419 | 21.8199 | FAIL |
| B | Fold 4 | bucket (-0.001, 12.0] | 4992.0000 | 11.0854 | 1590 | -12.2994 | -37.9066 | 13.8224 | -37.7091 | 11.2897 | FAIL |
| B | Pooled | Fold 1: bucket (-0.001, 10.0]; Fold 2: bucket (-0.001, 10.0]; Fold 3: bucket (-0.001, 12.0]; Fold 4: bucket (-0.001, 12.0] |  |  | 4543 | 12.1167 | -5.0187 | 29.6998 | -4.8739 | 30.0853 | FAIL |

### shared_ip

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | value == 0 | 301.0000 | 24.7785 | 40 | -2.2460 | -213.9163 | 345.1620 | -210.5301 | 348.4013 | FAIL |
| A | Fold 2 | value == 0 | 341.0000 | 21.6085 | 126 | 13.0260 | -47.4449 | 109.0673 | -46.1826 | 105.7313 | FAIL |
| A | Fold 3 | value == 0 | 467.0000 | 19.2929 | 100 | 29.9431 | -30.4058 | 93.4504 | -29.2590 | 88.1667 | FAIL |
| A | Fold 4 | value == 0 | 567.0000 | 21.1712 | 386 | -14.7942 | -68.8853 | 28.9794 | -67.0633 | 28.8847 | FAIL |
| A | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 652 | -1.7865 | -37.9764 | 35.1465 | -36.2795 | 32.3479 | FAIL |
| B | Fold 1 | value == 0 | 301.0000 | 24.7785 | 40 | -2.2460 | -216.0143 | 308.6610 | -226.7980 | 306.0678 | FAIL |
| B | Fold 2 | value == 0 | 341.0000 | 21.6085 | 126 | 13.0260 | -48.0272 | 102.1454 | -45.2191 | 108.4587 | FAIL |
| B | Fold 3 | value == 0 | 467.0000 | 19.2929 | 100 | 29.9431 | -27.4580 | 87.9285 | -31.7703 | 87.8415 | FAIL |
| B | Fold 4 | value == 0 | 567.0000 | 21.1712 | 386 | -14.7942 | -69.7711 | 30.2781 | -71.2655 | 28.4072 | FAIL |
| B | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 652 | -1.7865 | -36.4565 | 34.0950 | -36.8194 | 34.8910 | FAIL |

### ip_cluster_size

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.999, 3.0] | 820.0000 | 9.5795 | 149 | 112.8920 | -9.7486 | 256.3631 | -16.5942 | 257.3391 | FAIL |
| A | Fold 2 | bucket (2.0, 4.0] | 393.0000 | 63.5838 | 63 | 90.3059 | -47.1215 | 220.1446 | -49.4741 | 225.4712 | FAIL |
| A | Fold 3 | bucket (2.0, 4.0] | 559.0000 | 67.7273 | 106 | -11.1775 | -77.9819 | 72.7852 | -68.8811 | 68.7737 | FAIL |
| A | Fold 4 | bucket (2.0, 4.0] | 770.0000 | 52.0109 | 51 | 72.2266 | -61.5590 | 319.6152 | -55.7823 | 319.4774 | FAIL |
| A | Pooled | Fold 1: bucket (0.999, 3.0]; Fold 2: bucket (2.0, 4.0]; Fold 3: bucket (2.0, 4.0]; Fold 4: bucket (2.0, 4.0] |  |  | 369 | 67.7748 | 10.4028 | 143.3167 | 8.1179 | 144.4523 | PASS |
| B | Fold 1 | bucket (0.999, 3.0] | 820.0000 | 9.5795 | 212 | 101.4005 | -5.2195 | 209.9642 | -4.0168 | 213.9903 | FAIL |
| B | Fold 2 | bucket (2.0, 4.0] | 393.0000 | 63.5838 | 166 | 77.5369 | -8.2157 | 181.4595 | -17.3480 | 183.6035 | FAIL |
| B | Fold 3 | bucket (2.0, 4.0] | 559.0000 | 67.7273 | 211 | 10.3738 | -40.2860 | 78.4228 | -42.7157 | 80.7948 | FAIL |
| B | Fold 4 | bucket (2.0, 4.0] | 770.0000 | 52.0109 | 246 | -0.2126 | -46.0267 | 51.7963 | -48.2261 | 50.4999 | FAIL |
| B | Pooled | Fold 1: bucket (0.999, 3.0]; Fold 2: bucket (2.0, 4.0]; Fold 3: bucket (2.0, 4.0]; Fold 4: bucket (2.0, 4.0] |  |  | 835 | 43.7181 | 5.2036 | 89.9204 | 6.1015 | 87.4156 | PASS |

### challenge_type

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | category == 11 | 2037.0000 | -9.1643 | 0 |  |  |  |  |  | FAIL |
| A | Fold 2 | category == unknown | 949.0000 | 33.6765 | 242 | 64.7794 | -25.2366 | 167.6685 | -28.9106 | 173.2615 | FAIL |
| A | Fold 3 | category == unknown | 1430.0000 | 33.7952 | 464 | -17.0781 | -54.1299 | 17.8990 | -50.6750 | 19.2280 | FAIL |
| A | Fold 4 | category == unknown | 2403.0000 | 18.8845 | 901 | -8.6805 | -44.1341 | 24.3377 | -45.5318 | 23.6053 | FAIL |
| A | Pooled | Fold 1: category == 11; Fold 2: category == unknown; Fold 3: category == unknown; Fold 4: category == unknown |  |  | 1607 | -0.0428 | -26.3977 | 27.9249 | -27.1017 | 27.2464 | FAIL |
| B | Fold 1 | category == 11 | 2037.0000 | -9.1643 | 0 |  |  |  |  |  | FAIL |
| B | Fold 2 | category == unknown | 949.0000 | 33.6765 | 481 | 34.0295 | -21.6531 | 92.5929 | -21.8663 | 93.8902 | FAIL |
| B | Fold 3 | category == unknown | 1430.0000 | 33.7952 | 973 | -3.0294 | -27.3938 | 23.9678 | -28.8419 | 21.8199 | FAIL |
| B | Fold 4 | category == unknown | 2403.0000 | 18.8845 | 1590 | -12.2994 | -37.9066 | 13.8224 | -37.7091 | 11.2897 | FAIL |
| B | Pooled | Fold 1: category == 11; Fold 2: category == unknown; Fold 3: category == unknown; Fold 4: category == unknown |  |  | 3044 | -2.0156 | -20.5906 | 15.9126 | -20.3529 | 17.1078 | FAIL |

### gold_vol_prev_day

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.0182, 0.0237] | 519.0000 | 74.3331 | 187 | 80.3847 | -6.9535 | 192.3130 | -7.0811 | 197.5380 | FAIL |
| A | Fold 2 | bucket (0.0219, 0.0237] | 519.0000 | 74.3331 | 0 |  |  |  |  |  | FAIL |
| A | Fold 3 | bucket (0.0334, 0.0499] | 481.0000 | 34.0295 | 220 | -37.2968 | -81.1750 | 6.5273 | -81.5073 | 7.6872 | FAIL |
| A | Fold 4 | bucket (0.0182, 0.0197] | 1116.0000 | 27.9361 | 587 | 4.6940 | -41.4373 | 48.6676 | -40.6793 | 50.2396 | FAIL |
| A | Pooled | Fold 1: bucket (0.0182, 0.0237]; Fold 2: bucket (0.0219, 0.0237]; Fold 3: bucket (0.0334, 0.0499]; Fold 4: bucket (0.0182, 0.0197] |  |  | 994 | 9.6399 | -23.1782 | 44.2516 | -23.1820 | 45.4935 | FAIL |
| B | Fold 1 | bucket (0.0182, 0.0237] | 519.0000 | 74.3331 | 511 | 22.5302 | -24.6169 | 73.1752 | -21.1244 | 73.6989 | FAIL |
| B | Fold 2 | bucket (0.0219, 0.0237] | 519.0000 | 74.3331 | 0 |  |  |  |  |  | FAIL |
| B | Fold 3 | bucket (0.0334, 0.0499] | 481.0000 | 34.0295 | 409 | -13.4423 | -47.4044 | 21.8471 | -46.3339 | 22.1206 | FAIL |
| B | Fold 4 | bucket (0.0182, 0.0197] | 1116.0000 | 27.9361 | 1094 | -11.8437 | -44.5774 | 20.6988 | -43.7051 | 17.6762 | FAIL |
| B | Pooled | Fold 1: bucket (0.0182, 0.0237]; Fold 2: bucket (0.0219, 0.0237]; Fold 3: bucket (0.0334, 0.0499]; Fold 4: bucket (0.0182, 0.0197] |  |  | 2014 | -3.4468 | -26.4825 | 18.4723 | -24.2313 | 17.5196 | FAIL |

### sl_widening_delta

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.000498, 0.00844] | 101.0000 | 107.0482 | 13 | -78.6137 | -236.8334 | 106.6620 | -279.1565 | 123.8420 | FAIL |
| A | Fold 2 | bucket (0.000484, 0.00844] | 155.0000 | 60.8600 | 30 | 187.8834 | 10.9027 | 422.2673 | 11.1201 | 423.1326 | PASS |
| A | Fold 3 | bucket (0.000552, 0.00844] | 198.0000 | 125.1154 | 23 | -78.3550 | -245.6569 | 51.8811 | -235.4629 | 58.1163 | FAIL |
| A | Fold 4 | bucket (0.000551, 0.00844] | 240.0000 | 91.5272 | 47 | 45.5097 | -66.1614 | 134.7551 | -63.5419 | 139.4800 | FAIL |
| A | Pooled | Fold 1: bucket (0.000498, 0.00844]; Fold 2: bucket (0.000484, 0.00844]; Fold 3: bucket (0.000552, 0.00844]; Fold 4: bucket (0.000551, 0.00844] |  |  | 113 | 43.8169 | -31.8623 | 119.7032 | -31.4422 | 121.9822 | FAIL |
| B | Fold 1 | bucket (0.000498, 0.00844] | 101.0000 | 107.0482 | 50 | -37.4914 | -171.2601 | 107.7455 | -179.8913 | 108.3638 | FAIL |
| B | Fold 2 | bucket (0.000484, 0.00844] | 155.0000 | 60.8600 | 62 | 269.0169 | 66.0511 | 453.8266 | 69.0473 | 462.8738 | PASS |
| B | Fold 3 | bucket (0.000552, 0.00844] | 198.0000 | 125.1154 | 42 | -66.8172 | -186.3842 | 32.5097 | -181.7544 | 33.7774 | FAIL |
| B | Fold 4 | bucket (0.000551, 0.00844] | 240.0000 | 91.5272 | 85 | 39.4237 | -47.6057 | 123.3008 | -49.2409 | 123.8462 | FAIL |
| B | Pooled | Fold 1: bucket (0.000498, 0.00844]; Fold 2: bucket (0.000484, 0.00844]; Fold 3: bucket (0.000552, 0.00844]; Fold 4: bucket (0.000551, 0.00844] |  |  | 239 | 64.2225 | -10.7240 | 144.6479 | -16.1136 | 143.7137 | FAIL |

### same_direction_reentry

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | value == 0 | 1596.0000 | -2.4459 | 296 | 120.8887 | 50.7676 | 200.0411 | 46.2122 | 201.2117 | PASS |
| A | Fold 2 | value == 0 | 2350.0000 | 9.3936 | 368 | 49.4052 | -22.8378 | 125.7661 | -26.8057 | 128.7157 | FAIL |
| A | Fold 3 | value == 0 | 3198.0000 | 19.1965 | 370 | -23.2803 | -66.9585 | 17.3960 | -62.3442 | 18.9575 | FAIL |
| A | Fold 4 | value == 0 | 3983.0000 | 14.8473 | 708 | -10.7383 | -52.5980 | 28.3117 | -51.6685 | 26.5641 | FAIL |
| A | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 1742 | 21.6692 | -6.1546 | 51.5890 | -5.1135 | 50.5901 | FAIL |
| B | Fold 1 | value == 0 | 1596.0000 | -2.4459 | 754 | 34.4542 | -8.2841 | 78.4270 | -9.4162 | 81.8282 | FAIL |
| B | Fold 2 | value == 0 | 2350.0000 | 9.3936 | 848 | 46.3625 | 0.0661 | 91.0116 | -0.7887 | 95.8172 | FAIL |
| B | Fold 3 | value == 0 | 3198.0000 | 19.1965 | 785 | -2.8707 | -31.3234 | 29.4400 | -32.2806 | 26.5492 | FAIL |
| B | Fold 4 | value == 0 | 3983.0000 | 14.8473 | 1268 | -12.3438 | -41.7264 | 17.1191 | -42.0761 | 14.8911 | FAIL |
| B | Pooled | Fold 1: value == 0; Fold 2: value == 0; Fold 3: value == 0; Fold 4: value == 0 |  |  | 3655 | 12.9654 | -6.5032 | 32.6190 | -7.7084 | 33.0382 | FAIL |

### size_delta_ratio

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.883, 1.13] | 279.0000 | 20.8458 | 61 | 139.6401 | -13.6989 | 303.3363 | -3.7317 | 301.1064 | FAIL |
| A | Fold 2 | bucket (0.892, 1.111] | 413.0000 | 35.5667 | 35 | -19.6743 | -186.0126 | 205.5505 | -190.4219 | 195.7079 | FAIL |
| A | Fold 3 | bucket (0.884, 1.12] | 546.0000 | 13.8077 | 65 | -10.8877 | -80.1199 | 73.3575 | -77.7579 | 88.9406 | FAIL |
| A | Fold 4 | bucket (0.889, 1.119] | 671.0000 | 15.6954 | 110 | 36.5467 | -57.6551 | 140.9002 | -56.9203 | 137.3697 | FAIL |
| A | Pooled | Fold 1: bucket (0.883, 1.13]; Fold 2: bucket (0.892, 1.111]; Fold 3: bucket (0.884, 1.12]; Fold 4: bucket (0.889, 1.119] |  |  | 271 | 41.1140 | -17.3202 | 108.9514 | -15.8091 | 106.4209 | FAIL |
| B | Fold 1 | bucket (0.883, 1.13] | 279.0000 | 20.8458 | 153 | 49.6562 | -47.5408 | 155.7665 | -45.5810 | 152.1671 | FAIL |
| B | Fold 2 | bucket (0.892, 1.111] | 413.0000 | 35.5667 | 109 | -66.4629 | -212.4459 | 47.6811 | -209.1892 | 48.7185 | FAIL |
| B | Fold 3 | bucket (0.884, 1.12] | 546.0000 | 13.8077 | 139 | 16.3936 | -48.9558 | 86.4315 | -42.7845 | 90.7160 | FAIL |
| B | Fold 4 | bucket (0.889, 1.119] | 671.0000 | 15.6954 | 208 | 29.3777 | -35.3307 | 106.5175 | -40.4543 | 99.5071 | FAIL |
| B | Pooled | Fold 1: bucket (0.883, 1.13]; Fold 2: bucket (0.892, 1.111]; Fold 3: bucket (0.884, 1.12]; Fold 4: bucket (0.889, 1.119] |  |  | 609 | 14.3551 | -29.6350 | 60.6375 | -30.2738 | 56.8237 | FAIL |

### trader_prior_tilt

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-381.251, 71.7] | 1847.0000 | -8.5912 | 369 | 93.9718 | 33.0753 | 162.3152 | 30.9624 | 163.0155 | PASS |
| A | Fold 2 | bucket (-387.123, 64.654] | 2701.0000 | 4.6965 | 452 | 59.1396 | -7.0466 | 131.0490 | -10.0978 | 134.5399 | FAIL |
| A | Fold 3 | bucket (-394.97499999999997, 55.231] | 3597.0000 | 14.9728 | 457 | -16.6677 | -54.9542 | 18.7332 | -50.6915 | 20.8024 | FAIL |
| A | Fold 4 | bucket (-399.381, 49.944] | 4460.0000 | 12.2251 | 897 | -8.6176 | -44.1364 | 24.4175 | -45.6362 | 23.8151 | FAIL |
| A | Pooled | Fold 1: bucket (-381.251, 71.7]; Fold 2: bucket (-387.123, 64.654]; Fold 3: bucket (-394.97499999999997, 55.231]; Fold 4: bucket (-399.381, 49.944] |  |  | 2175 | 21.1768 | -3.0976 | 46.6904 | -1.6107 | 47.2618 | FAIL |
| B | Fold 1 | bucket (-381.251, 71.7] | 1847.0000 | -8.5912 | 861 | 32.6794 | -8.4165 | 73.9218 | -8.3512 | 76.6103 | FAIL |
| B | Fold 2 | bucket (-387.123, 64.654] | 2701.0000 | 4.6965 | 914 | 45.1614 | 0.2364 | 91.1845 | -1.1809 | 95.9441 | FAIL |
| B | Fold 3 | bucket (-394.97499999999997, 55.231] | 3597.0000 | 14.9728 | 876 | -0.3301 | -26.0532 | 28.6252 | -27.0007 | 25.6859 | FAIL |
| B | Fold 4 | bucket (-399.381, 49.944] | 4460.0000 | 12.2251 | 1444 | -9.3998 | -37.4767 | 17.5906 | -37.1200 | 15.6143 | FAIL |
| B | Pooled | Fold 1: bucket (-381.251, 71.7]; Fold 2: bucket (-387.123, 64.654]; Fold 3: bucket (-394.97499999999997, 55.231]; Fold 4: bucket (-399.381, 49.944] |  |  | 4095 | 13.5658 | -4.8834 | 32.6031 | -5.4944 | 33.0676 | FAIL |

### trader_prior_sl_discipline

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (0.00134, 0.00169] | 1464.0000 | 12.0967 | 340 | 96.0157 | 30.6585 | 171.4011 | 27.8790 | 172.1254 | PASS |
| A | Fold 2 | bucket (0.00143, 0.00149] | 1444.0000 | 28.5996 | 411 | 46.2416 | -23.5326 | 124.3019 | -28.5091 | 126.8827 | FAIL |
| A | Fold 3 | bucket (0.0014, 0.00145] | 1953.0000 | 33.6519 | 397 | -16.9821 | -58.8703 | 22.8297 | -57.3106 | 23.5813 | FAIL |
| A | Fold 4 | bucket (0.00137, 0.0014] | 2336.0000 | 29.2269 | 789 | -19.6597 | -59.9853 | 15.9263 | -58.8669 | 16.3228 | FAIL |
| A | Pooled | Fold 1: bucket (0.00134, 0.00169]; Fold 2: bucket (0.00143, 0.00149]; Fold 3: bucket (0.0014, 0.00145]; Fold 4: bucket (0.00137, 0.0014] |  |  | 1937 | 15.1767 | -11.7609 | 42.9369 | -10.7336 | 42.4778 | FAIL |
| B | Fold 1 | bucket (0.00134, 0.00169] | 1464.0000 | 12.0967 | 491 | 42.8447 | -15.2488 | 109.1090 | -17.3339 | 114.6978 | FAIL |
| B | Fold 2 | bucket (0.00143, 0.00149] | 1444.0000 | 28.5996 | 484 | 55.2339 | -12.1776 | 130.6716 | -14.3581 | 133.3571 | FAIL |
| B | Fold 3 | bucket (0.0014, 0.00145] | 1953.0000 | 33.6519 | 427 | -6.8093 | -47.2336 | 36.0474 | -46.8453 | 31.8403 | FAIL |
| B | Fold 4 | bucket (0.00137, 0.0014] | 2336.0000 | 29.2269 | 825 | -27.0072 | -67.8209 | 10.8676 | -67.6412 | 9.2612 | FAIL |
| B | Pooled | Fold 1: bucket (0.00134, 0.00169]; Fold 2: bucket (0.00143, 0.00149]; Fold 3: bucket (0.0014, 0.00145]; Fold 4: bucket (0.00137, 0.0014] |  |  | 2227 | 10.1399 | -15.3824 | 35.7106 | -15.0703 | 36.8145 | FAIL |

### trader_prior_survival

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (1.0370000000000001, 1.951] | 1417.0000 | 6.1035 | 336 | 77.4954 | 18.7897 | 150.4602 | 10.7498 | 151.3756 | PASS |
| A | Fold 2 | bucket (1.893, 2.422] | 436.0000 | 28.3275 | 10 | -165.0369 | -1753.9249 | 573.9991 | -1647.0455 | 573.9991 | FAIL |
| A | Fold 3 | bucket (1.792, 2.343] | 574.0000 | 61.1358 | 16 | -63.4784 | -250.8654 | 199.4000 | -250.8654 | 199.4000 | FAIL |
| A | Fold 4 | bucket (1.723, 2.307] | 725.0000 | 54.1712 | 12 | 231.8919 | -316.0755 | 502.7238 | -329.0605 | 467.3187 | FAIL |
| A | Pooled | Fold 1: bucket (1.0370000000000001, 1.951]; Fold 2: bucket (1.893, 2.422]; Fold 3: bucket (1.792, 2.343]; Fold 4: bucket (1.723, 2.307] |  |  | 374 | 69.9336 | 4.2307 | 137.6970 | 3.8667 | 143.0321 | PASS |
| B | Fold 1 | bucket (1.0370000000000001, 1.951] | 1417.0000 | 6.1035 | 574 | 37.8288 | -5.5759 | 85.5493 | -4.3251 | 91.3556 | FAIL |
| B | Fold 2 | bucket (1.893, 2.422] | 436.0000 | 28.3275 | 152 | 84.8397 | -67.6710 | 235.8640 | -64.5951 | 217.6764 | FAIL |
| B | Fold 3 | bucket (1.792, 2.343] | 574.0000 | 61.1358 | 112 | 26.1818 | -21.1362 | 86.1904 | -22.9814 | 79.9641 | FAIL |
| B | Fold 4 | bucket (1.723, 2.307] | 725.0000 | 54.1712 | 117 | 18.1142 | -108.2349 | 134.0831 | -119.0573 | 136.5863 | FAIL |
| B | Pooled | Fold 1: bucket (1.0370000000000001, 1.951]; Fold 2: bucket (1.893, 2.422]; Fold 3: bucket (1.792, 2.343]; Fold 4: bucket (1.723, 2.307] |  |  | 955 | 41.5299 | 4.0038 | 81.1146 | 2.0836 | 81.2294 | PASS |

## Appended Balance-Derived Per-Feature Tables

### cum_pnl_usd

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-130.184, 0.0] | 933.0000 | 16.0062 | 198 | 116.5497 | 21.5101 | 223.0899 | 14.9953 | 223.5740 | PASS |
| A | Fold 2 | bucket (-149.68, 0.0] | 1381.0000 | 30.1920 | 238 | 83.1101 | -22.3059 | 188.8495 | -29.4376 | 199.1378 | FAIL |
| A | Fold 3 | bucket (-155.224, 0.0] | 1910.0000 | 44.0758 | 235 | 2.0499 | -47.2811 | 49.2186 | -43.3648 | 50.3480 | FAIL |
| A | Fold 4 | bucket (-155.9, 0.0] | 2412.0000 | 39.7181 | 431 | 24.7774 | -33.1798 | 81.6329 | -37.6049 | 80.2527 | FAIL |
| A | Pooled | Fold 1: bucket (-130.184, 0.0]; Fold 2: bucket (-149.68, 0.0]; Fold 3: bucket (-155.224, 0.0]; Fold 4: bucket (-155.9, 0.0] |  |  | 1102 | 49.0180 | 9.6677 | 89.7553 | 9.7754 | 88.4893 | PASS |
| B | Fold 1 | bucket (-130.184, 0.0] | 933.0000 | 16.0062 | 410 | 67.2234 | 6.1100 | 130.3179 | 9.3148 | 130.5427 | PASS |
| B | Fold 2 | bucket (-149.68, 0.0] | 1381.0000 | 30.1920 | 517 | 83.8476 | 20.5713 | 150.3551 | 15.7645 | 152.9465 | PASS |
| B | Fold 3 | bucket (-155.224, 0.0] | 1910.0000 | 44.0758 | 500 | 23.6726 | -13.2593 | 62.6248 | -14.1923 | 60.1212 | FAIL |
| B | Fold 4 | bucket (-155.9, 0.0] | 2412.0000 | 39.7181 | 742 | -3.7807 | -48.3544 | 36.0774 | -44.8274 | 36.1004 | FAIL |
| B | Pooled | Fold 1: bucket (-130.184, 0.0]; Fold 2: bucket (-149.68, 0.0]; Fold 3: bucket (-155.224, 0.0]; Fold 4: bucket (-155.9, 0.0] |  |  | 2169 | 36.8565 | 8.2186 | 64.3898 | 11.3820 | 63.1741 | PASS |

### dd_from_peak_usd

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (195.992, 2213.23] | 408.0000 | 1.6180 | 79 | 101.5307 | 21.5293 | 204.1624 | 28.9303 | 213.6717 | PASS |
| A | Fold 2 | bucket (212.05, 2213.23] | 597.0000 | 21.1073 | 92 | 30.0263 | -47.8289 | 93.0524 | -48.1618 | 96.3497 | FAIL |
| A | Fold 3 | bucket (-0.001, 36.496] | 2411.0000 | 21.2240 | 286 | -43.7597 | -93.9914 | 2.0402 | -87.6097 | 3.6666 | FAIL |
| A | Fold 4 | bucket (-0.001, 34.412] | 2995.0000 | 12.3652 | 526 | -14.8557 | -69.4884 | 38.9524 | -68.6517 | 37.0788 | FAIL |
| A | Pooled | Fold 1: bucket (195.992, 2213.23]; Fold 2: bucket (212.05, 2213.23]; Fold 3: bucket (-0.001, 36.496]; Fold 4: bucket (-0.001, 34.412] |  |  | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |
| B | Fold 1 | bucket (195.992, 2213.23] | 408.0000 | 1.6180 | 223 | 56.8699 | 4.1983 | 112.5452 | 9.8061 | 114.4781 | PASS |
| B | Fold 2 | bucket (212.05, 2213.23] | 597.0000 | 21.1073 | 220 | -46.1105 | -107.2713 | 7.8286 | -110.1311 | 13.6831 | FAIL |
| B | Fold 3 | bucket (-0.001, 36.496] | 2411.0000 | 21.2240 | 597 | -19.4284 | -53.2256 | 16.3088 | -52.5374 | 15.0826 | FAIL |
| B | Fold 4 | bucket (-0.001, 34.412] | 2995.0000 | 12.3652 | 907 | -15.3455 | -53.7814 | 24.3616 | -53.8641 | 22.6686 | FAIL |
| B | Pooled | Fold 1: bucket (195.992, 2213.23]; Fold 2: bucket (212.05, 2213.23]; Fold 3: bucket (-0.001, 36.496]; Fold 4: bucket (-0.001, 34.412] |  |  | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |

### breach_proximity_usd

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (-2013.231, 4.008] | 408.0000 | 1.6180 | 79 | 101.5307 | 21.5293 | 204.1624 | 28.9303 | 213.6717 | PASS |
| A | Fold 2 | bucket (-2013.231, -12.05] | 598.0000 | 20.3813 | 92 | 30.0263 | -47.8289 | 93.0524 | -48.1618 | 96.3497 | FAIL |
| A | Fold 3 | bucket (163.504, 200.0] | 2411.0000 | 21.2240 | 286 | -43.7597 | -93.9914 | 2.0402 | -87.6097 | 3.6666 | FAIL |
| A | Fold 4 | bucket (165.588, 200.0] | 2995.0000 | 12.3652 | 526 | -14.8557 | -69.4884 | 38.9524 | -68.6517 | 37.0788 | FAIL |
| A | Pooled | Fold 1: bucket (-2013.231, 4.008]; Fold 2: bucket (-2013.231, -12.05]; Fold 3: bucket (163.504, 200.0]; Fold 4: bucket (165.588, 200.0] |  |  | 983 | -9.7111 | -44.2414 | 25.9201 | -40.3174 | 23.7440 | FAIL |
| B | Fold 1 | bucket (-2013.231, 4.008] | 408.0000 | 1.6180 | 223 | 56.8699 | 4.1983 | 112.5452 | 9.8061 | 114.4781 | PASS |
| B | Fold 2 | bucket (-2013.231, -12.05] | 598.0000 | 20.3813 | 220 | -46.1105 | -107.2713 | 7.8286 | -110.1311 | 13.6831 | FAIL |
| B | Fold 3 | bucket (163.504, 200.0] | 2411.0000 | 21.2240 | 597 | -19.4284 | -53.2256 | 16.3088 | -52.5374 | 15.0826 | FAIL |
| B | Fold 4 | bucket (165.588, 200.0] | 2995.0000 | 12.3652 | 907 | -15.3455 | -53.7814 | 24.3616 | -53.8641 | 22.6686 | FAIL |
| B | Pooled | Fold 1: bucket (-2013.231, 4.008]; Fold 2: bucket (-2013.231, -12.05]; Fold 3: bucket (163.504, 200.0]; Fold 4: bucket (165.588, 200.0] |  |  | 1947 | -11.8025 | -33.9839 | 9.6455 | -34.2030 | 12.0246 | FAIL |

### target_proximity_usd

| track | fold | selected_bucket | train_bucket_n | train_bucket_mean_reverse_profit_per_lot | n_selected | raw_mean_reverse_profit_per_lot | trader_ci_lo | trader_ci_hi | ip_ci_lo | ip_ci_hi | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Fold 1 | bucket (400.0, 530.184] | 295.0000 | 13.6720 | 62 | 70.0906 | -72.3001 | 241.9414 | -75.7347 | 234.6790 | FAIL |
| A | Fold 2 | bucket (281.05, 400.0] | 1326.0000 | 19.7134 | 226 | 71.8361 | -42.0935 | 177.3372 | -42.8226 | 187.0318 | FAIL |
| A | Fold 3 | bucket (289.014, 400.0] | 1789.0000 | 35.9232 | 213 | -30.6667 | -83.5611 | 23.2325 | -80.7267 | 26.2780 | FAIL |
| A | Fold 4 | bucket (296.26, 400.0] | 2204.0000 | 32.0543 | 409 | -4.9170 | -67.4478 | 54.1615 | -66.1669 | 53.2593 | FAIL |
| A | Pooled | Fold 1: bucket (400.0, 530.184]; Fold 2: bucket (281.05, 400.0]; Fold 3: bucket (289.014, 400.0]; Fold 4: bucket (296.26, 400.0] |  |  | 910 | 13.2280 | -30.0540 | 58.5875 | -28.9008 | 56.2392 | FAIL |
| B | Fold 1 | bucket (400.0, 530.184] | 295.0000 | 13.6720 | 131 | 3.3293 | -96.9045 | 101.7554 | -91.1495 | 99.3743 | FAIL |
| B | Fold 2 | bucket (281.05, 400.0] | 1326.0000 | 19.7134 | 493 | 75.0252 | 9.5448 | 140.4995 | 7.3874 | 148.1788 | PASS |
| B | Fold 3 | bucket (289.014, 400.0] | 1789.0000 | 35.9232 | 458 | -0.9223 | -38.2271 | 38.9293 | -41.5830 | 40.1726 | FAIL |
| B | Fold 4 | bucket (296.26, 400.0] | 2204.0000 | 32.0543 | 690 | -7.6016 | -54.2019 | 38.9640 | -53.7153 | 35.1130 | FAIL |
| B | Pooled | Fold 1: bucket (400.0, 530.184]; Fold 2: bucket (281.05, 400.0]; Fold 3: bucket (289.014, 400.0]; Fold 4: bucket (296.26, 400.0] |  |  | 1772 | 17.9210 | -9.6103 | 46.8645 | -9.6272 | 48.8923 | FAIL |
