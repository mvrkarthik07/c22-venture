# `challenge_type` deconfounding diagnostic

Date: 2026-08-24  
Comparison: frozen V2 versus the branch-only no-`challenge_type` ablation  
Position key: `(campaignId, accountId, positionId)`  
Primary window: C53–C65, `n=6,582`; C66 excluded from primary dollar totals

The frozen V2 acted set has `n=177`; the ablation acted set has `n=188`.
All comparisons below use the identical collapsed-position stream and the
frozen V2/ablation decisions already generated from their respective artifacts.

## Part 1 — acted-set overlap

| group | n | mean reverseProfit/lot | total lots | dollar total |
|---|---:|---:|---:|---:|
| V2 ∩ ablation | 176 | 9.8077 | 104.90 | -$3,578.49 |
| V2 only | 1 | 120.4444 | 0.18 | +$21.68 |
| ablation only | 12 | -157.5378 | 9.29 | -$382.24 |

The sets are **not nested**: one V2-only trade is replaced by 12
ablation-only trades. Equivalently, `|177 ∩ 188|=176`, V2-only `n=1`, and
ablation-only `n=12`.

### Campaign distribution

| group | campaign distribution |
|---|---|
| V2 ∩ ablation (`n=176`) | C53: 4; C54: 14; C55: 14; C56: 10; C57: 9; C58: 17; C59: 21; C60: 10; C61: 26; C62: 11; C63: 14; C64: 14; C65: 12 |
| V2 only (`n=1`) | C53: 1 |
| ablation only (`n=12`) | C58: 1; C60: 1; C61: 2; C63: 2; C64: 2; C65: 4 |

### Challenge-type distribution

| group | level 11 | unknown |
|---|---:|---:|
| V2 ∩ ablation (`n=176`) | 63 | 113 |
| V2 only (`n=1`) | 1 | 0 |
| ablation only (`n=12`) | 0 | 12 |

The coverage change is therefore not a random enlargement of the same set:
the sole V2-only trade is level 11, while every ablation-only trade is
unknown.

## Part 2 — fixed-acted-set counterfactual

The original 177 V2-acted rows were held fixed. The two challenge-type column
contributions were set to zero in the score, without refitting, reselecting,
reapplying the hurdle, or changing the acted mask. Because EW/lot and SW/lot
are realized outcome metrics of the fixed rows, zeroing a score contribution
cannot change either realized metric.

| fixed acted set | n | EW/lot | SW/lot |
|---|---:|---:|---:|
| Original V2 rows | 177 | 10.4327 | -33.8486 |
| Challenge contribution set to zero | 177 | 10.4327 | -33.8486 |
| Delta | 0 | 0.0000 | 0.0000 |

Delta versus the frozen `+10.4327` EW/lot is **`0.0000`/lot**. The
account-clustered 95% CI on the delta itself is **[0.0000, 0.0000]**: every
trade-level realized EW difference is exactly zero, so trader-cluster
resampling remains degenerate at zero. The same fixed-set result holds for
SW/lot.

This is the clean fixed-coverage number requested; it is necessarily zero for
realized P&L. Any nonzero realized performance change requires changing which
rows are acted on, which is the coverage/set effect measured in Part 1.

## Part 3 — level decomposition within the current 177

The acted-set coverage share is calculated against `n=177`. The account
cluster is `traderKey`, with the existing campaign-account fallback when the
key is missing. CIs use the pinned trader-cluster bootstrap (`n_boot=2,000`,
seed `7`).

| level | n | acted-set share | EW/lot | account 95% CI for EW | SW/lot | dollar contribution |
|---|---:|---:|---:|---|---:|---:|
| 11 | 64 | 36.1582% | 11.8999 | [-71.5218, 78.7884] | -10.8250 | -$410.16 |
| unknown | 113 | 63.8418% | 9.6018 | [-70.0267, 95.1443] | -46.8321 | -$3,146.65 |
| Total | 177 | 100.0000% | 10.4327 | [-51.0655, 71.3163] | -33.8486 | -$3,556.81 |

The equal-weighted aggregate decomposes as:

- Level 11 contributes `+4.3028`/lot to the aggregate and **41.2431%** of
  `+10.4327`.
- Unknown contributes `+6.1300`/lot to the aggregate and **58.7569%** of
  `+10.4327`.

Campaign distribution within each level:

| level | campaign distribution |
|---|---|
| 11 (`n=64`) | C53: 5; C54: 14; C55: 14; C56: 10; C59: 21 |
| unknown (`n=113`) | C57: 9; C58: 17; C60: 10; C61: 26; C62: 11; C63: 14; C64: 14; C65: 12 |

### Base rates versus acted rates

The requested evaluation base rate uses C53–C66, `n=6,583`; the 177-row acted
set is C53–C65 and therefore excludes C66.

| population | n | level 11 n | level 11 rate | unknown n | unknown rate |
|---|---:|---:|---:|---:|---:|
| Evaluation C53–C66 | 6,583 | 2,589 | 39.3286% | 3,994 | 60.6714% |
| V2 acted C53–C65 | 177 | 64 | 36.1582% | 113 | 63.8418% |

The acted set is therefore slightly more unknown-heavy than the full
evaluation base rate: `63.8418%` versus `60.6714%`.

## Part 4 — clustered CIs for the ablation result

These are account-clustered 95% CIs using the same `n_boot=2,000`, seed `7`
procedure. V2 uses `n=177`; the ablation uses `n=188`.

| model | n | EW/lot | account 95% CI for EW | SW/lot | account 95% CI for SW |
|---|---:|---:|---|---:|---|
| Frozen V2 | 177 | 10.4327 | [-51.0655, 71.3163] | -33.8486 | [-74.3385, -0.7109] |
| No `challenge_type` ablation | 188 | -0.8740 | [-53.4451, 48.8400] | -34.6854 | [-73.1850, -2.6308] |

The EW intervals **overlap**: the overlap is approximately
`[-51.0655, 48.8400]`. The SW intervals also **overlap**: the overlap is
approximately `[-73.1850, -2.6308]`. The point-estimate EW sign flip is thus
not accompanied by separated account-clustered 95% intervals.
