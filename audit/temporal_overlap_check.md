# Temporal overlap audit: `sl_usage_rate_5` and `manual_exit_rate_5`

## Verdict

**OVERLAP: 63.34%**

The overlap rate is the same for both features because both use the same
account/campaign lookback deque. It is 1,529 of 2,414 currently computed
values in the full position dataset. This is a temporal-overlap finding, not a
claim that the current trade's own close value is read before prediction.

## Audit definition and source path

- The frozen code computes both fields at entry time only after at least three
  prior state updates: `features.py:329-359`.
- The state deques retain the most recent five prior updates. The current row
  is appended only after feature computation and decision preparation:
  `stage3_model.py:497-515`; the two deque updates are
  `features.py:457-459`.
- I reconstructed the exact deque in the loaded raw-position stream. The
  reconstruction matched both current feature columns exactly: maximum
  absolute difference `0.0` across `n=2,414` non-missing values per feature.
- “Computed” below means the current feature is non-missing. Thus the first
  computed values can have 3 or 4 lookback rows; later values have 5. The
  overlap count is the number of those rows with
  `closeDateTime > current openDateTime`, from 0 through 5.

## Overlap distributions

Counts are counts of computed values; percentages in the last column use that
row's computed-value `n` as denominator.

| feature | scope | computed n | overlap 0 | overlap 1 | overlap 2 | overlap 3 | overlap 4 | overlap 5 | overlap >=1 | overlap >=1 % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sl_usage_rate_5` | full dataset | 2,414 | 885 | 723 | 432 | 239 | 111 | 24 | 1,529 | 63.34% |
| `manual_exit_rate_5` | full dataset | 2,414 | 885 | 723 | 432 | 239 | 111 | 24 | 1,529 | 63.34% |
| `sl_usage_rate_5` | training <=C52 | 9 | 1 | 1 | 3 | 4 | 0 | 0 | 8 | 88.89% |
| `manual_exit_rate_5` | training <=C52 | 9 | 1 | 1 | 3 | 4 | 0 | 0 | 8 | 88.89% |
| `sl_usage_rate_5` | eval C53-C66 | 2,405 | 884 | 722 | 429 | 235 | 111 | 24 | 1,521 | 63.24% |
| `manual_exit_rate_5` | eval C53-C66 | 2,405 | 884 | 722 | 429 | 235 | 111 | 24 | 1,521 | 63.24% |
| `sl_usage_rate_5` | frozen V2 177 acted trades | 123 | 34 | 38 | 30 | 16 | 4 | 1 | 89 | 72.36% |
| `manual_exit_rate_5` | frozen V2 177 acted trades | 123 | 34 | 38 | 30 | 16 | 4 | 1 | 89 | 72.36% |

The 177 acted-trade row has `n=123` because 54 of the 177 acted trades do not
yet have the minimum three prior state updates required for either rolling
feature.

## Timestamp and schema checks

The timestamps used were:

- current entry: position-level `openDateTime`;
- prior close: position-level `closeDateTime`.

The raw schema requires both fields (`pipeline.py:52-57`). The raw loader parses
both directly from the source columns (`pipeline.py:153-157`). At position
collapse, `openDateTime` is the first raw fill timestamp and `closeDateTime` is
the maximum raw fill `closeDateTime` (`pipeline.py:247-265`). The code then
derives `durationSec` from those two timestamps (`pipeline.py:271`); it does not
backfill `closeDateTime` from duration or another feature. In this run,
`closeDateTime` was non-missing for all `n=7,277` collapsed positions, and no
timestamp values were imputed by the audit.

The strict comparison used only prior rows satisfying the strict inequality
`closeDateTime < current openDateTime`; equal timestamps were excluded.

## Account scope and stability

The lookback state key is exactly `(campaignId, accountId)` in
`stage3_model.py:476-485`. Therefore the rolling features are account-scoped
within a campaign and cannot carry a rolling deque from one campaign into
another. The raw `accountId` field is reused across campaigns in this data:
`492` of `499` distinct account-key values occur in more than one campaign,
with a maximum of `12` campaigns for one key. Consequently, `accountId` is
repeatable across campaigns in the input, but the feature state key is
campaign-scoped rather than a globally continuous account history.

All `n=7,277` rows had a non-missing account key, so the row-specific fallback
key in `stage3_model.py:484` was not used in this audit.

## Strict close-before-entry recomputation

The strict variant filtered each account/campaign's prior history to
`closeDateTime < current openDateTime`, then retained the most recent five
eligible rows and applied the same minimum-three-row rule. `exit_type` and
`slPrice` definitions were otherwise unchanged.

| feature | scope | current computed n | strict computed n | paired n | Pearson | Spearman | paired values changed n (%) | current values with strict value unavailable |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `sl_usage_rate_5` | full dataset | 2,414 | 1,896 | 1,896 | 0.946153 | 0.955943 | 386 (20.36%) | 518 (21.46%) |
| `manual_exit_rate_5` | full dataset | 2,414 | 1,896 | 1,896 | 0.904371 | 0.896587 | 576 (30.38%) | 518 (21.46%) |
| `sl_usage_rate_5` | eval C53-C66 | 2,405 | 1,895 | 1,895 | 0.946133 | 0.955920 | 386 (20.37%) | 510 (21.21%) |
| `manual_exit_rate_5` | eval C53-C66 | 2,405 | 1,895 | 1,895 | 0.904371 | 0.896589 | 576 (30.40%) | 510 (21.21%) |
| `sl_usage_rate_5` | frozen V2 177 acted trades | 123 | 79 | 79 | 0.935752 | 0.904354 | 13 (16.46%) | 44 (35.77%) |
| `manual_exit_rate_5` | frozen V2 177 acted trades | 123 | 79 | 79 | 0.930901 | 0.937900 | 25 (31.65%) | 44 (35.77%) |

“Paired values changed” compares only rows where both current and strict
values exist. If a strict-unavailable value is conservatively also counted as
a change, the full-dataset rates are `904/2,414 = 37.45%` for
`sl_usage_rate_5` and `1,094/2,414 = 45.32%` for `manual_exit_rate_5`.

## Conclusion

The frozen implementation computes the rates from prior state updates, but a
majority of computed windows include at least one prior position that was still
open at the current position's entry: `1,529/2,414 = 63.34%` in the full
dataset and `89/123 = 72.36%` among the feature-computed rows in the 177 acted
set. Under the requested close-before-entry definition, the verdict is:

**OVERLAP: 63.34%**
