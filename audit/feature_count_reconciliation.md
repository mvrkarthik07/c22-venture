# Stage 3 feature-count reconciliation

Date: 2026-08-24  
Scope: frozen `stage3-submission-2026-08-21` source and
`artifacts/stage3_v2.json`  
Read-only audit; no code, feature definition, or artifact was changed.

**VERDICT: STALE_DOCS**

The accurate reconciliation is: **(a) is true for the lineage, (b) describes
the deliberate implementation of the V2 selection, and (c) is false.** The
24-feature number is the screened admissible family. The frozen V2 model and
`predict()` use 20 raw features. The four omitted definitions remain in the
Stage 2 feature library, but are deliberately excluded from the final V2
design matrix by the hardcoded `V2_FEATURES` list.

## Artifact versus `predict()` matrix

The artifact was read directly. It contains:

| Item | Count |
|---|---:|
| Artifact raw `feature_names` | 20 |
| `stage3_model.V2_FEATURES` | 20 |
| Fitted Ridge coefficients | 21 |
| Artifact `preprocessing.transformed_feature_names` | 21 |
| Columns in the matrix built by `_transform()` | 21 |

The coefficient count is 21, not 20, because the 20 raw features include
categorical `challenge_type`. The 19 numeric features produce 19 standardized
columns, and `challenge_type` produces two one-hot columns:
`cat__challenge_type=11` and `cat__challenge_type=unknown`.

The artifact raw names and `V2_FEATURES` match exactly, both in membership and
position, at all 20 positions. There are no raw columns present in one list and
absent from the other.

The transformed matrix and artifact names also match exactly at every position:

| Position | Matrix column constructed by `predict()` | Artifact transformed name | Match |
|---:|---|---|---|
| 1 | `num__loss_streak` | `num__loss_streak` | yes |
| 2 | `num__win_streak` | `num__win_streak` | yes |
| 3 | `num__pnl_ewm` | `num__pnl_ewm` | yes |
| 4 | `num__lot_zscore` | `num__lot_zscore` | yes |
| 5 | `num__amount` | `num__amount` | yes |
| 6 | `num__size_after_loss_delta` | `num__size_after_loss_delta` | yes |
| 7 | `num__sl_usage_rate_5` | `num__sl_usage_rate_5` | yes |
| 8 | `num__manual_exit_rate_5` | `num__manual_exit_rate_5` | yes |
| 9 | `num__pnl_pct` | `num__pnl_pct` | yes |
| 10 | `num__dd_from_peak_pct` | `num__dd_from_peak_pct` | yes |
| 11 | `num__trade_index` | `num__trade_index` | yes |
| 12 | `num__log_dt_close` | `num__log_dt_close` | yes |
| 13 | `num__trades_per_hour` | `num__trades_per_hour` | yes |
| 14 | `num__prior_campaigns_x_loss_streak_ge_2` | `num__prior_campaigns_x_loss_streak_ge_2` | yes |
| 15 | `num__shared_ip` | `num__shared_ip` | yes |
| 16 | `num__ip_cluster_size` | `num__ip_cluster_size` | yes |
| 17 | `num__gold_vol_prev_day` | `num__gold_vol_prev_day` | yes |
| 18 | `num__same_direction_reentry` | `num__same_direction_reentry` | yes |
| 19 | `num__size_delta_ratio` | `num__size_delta_ratio` | yes |
| 20 | `cat__challenge_type=11` | `cat__challenge_type=11` | yes |
| 21 | `cat__challenge_type=unknown` | `cat__challenge_type=unknown` | yes |

The construction is the same in fit and prediction: `_fit_transform_parameters()`
appends numeric columns in `_NUMERIC_FEATURES` order, then categorical columns
in sorted category order (`stage3_model.py:165-207`), while `_transform()` uses
the artifact's stored category order (`stage3_model.py:210-223`). Fitting calls
Ridge on that matrix (`stage3_model.py:235-249`), and prediction multiplies the
same 21-column transform by the 21 coefficients (`stage3_model.py:252-255`).

Therefore there is no fit/predict column-count or column-order mismatch, and no
column is present in one final matrix but not the other.

## Where the 24 became 20

The 24-set comes from the 28-feature Stage 2 frozen list after removing the
four SL/TP-contaminated fields. The audit trail explicitly describes that
24-feature admissible family (`reports/trials_log_and_power.md:12-16` and
`reports/common_split_viability.md:174-180`).

The Stage 3 comparison then explicitly records that V2 drops four history
fields and retains the interaction, producing 20 inputs
(`reports/trials_log_and_power.md:410-416`). The V2 freeze recommendation
repeats that choice (`reports/trials_log_and_power.md:545-552`).

The four fields in the 24-set but absent from the final 20-set are:

| Feature | Definition exists in | Final drop point | Failure mode |
|---|---|---|---|
| `prior_campaigns` | `build_features.FEATURE_COLUMNS`; `TraderState._resolve_prior_campaigns()` | Omitted from `stage3_model.V2_FEATURES` (`stage3_model.py:34-55`) during the explicit V2 history-field selection | Deliberate selection, then hardcoded omission; no silent failure or swallowed exception |
| `trader_prior_tilt` | `build_features.FEATURE_COLUMNS`; `TraderHistory.compute_features()`; Stage 2 row builder | Omitted from `stage3_model.V2_FEATURES` during the same explicit V2 history-field selection | Deliberate selection, then hardcoded omission; no silent failure or swallowed exception |
| `trader_prior_sl_discipline` | `build_features.FEATURE_COLUMNS`; `TraderHistory.compute_features()`; Stage 2 row builder | Omitted from `stage3_model.V2_FEATURES` during the same explicit V2 history-field selection | Deliberate selection, then hardcoded omission; no silent failure or swallowed exception |
| `trader_prior_survival` | `build_features.FEATURE_COLUMNS`; `TraderHistory.compute_features()`; Stage 2 row builder | Omitted from `stage3_model.V2_FEATURES` during the same explicit V2 history-field selection | Deliberate selection, then hardcoded omission; no silent failure or swallowed exception |

The Stage 2 builder still defines and can export these fields
(`build_features.py:30-59`; `features.py:19-77`; `build_features.py:280-430`),
but the final Stage 3 path requires only `campaignId`, `accountId`,
`openDateTime`, and `amount` as mandatory runtime inputs and constructs only
the V2 list (`stage3_model.py:468-499`). No exception or fallback removes the
four fields at runtime.

## Tests that would catch case (c)

No test explicitly asserts the complete invariant
`len(coefficients) == len(transformed_feature_names)` and compares every
transformed name with independently reconstructed matrix order. However, the
existing tests would catch the specific 24-column-versus-20-column failure in
these ways:

- `test_frozen_artifact_and_unseen_trader_are_deterministic`
  (`tests/test_stage3_model.py:56-70`) calls `_load_artifact()`, which rejects
  artifact raw names that do not exactly equal `V2_FEATURES`, and then calls
  `predict()`, which would fail the matrix multiplication if the coefficient
  vector had the wrong length.
- `test_predict_smoke_arbitrary_campaign_unseen_trader_and_nan_features`
  (`tests/test_stage3_model.py:73-82`) calls `predict()` and would likewise
  expose a transformed-matrix/coefficient dimension error.
- `test_recompute_after_truncation_is_byte_identical_for_200_positions` and
  `test_forbidden_input_columns_do_not_reach_entry_features` load the artifact
  and would catch a raw artifact feature-name mismatch, but they do not score
  rows and therefore would not independently catch a coefficient-length error
  if raw names still matched.

No existing test specifically checks transformed-column names and order against
the artifact metadata. Such a same-width semantic permutation could therefore
pass the current tests, but the actual frozen artifact has an exact 21/21
position-by-position match.

## 6. Source of the extra transformed column

The artifact's 21 transformed columns, in exact order, are:

| Position | Transformed column |
|---:|---|
| 1 | `num__loss_streak` |
| 2 | `num__win_streak` |
| 3 | `num__pnl_ewm` |
| 4 | `num__lot_zscore` |
| 5 | `num__amount` |
| 6 | `num__size_after_loss_delta` |
| 7 | `num__sl_usage_rate_5` |
| 8 | `num__manual_exit_rate_5` |
| 9 | `num__pnl_pct` |
| 10 | `num__dd_from_peak_pct` |
| 11 | `num__trade_index` |
| 12 | `num__log_dt_close` |
| 13 | `num__trades_per_hour` |
| 14 | `num__prior_campaigns_x_loss_streak_ge_2` |
| 15 | `num__shared_ip` |
| 16 | `num__ip_cluster_size` |
| 17 | `num__gold_vol_prev_day` |
| 18 | `num__same_direction_reentry` |
| 19 | `num__size_delta_ratio` |
| 20 | `cat__challenge_type=11` |
| 21 | `cat__challenge_type=unknown` |

The raw feature `challenge_type` expands into two columns. The mechanism is
manual one-hot/dummy encoding: numeric features are standardized one-for-one,
then one binary column is appended for each fitted categorical level
(`stage3_model.py:171-191`). It is not an intercept, basis expansion, binning,
or interaction. The intercept remains the separate Ridge intercept used in the
score calculation (`stage3_model.py:252-255`).

The encoder was fit on these exact `challenge_type` levels, stored in the
artifact in sorted order:

```text
11
unknown
```

The runtime behavior is implemented by `_canonical_category()` and the
categorical loop in `_transform()` (`stage3_model.py:104-112`,
`stage3_model.py:219-223`):

- An **unseen non-missing level** is converted to its string representation but
  is not added to the fitted level list. It therefore sets both fitted dummy
  columns to `0`; prediction does not raise an exception.
- A **missing value** is canonicalized to the fitted level `unknown`, so it
  sets `cat__challenge_type=unknown` to `1` and the `11` dummy to `0`.
- Missingness is encoded **in effect as the `unknown` level**, because
  `unknown` is present in the fitted categories. There is no separate boolean
  missingness indicator. If a new dataset contains no missing/`unknown` rows,
  the `cat__challenge_type=unknown` column remains in the matrix but is all
  zeros.

The fitted coefficients for the two categorical columns are:

| Transformed column | Coefficient | Absolute coefficient |
|---|---:|---:|
| `cat__challenge_type=11` | `1.88788160294` | `1.88788160294` |
| `cat__challenge_type=unknown` | `-1.88788160294` | `1.88788160294` |

Taking `cat__challenge_type=unknown` as the additional column relative to the
20 raw-feature count, its fitted coefficient is **`-1.88788160294`**. Its
absolute magnitude is tied for **5th rank among 21 coefficients** (the other
5th-ranked coefficient is `cat__challenge_type=11`; the ranking is by absolute
magnitude using competition ranking).
