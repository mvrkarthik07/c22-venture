# Corrected power and C66 coverage recomputation

Date: 2026-08-26  
Branch: `stage3-submission`  
Scope: frozen V2 results, existing Stage 2 pooled effects, corrected accountId
clustering, and a reporting-only C66 restatement. No refit, re-selection,
artifact modification, estimator change, alpha change, hurdle change, or
override change was performed.

## Method and criterion

The published “above the MDE” comparison used the point estimate of each of the
48 pooled Stage 2 feature-track effects against the training detection floor.
The same point-estimate criterion is retained here. A 95% CI is reported for
each effect, but “detectable” below means **point estimate greater than the
corrected lower floor, $53.02/lot**, matching the original comparison rather
than requiring the CI lower endpoint to exceed zero.

The corrected accountId training MDE is:

| sigma convention | n | accountId DEFF | MDE |
|---|---:|---:|---:|
| winsorized | 694 | 1.067932 | **$53.02/lot** |
| raw | 694 | 1.067932 | **$61.03/lot** |

The effect CIs below use 2,000 accountId-clustered bootstrap replicates, seed 7.

## 1. Effects above the corrected floor

The old count was 1/48 at the published traderKey-clustered winsorized floor.
At the corrected lower accountId floor of $53.02/lot, the count is:

**3 of 48 point estimates exceed $53.02/lot.**

| effect | track | n | point estimate | accountId-clustered 95% CI | point > $53.02? |
|---|---|---:|---:|---|---|
| `manual_exit_rate_5` | Track A | 121 | 64.912/lot | [2.272, 126.836] | Yes |
| `ip_cluster_size` | Track A | 369 | 67.775/lot | [3.919, 144.992] | Yes |
| `trader_prior_survival` | Track A | 373 | 70.630/lot | [-1.069, 147.010] | Yes |

The other 45 of 48 point estimates are at or below $53.02/lot. The three rows
are not three new model discoveries: `manual_exit_rate_5` is subsequently
flagged contaminated by the close-time audit, and `trader_prior_survival` was
not in the final 20-feature V2 artifact. Only `ip_cluster_size` is both in the
final V2 raw feature list and classified clean in the later rolling sweep.

## 2. Seven coverage levels at the corrected floor

Coverage is restated with C66 excluded from both numerator and denominator, so
the evaluation denominator is `n=6,582`. The seven rows use the frozen V2
scores and overrides; only the evaluation mask and reporting denominator are
changed. Each row's raw-sigma accountId MDE uses that row's observed account
DEFF; the winsorized MDE is shown for reference. Values below one are retained
as observed rather than silently replacing the reported DEFF with one.

| target | n acted | achieved coverage | EW/lot | accountId 95% CI | account DEFF | raw MDE | winsorized MDE | clears raw MDE? |
|---:|---:|---:|---:|---|---:|---:|---:|---|
| 1% | 66 | 1.0027% | 2.279 | [-98.883, 104.666] | 0.530410 | 191.50 | 166.37 | No |
| 2.7% | 177 | 2.6892% | 10.433 | [-46.117, 66.826] | 0.667024 | 116.94 | 101.59 | No |
| 5% | 329 | 4.9985% | 23.284 | [-26.719, 77.101] | 1.024895 | 86.83 | 75.44 | No |
| 10% | 658 | 9.9970% | 22.124 | [-20.761, 65.533] | 1.207979 | 66.66 | 57.91 | No |
| 25% | 1,646 | 25.0076% | 32.118 | [2.645, 61.985] | 1.001039 | 38.37 | 33.33 | No |
| 50% | 3,291 | 50.0000% | 21.675 | [1.432, 42.573] | 1.021744 | 27.41 | 23.82 | No |
| 100% target | 5,615 | 85.3084% | 13.139 | [-1.788, 28.422] | 1.241052 | 23.13 | 20.09 | No |

**Result: 0 of 7 coverage levels clear their own corrected raw MDE.** No
coverage level is listed as a clearance because none does so. The 25% row is
the closest on the raw-MDE comparison: `32.118/38.37 = 0.837`.

## 3. Restated observed-effect comparison

The prior statement was “training MDE $65–78/lot against observed effects of
$41–70/lot.” Under accountId clustering it is:

> **Training MDE $53.02–$61.03/lot; the observed pooled feature-track effects range from approximately −$211 to +$70.630/lot, and 3 of 48 point estimates exceed the corrected lower floor of $53.02/lot.**

The three exceeding effects are the rows listed in Section 1. The original
“$41–70” wording was a rounded description of the positive observed-effect
range; it is not the minimum across all 48 signed effects.

## 4. Corrected MDE for the IS EW estimate

The V2 IS EW estimate is `n=4`, point `50.8966/lot`, with accountId-clustered
95% CI `[-37.2130, 142.1230]`. Its training-window MDE is based on `n=694`
training rows:

```text
accountId winsorized MDE = $53.02/lot
accountId raw MDE        = $61.03/lot
```

The IS point estimate `50.8966/lot` clears neither floor: it is `$2.1234`
below the winsorized floor and `$10.1334` below the raw floor. Training is the
selection window, so this IS estimate remains optimistically biased by
construction; no correction for that bias is applied.

## 5. `trader_prior_survival`: field-class audit

`trader_prior_survival` is **CONTAMINATED** under the field-class-aware causal
rebuild. Its consumed prior-trade fields are:

| consumed column | field class | use |
|---|---|---|
| `openDateTime` (`first_open`) | OPEN-TIME | first prior open in the history span |
| `closeDateTime` (`last_close`) | CLOSE-TIME | last prior close in the history span |
| `traderKey` / fallback history key | OPEN-TIME metadata key | groups prior trades into the history entity |
| `campaignId` | OPEN-TIME metadata | groups prior campaign history |

The feature is the mean active span over prior campaigns, calculated from
`last_close - first_open`; therefore the `closeDateTime` consumption is the
contaminating field. The field-class-aware rebuild classifies the feature as
contaminated even though its reported original point estimate was positive.

## 6. Why `trader_prior_survival` is absent from V2

The selection record states:

> “V2 drops the four history fields (`prior_campaigns` plus the three
> `trader_prior_*` columns) but retains the interaction
> `prior_campaigns_x_loss_streak_ge_2` (20 inputs).”

This was a **set-level parsimony selection**, not a per-feature detection
threshold. The selection record states: “V2 is preferred on parsimony rather
than on a claim that its point estimate is proven better.” The stated criterion
was overlapping history-bearing V1/V2 intervals and no history-specific
advantage. The relevant V1 standardized coefficient for
`trader_prior_survival` was `-0.5473` (absolute value `0.5473`); the
history-bearing subset comparison was V1 `n=182`, EW `-2.579/lot`, CI
`[-62.526, 62.035]`, versus V2 `n=155`, EW `10.031/lot`, CI
`[-52.813, 78.831]`.

Thus the drop was criterion-driven at the **feature-set** level and represented
as a hardcoded omission in the final V2 feature list. It was not a silent
failure, swallowed exception, or a separate `trader_prior_survival` cutoff.
The positive exploratory estimate `70.630/lot` (`n=373`, original CI
`[4.704, 138.501]`) was not used to retain it; the accountId-clustered
recomputed interval is `[-1.069, 147.010]`.

## 7. C66 scope restatement

The adopted convention is to exclude C66 from both the numerator and
denominator because it is a corrupted single-position export. The corrected
common-split V2 denominator is `n=6,582` (C53-C65), with `177` acted trades and
coverage `2.6892%` (`2.69%`). The full frozen predict path still returns 178
acts on 6,583 rows; that is the superseded mixed-scope figure, not the adopted
reporting convention.

### Coverage restatements

| panel | superseded count / denominator | superseded coverage | corrected count / denominator | corrected coverage | delta (percentage points) |
|---|---:|---:|---:|---:|---:|
| V2 common split | 178 / 6,583 | 2.7039% | 177 / 6,582 | 2.6892% | -0.0148 |
| V3 common split | 6 / 6,583 | 0.0911% | 5 / 6,582 | 0.0760% | -0.0151 |
| V2 IS / training | 4 / 694 | 0.5764% | 4 / 694 | 0.5764% | 0.0000 |
| V3 IS / training | 2 / 694 | 0.2882% | 2 / 694 | 0.2882% | 0.0000 |

The seven V2 coverage-frontier rows are restated below. Counts are shown so
the denominator change is auditable; the effect estimates and accountId CIs
are unchanged from the C53-C65 computation in Section 2.

| target | superseded count / 6,583 | superseded coverage | corrected count / 6,582 | corrected coverage | delta pp |
|---:|---:|---:|---:|---:|---:|
| 1% | 66 / 6,583 | 1.0026% | 66 / 6,582 | 1.0027% | +0.0002 |
| 2.7% | 178 / 6,583 | 2.7039% | 177 / 6,582 | 2.6892% | -0.0148 |
| 5% | 329 / 6,583 | 4.9977% | 329 / 6,582 | 4.9985% | +0.0008 |
| 10% | 658 / 6,583 | 9.9954% | 658 / 6,582 | 9.9970% | +0.0015 |
| 25% | 1,646 / 6,583 | 25.0038% | 1,646 / 6,582 | 25.0076% | +0.0038 |
| 50% | 3,292 / 6,583 | 50.0076% | 3,291 / 6,582 | 50.0000% | -0.0076 |
| 100% target | 5,616 / 6,583 | 85.3106% | 5,615 / 6,582 | 85.3084% | -0.0022 |

The superseded figures appear in `stage3_report.pdf`,
`reports/stage3_backtest.md`, `reports/trials_log_and_power.md`,
`report/dual_split.md`, `report/per_campaign.md`, `report/is_oos_gap.md`, and
`report/baselines_common_split.md`. The old documents mix a C53-C65 dollar
base with a C53-C66 coverage denominator; the table above is the explicit
restatement.

Under the adopted convention, C66 exclusion is applied identically to the
numerator, denominator, dollar total, and acted-lot base for DO NOTHING, MODEL,
and FADE EVERYTHING. The frozen artifact and model code are unchanged; this is
a reporting-scope correction. In particular, the historical frozen path's
dollar-total exclusion was already C66-specific, while its coverage denominator
still included C66, which is why the superseded mixed-scope figures existed.

**Verdict:** all power claims are restated at the corrected accountId floor;
no model, feature definition, fitted value, or artifact was changed.
