# Account-clustered bootstrap recomputation

Date: 2026-08-25.  The frozen artifact was not refit and no fitted value was
changed.

## Contract and causal checks

- Tests: 28 passed in 4.59s pytest time (4.83s wall time); baseline was 20 in 8.78s (9.41s wall time). The measured suite increase was 0s, and the final runtime is below the 15s limit.
- Part B sample: state size 64 rows, fixed seed 7, full position state size 7,277. Every sampled feature was bit-identical; mismatches=0.
- `artifacts/stage3_v2.json` SHA-256 before: `7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b`.
- `artifacts/stage3_v2.json` SHA-256 after: `7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b`.
- The new sidecar is `artifacts/stage3_v2_transformed_columns.json`, SHA-256 `1facf8f320490689aa2b42590dbf47a7ff04246d9f28f55bc9a5d87b1cd07bb6`.

## Clustering unit

Before this change, `_cluster_bootstrap(..., "account")` actually clustered by
`traderKey`, falling back to `campaignId::accountId`; it did not use the
account key itself. That implementation remains available as
`cluster_kind="traderKey"` for the before column below.

The new default `cluster_kind="account"` uses `accountId` and resamples the
selected accounts with replacement, retaining all selected trades belonging to
each sampled account. The seed remains 7 and the bootstrap count remains
2,000. Missing account IDs use deterministic campaign-qualified singleton
fallbacks.

For the acted-set interval, the common split is C53-C65: 177 acted trades and
C66 is excluded. The full-evaluation diagnostics are C53-C66, n=6,583;
C66 is retained for coverage and per-lot diagnostics but excluded from dollar
totals.

| set | trades | distinct accounts | trades/account min | median | max |
|---|---:|---:|---:|---:|---:|
| V2 acted, C53-C65 | 177 | 92 | 1 | 1 | 8 |
| Full eval, C53-C66 | 6,583 | 496 | 1 | 11 | 63 |

## Common-split EW and SW results

`EW/lot` is the arithmetic mean of realized `reverseProfit/lot`.
`SW/lot` is total realized reverseProfit divided by total lots. Intervals are
95% account-clustered bootstrap intervals. The before values reproduce the
frozen report's traderKey-based implementation; the after values use accountId.

| metric / set | n | point | before 95% CI (traderKey) | after 95% CI (accountId) |
|---|---:|---:|---|---|
| EW, model acted, C53-C65 | 177 | 10.433 | [-52.786, 72.331] | [-46.117, 66.826] |
| SW, model acted, C53-C65 | 177 | -33.849 | [-74.360, 1.166] | [-70.260, 2.964] |
| EW, model no overrides, C53-C65 | 183 | 10.452 | [-49.773, 70.475] | [-43.125, 64.704] |
| SW, model no overrides, C53-C65 | 183 | -32.650 | [-71.655, 1.931] | [-66.794, 3.269] |
| EW, fade everything, C53-C65 | 6,582 | 5.436 | [-9.339, 20.713] | [-8.572, 20.475] |
| SW, fade everything, C53-C65 | 6,582 | -3.001 | [-11.031, 5.381] | [-10.493, 4.840] |
| EW, model acted, C53-C66 | 178 | 10.325 | [-52.204, 72.290] | [-42.819, 68.866] |
| EW, fade everything, C53-C66 | 6,583 | 5.434 | [-9.067, 20.254] | [-8.572, 20.466] |
| SW, fade everything, C53-C66 | 6,583 | -3.587 | [-10.681, 4.427] | [-10.336, 3.734] |

The accountId intervals did not widen for these rows; they changed according to
the observed account-level grouping. No interval or seed was tuned.

### Interval-label correction

The earlier EW interval reported as `[-51.0655, 71.3163]` in
`audit/challenge_type_deconfound.md` was not trade-level. Its resampling unit
was the legacy `traderKey` cluster, with `campaignId::accountId` as the
fallback when `traderKey` was missing. It should therefore be read as
**traderKey-clustered**, not accountId-clustered and not trade-level. The
direct trade-level comparator for the same 177 acted trades is
`[-50.682, 74.119]`; the accountId result is `[-46.117, 66.826]`.

## Training MDE recomputation

The prior training range was $65-$78/lot (winsorized/raw, traderKey-based).
Using the same primary-era sigma inputs (raw 555.326284, winsorized
482.451536), n=694, and accountId clusters gives:

| clustering | distinct clusters | mean trades/cluster | ICC | DEFF | raw MDE | winsorized MDE |
|---|---:|---:|---:|---:|---:|---:|
| Before: published traderKey planning estimate | — | — | 0.162328 | 1.753221 | $78.20/lot | $67.94/lot |
| After: accountId | 330 | 2.103 | 0.061587 | 1.067932 | $61.03/lot | $53.02/lot |

The MDE computation is `2.801585 * sigma * sqrt(DEFF / n)`, with n=694 and
the same raw and 1%/99% winsorized outcome dispersions used by the existing
report. The account-level recomputed range is $53.02-$61.03/lot.

## Before/after intervals for the Stage 3 backtest submission

The following tables cover each distinct account-CI row in
`reports/stage3_backtest.md`; duplicated C53-C65/C53-C66 sections in that file
have identical values and are shown once. Cluster diagnostics for the common
acted and full-evaluation intervals are the n/account/min/median/max values
above; all rows use the same fixed-seed 2,000-resample method.

### Per-campaign acted rows

| campaign | n | before 95% CI | after 95% CI |
|---:|---:|---|---|
| C53 | 5 | [48.512, 510.000] | [62.119, 411.750] |
| C54 | 14 | [-71.219, 195.638] | [-67.989, 195.326] |
| C55 | 14 | [-375.126, 126.609] | [-347.710, 109.515] |
| C56 | 10 | [-111.370, 446.548] | [-90.793, 411.359] |
| C57 | 9 | [-220.217, 224.867] | [-207.456, 198.640] |
| C58 | 17 | [-256.267, 222.994] | [-247.919, 199.595] |
| C59 | 21 | [-221.813, -8.205] | [-212.512, -13.058] |
| C60 | 10 | [-294.341, 325.622] | [-265.068, 241.071] |
| C61 | 26 | [-138.010, 66.643] | [-127.849, 64.762] |
| C62 | 11 | [-99.998, 199.999] | [-89.949, 185.426] |
| C63 | 14 | [-296.714, 70.673] | [-285.042, 69.215] |
| C64 | 14 | [-89.265, 358.417] | [-85.793, 363.677] |
| C65 | 12 | [-66.447, 460.256] | [-55.792, 421.499] |
| Best campaign removed (C53) | 172 | [-60.200, 66.313] | [-51.592, 64.648] |

### Walk-forward and frontier rows

| row | n | before 95% CI | after 95% CI |
|---|---:|---|---|
| Track A fold 1 | 15 | [-19.601, 350.132] | [-2.432, 310.429] |
| Track A fold 2 | 8 | [-281.500, 0.371] | [-264.933, -7.412] |
| Track A fold 3 | 83 | [-134.196, 107.650] | [-140.406, 99.540] |
| Track A fold 4 | 8 | [-25.931, 552.238] | [9.211, 517.229] |
| Track A pooled | 114 | [-80.926, 111.031] | [-78.912, 101.596] |
| Track A pooled fade everything EW | 2,190 | [-3.458, 44.978] | [-2.682, 45.611] |
| Track A pooled fade everything SW | 2,190 | [-4.582, 21.592] | [-5.155, 22.207] |
| Track B fold 1 | 53 | [-73.662, 188.866] | [-65.227, 177.417] |
| Track B fold 2 | 19 | [-479.776, -43.912] | [-463.728, -48.091] |
| Track B fold 3 | 157 | [-75.667, 120.751] | [-68.188, 117.507] |
| Track B fold 4 | 8 | [-24.205, 554.967] | [9.211, 517.229] |
| Track B pooled | 237 | [-52.517, 95.979] | [-48.527, 95.039] |
| Track B pooled fade everything EW | 4,545 | [-5.507, 29.821] | [-5.461, 28.914] |
| Track B pooled fade everything SW | 4,545 | [-9.216, 9.239] | [-9.291, 9.404] |
| Frontier 1.0% | 66 | [-116.231, 110.628] | [-101.450, 98.007] |
| Frontier 2.7% | 178 | [-52.204, 72.290] | [-42.819, 68.866] |
| Frontier 5.0% | 329 | [-27.046, 75.815] | [-24.985, 72.987] |
| Frontier 10.0% | 658 | [-21.420, 66.439] | [-21.369, 64.464] |
| Frontier 25.0% | 1,646 | [-0.608, 62.686] | [1.881, 61.557] |
| Frontier 50.0% | 3,292 | [-0.196, 43.667] | [1.432, 42.573] |
| Frontier 100.0% | 5,616 | [-2.928, 29.412] | [-1.788, 28.408] |

### In-sample/evaluation rows

| row | n | before 95% CI | after 95% CI |
|---|---:|---|---|
| Training C33-C52 | 4 | [-62.924, 193.331] | [-37.213, 142.123] |
| Evaluation C53-C66 | 178 | [-52.204, 72.290] | [-42.819, 68.866] |

All dollar totals remain calculated from realized `actual_absolute_rp`; the
bootstrap changes only uncertainty intervals. C66 remains excluded from every
dollar total by `_common_split_economic()` in `stage3_model.py`.
