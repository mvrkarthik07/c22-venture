# Design Annex Stats

## Sample

| quantity | value | method | n_basis |
| --- | --- | --- | --- |
| primary_positions | 6582 | feature rows in campaigns 53-65 merged one-to-one to raw positions | 6582 |
| primary_campaigns | 13 | distinct campaignId in campaigns 53-65 | 13 |
| distinct_account_ids | 496 | distinct accountId across the primary era | 496 |
| campaign_account_pairs | 2117 | distinct (campaignId, accountId) pairs | 2117 |

## Sigma

| sigma_variant | std_dev | winsor_lower | winsor_upper | method | n_rows |
| --- | --- | --- | --- | --- | --- |
| raw | 555.326283623 | NaN | NaN | sample standard deviation of gross_loss_per_lot with ddof=1 | 6582 |
| winsorized_1pct_99pct | 482.451536082 | -1504.42 | 1765.61 | sample standard deviation after clipping at empirical 1st/99th percentiles; ddof=1 | 6582 |

## ICC, Mean Cluster Size, and Design Effect

| cluster_scheme | icc | mean_cluster_size | design_effect | n_rows | n_clusters | fallback_rows | fallback_singleton_clusters | singleton_clusters_total | max_cluster_size | method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| traderKey | 0.16232845166 | 5.64010282776 | 1.75322070758 | 6582 | 1167 | 15 | 4 | 360 | 77 | one-way random-effects ANOVA ICC with singleton fallback for missing traderKey rows |
| ipClusterId | 0.0964717957713 | 7.37892376682 | 1.61538623087 | 6582 | 892 | 15 | 4 | 263 | 168 | one-way random-effects ANOVA ICC with singleton fallback for invalid ipClusterId rows |

## Campaign Throughput Inputs

- `mean_positions_per_campaign` = `506.307692308` from `n_campaigns=13`.
- `mean_active_accounts_per_campaign` = `162.846153846` from `n_campaigns=13`.
- `mean_positions_per_active_account` = `3.10911667454` from `n_campaign_account_pairs=2117`.

| campaignId | positions | active_accounts |
| --- | --- | --- |
| 53 | 519 | 160 |
| 54 | 509 | 172 |
| 55 | 485 | 140 |
| 56 | 524 | 166 |
| 57 | 511 | 138 |
| 58 | 438 | 141 |
| 59 | 552 | 195 |
| 60 | 481 | 176 |
| 61 | 564 | 176 |
| 62 | 409 | 158 |
| 63 | 584 | 160 |
| 64 | 496 | 163 |
| 65 | 510 | 172 |

## Required n Per Arm

- Formula: `n_per_arm = 2 * (z_(1-alpha/2) + z_(1-beta))^2 * sigma^2 / delta^2 * DEFF`.
- `alpha = 0.05`, `power = 0.80`, `z_(1-alpha/2) = 1.95996398454`, `z_(1-beta) = 0.841621233573`, `z_sum = 2.80158521811`.
- `campaign_waves_per_arm_from_positions = n_per_arm / mean_positions_per_campaign`.
- `campaign_waves_per_arm_from_active_accounts = (n_per_arm / mean_positions_per_active_account) / mean_active_accounts_per_campaign`.

| sigma_variant | cluster_scheme | delta_dollars_per_lot | n_per_arm_formula | n_per_arm_ceiling | required_active_accounts_per_arm | campaign_waves_per_arm_from_positions | campaign_waves_per_arm_from_active_accounts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw | traderKey | 10 | 84873.2279947 | 84874 | 27298.1804413 | 167.631717401 | 167.631717401 |
| raw | traderKey | 20 | 21218.3069987 | 21219 | 6824.54511033 | 41.9079293502 | 41.9079293502 |
| raw | traderKey | 40 | 5304.57674967 | 5305 | 1706.13627758 | 10.4769823375 | 10.4769823375 |
| raw | ipClusterId | 10 | 78200.6756365 | 78201 | 25152.0556552 | 154.452868927 | 154.452868927 |
| raw | ipClusterId | 20 | 19550.1689091 | 19551 | 6288.0139138 | 38.6132172317 | 38.6132172317 |
| raw | ipClusterId | 40 | 4887.54222728 | 4888 | 1572.00347845 | 9.65330430791 | 9.65330430791 |
| winsorized_1pct_99pct | traderKey | 10 | 64059.2203675 | 64060 | 20603.6720629 | 126.522313093 | 126.522313093 |
| winsorized_1pct_99pct | traderKey | 20 | 16014.8050919 | 16015 | 5150.91801572 | 31.6305782732 | 31.6305782732 |
| winsorized_1pct_99pct | traderKey | 40 | 4003.70127297 | 4004 | 1287.72950393 | 7.9076445683 | 7.9076445683 |
| winsorized_1pct_99pct | ipClusterId | 10 | 59023.0209436 | 59024 | 18983.8552625 | 116.5753984 | 116.5753984 |
| winsorized_1pct_99pct | ipClusterId | 20 | 14755.7552359 | 14756 | 4745.96381562 | 29.1438495999 | 29.1438495999 |
| winsorized_1pct_99pct | ipClusterId | 40 | 3688.93880898 | 3689 | 1186.49095391 | 7.28596239998 | 7.28596239998 |

## Supporting Stats

| quantity | value | method | n_basis |
| --- | --- | --- | --- |
| positions_per_active_account_mean | 3.10911667454 | mean of per-(campaignId, accountId) position counts | 2117 |
| positions_per_active_account_median | 2 | median of per-(campaignId, accountId) position counts | 2117 |
| positions_per_active_account_p90 | 7 | 90th percentile of per-(campaignId, accountId) position counts | 2117 |
| active_span_hours_mean | 3.37693644046 | mean of per-(campaignId, accountId) active span hours from first open to last close | 2117 |
| active_span_hours_median | 1.59333333333 | median of per-(campaignId, accountId) active span hours from first open to last close | 2117 |
| active_span_hours_p90 | 9.48105555556 | 90th percentile of per-(campaignId, accountId) active span hours from first open to last close | 2117 |
| near_4pct_drawdown_positions | 469 | count of positions with dd_from_peak_pct in [0.03, 0.05] | 6582 |
| near_4pct_drawdown_share | 0.0712549377089 | share of positions with dd_from_peak_pct in [0.03, 0.05] | 6582 |
| no_sl_position_count | 1569 | count of positions with has_sl == False | 6582 |
| no_sl_position_share | 0.23837739289 | share of positions with has_sl == False | 6582 |
| no_sl_abs_profit_share | 0.192845560532 | share of total absolute P&L contributed by positions with has_sl == False, using abs(profit) | 6582 |
| total_absolute_profit | 846943.22 | sum of abs(profit) across all primary-era positions | 6582 |
