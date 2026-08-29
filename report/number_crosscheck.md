# Stage 3 number cross-check

Date: 2026-08-26  
Scope: `stage3_report.pdf` and the Stage 3 supporting reports/artifact in this
repository. This is read-only; no model, feature, fit, or artifact was changed.
The PDF is four pages and has no separately titled appendix; the repository's
supporting Markdown reports are the appendix/source artifacts listed at the end.

## Result

The core identities and the C53–C65 dollar arithmetic reproduce. Mismatches are
present in the submitted brief's labels and lineage:

- the brief says “24 admissible features” for V2, but the frozen V2 artifact and
  `predict()` use 20 raw features;
- the common-split table labelled C53–C66 reports the C53–C65 dollar-eligible
  subset (6,582 rows, 177 acted), while the full evaluation contains 6,583 rows
  and 178 acted;
- the historical confidence intervals are traderKey-clustered, not
  `accountId`-clustered; the earlier `[-51.066, 71.316]` interval was also
  mislabeled as trade-level in one audit path;
- the brief says “19 tests” but the frozen submission tag has 20 tests. The
  current worktree has 28 after later compliance-test additions.

`MATCH` below means the recomputation agrees after the brief's displayed
rounding. `MISMATCH` means the stated value, label, denominator, or provenance
does not match the relevant artifact. No mismatch is silently corrected.

## Direct identity checks

### Reverse-profit identity

The position-level check was run from the repaired raw loaders and
`pipeline.to_positions()`:

```text
residual = reverseProfit - (-profit - 7.00 * amount)
n = 7,277 positions
max absolute residual = 4.547473508864641e-13 dollars
rows with residual > 1e-9 = 0
```

This is an exact identity to floating-point precision. The Stage 3 source report
also checks the per-lot form `reverseProfit/amount` against
`-profit/amount - 7.00`, for the same `n = 7,277`, with maximum absolute
deviation `9.094947017729282e-13`. The two maxima differ only because one check
is in dollars and the other is per lot.

**Result: MATCH.**

### Commission regression

The brief's formula is a regression statement, not an exact row-wise identity.
The source report's “commission” convention is positive commission cost, i.e.
`commission_cost = -commission` for the signed raw field. On the primary-era
source scope C53–C65:

```text
OLS commission_cost ~ amount
n = 6,582 positions
intercept = 0.001953172318209890  -> 0.0020
slope     = 34.99171226729312     -> 34.9917
R^2       = 0.9998359284435611    -> 0.9998
```

The signed raw `commission` column instead has intercept
`-0.001953172318209890` and slope `-34.99171226729312`. Thus the printed
formula matches the artifact under the positive-cost convention; interpreted as
the signed raw column it has the opposite sign. That convention is made
explicit here rather than hidden.

**Result: MATCH under the source report's cost convention; SIGN-CONVENTION
MISMATCH if “commission” means the signed raw column.**

### Dollar loss, size-weighted result, and the common denominator

For the dollar-eligible model set (C53–C65; C66 excluded):

```text
n acted                          = 177
acted lots                       = 105.08000000000001 -> 105.08
acted dollar reverseProfit       = -3,556.81
exact SW/lot                     = -3,556.81 / 105.08
                                 = -33.84859154929577 -> -33.849
```

The arithmetic uses the unrounded SW value. Multiplying the displayed rounded
figures gives `-33.849 * 105.08 = -3,556.85292`, a `$0.04292` display-rounding
difference; it is not a data mismatch. Using the unrounded value and the exact
lot sum reconciles to `-$3,556.81`.

The same 105.08-lot base is used for the size-weighted dollar total and for the
C66-excluded dollar total. C66 contributes one acted observation with 462.30
lots and `-$4,019.40`, but it is excluded from dollar totals. It is retained in
the full per-lot evaluation, which is why the full `predict()` evaluation has
178 acted rows.

For the brief's printed percentage:

```text
177 / 6,583 * 100 = 2.6887437338599423% -> 2.69%
```

This displayed percentage reconciles numerically, but the numerator is the
C66-excluded acted count and the denominator includes C66. The full predict
count is `178 / 6,583 = 2.703934...% -> 2.70%`.

**Result: MATCH for the C53–C65 dollar arithmetic; SCOPE MISMATCH for the
“C53–C66, 177 acted” label.**

### “47 of 48 effects undetectable”

The one effect above the stated training detection floor is:

| field | value |
|---|---:|
| effect | `trader_prior_survival`, Track A |
| n | 373 |
| point estimate | `70.630/lot` |
| traderKey-clustered 95% CI | `[4.704, 138.501]` |
| IP-clustered 95% CI | `[4.340, 144.273]` |
| raw p | `0.037` |
| in final V2 acted feature set? | **No** |

It was screened in the 24-feature family but dropped from the final 20 raw V2
inputs. It therefore is not one of the 20 fitted V2 features. The remaining
`47` of `48` pooled admissible Track A/Track B feature-track effects did not
clear the stated training MDE floor.

**Result: MATCH.**

## Claim register: brief and supporting artifacts

The register below covers every quantitative claim printed in the four-page
Stage 3 brief, including its tables and the supporting values that the brief
quotes from the Stage 3 reports. Page numbers and document dates are not treated
as scientific claims. “Source artifact” is the repository object from which the
brief's number is stated to originate; “recomputed” is the direct check or the
authoritative value read from that object.

### Data, target, model, and feature claims

| claim | stated value | source artifact | recomputed value | status |
|---|---:|---|---:|---|
| fills collapsed to positions | `46,520 -> 7,277` | [`reports/stage3_backtest.md`](../reports/stage3_backtest.md), `pipeline.py` | `46,520 -> 7,277` | MATCH |
| position stream campaign count | `34 campaigns` | [`docs/eda_memo.md`](../docs/eda_memo.md) | `34` campaigns in loaded position stream | MATCH |
| reverse-profit cost | `$7.00/lot`, applied once | [`reports/common_split_viability.md`](../reports/common_split_viability.md), `stage3_model.py` | exact identity above, `n=7,277` | MATCH |
| common training window | C33–C52, `n=694` | [`artifacts/stage3_v2.json`](../artifacts/stage3_v2.json), [`reports/stage3_backtest.md`](../reports/stage3_backtest.md) | `694` | MATCH |
| common evaluation window | C53–C66, `n=6,583` | artifact/backtest report | `6,583` | MATCH |
| inner alpha selection | `alpha=1000` | artifact/backtest report | artifact `alpha_cv_selected=1000` | MATCH |
| frozen alpha | `3162.28` | `artifacts/stage3_v2.json` | `3162.27766017`, displayed `3162.28` | MATCH |
| hurdle | `0` | artifact/backtest report | artifact hurdle `0.0` | MATCH |
| target preprocessing | training-fold 1st/99th percentile winsorization | [`stage3_model.py`](../stage3_model.py), artifact | artifact stores training winsorization bounds | MATCH |
| V2 raw feature count | `24 admissible features` | [`stage3_report.pdf`](../stage3_report.pdf), [`reports/trials_log_and_power.md`](../reports/trials_log_and_power.md) | artifact `feature_names` has `20`; `V2_FEATURES` has `20` | **MISMATCH: stale count** |
| V1 history fields | `4` plus cold-start indicator | Stage 3 brief and feature-count audit | four history definitions are identifiable; V1 comparison is documented | MATCH |
| V2 cold-start rate | `79.39%` | [`reports/common_split_viability.md`](../reports/common_split_viability.md) | `5,214/6,568` keyed rows = `79.39%`; overall source report also reports `6,583` eval rows | MATCH, keyed denominator stated |
| V1 cold-start coefficient | `2.705` | [`reports/common_split_viability.md`](../reports/common_split_viability.md) | source coefficient `2.705` | MATCH |
| four history coefficients | `0.012–0.547` | common-split viability report | source range `0.012–0.547` | MATCH |
| V1 full-eval CI | `[-49.44, 43.16]` | [`reports/common_split_viability.md`](../reports/common_split_viability.md) | source value `[-49.44, 43.16]` | MATCH (historical method) |
| V2 full-eval CI in brief | `[-58.43, 37.92]` | common-split viability report | source value `[-58.43, 37.92]` | MATCH (historical method) |
| history-bearing rows | `20.57%` | common-split viability report | source value `20.57%` | MATCH |
| history-bearing V1/V2 means | `-2.58` vs `+10.03` | common-split viability report | source values `-2.58`, `+10.03` | MATCH |
| inadmissible SL/TP feature count and names | `4`: `sl_distance_pct`, `sl_widening_delta`, `has_sl`, `has_tp` | [`audit/tp_admissibility_2026-08-24.md`](../audit/tp_admissibility_2026-08-24.md) | same four names | MATCH for the original ruling |
| multi-fill primary positions in recovery audit | `4,543` | `audit/tp_admissibility_2026-08-24.md` | `4,543` | MATCH |
| slPrice change rate | `73.12%` | tp admissibility audit | source value `73.12%` | MATCH |
| tpPrice change rate | `79.84%` | tp admissibility audit | source value `79.84%` | MATCH |
| direction violation, first vs last fill | `11.98%` vs `16.51%` | tp admissibility audit | source values `11.98%`, `16.51%` | MATCH |
| violating rows | `-68.53/lot`, `57.12%` win rate | tp admissibility audit | source values `-68.53`, `57.12%` | MATCH |
| decision score threshold | `theta_sel=-10` | artifact/backtest report | artifact selected threshold `-10.0` | MATCH |
| economic execution hurdle | `0` | artifact/backtest report | `0.0` | MATCH |
| abstain overrides | `2`: `win_streak > 1`, `trades_per_hour > 60` | artifact/backtest report | artifact contains both exact overrides | MATCH |
| features described as retained/admissible | `sl_usage_rate_5`, `manual_exit_rate_5`, `trader_prior_sl_discipline` | Stage 3 brief and [`audit/rolling_feature_sweep.md`](../audit/rolling_feature_sweep.md) | the sweep flags `sl_usage_rate_5` and `manual_exit_rate_5` as contaminated; `trader_prior_sl_discipline` is not in the final 20 | **MISMATCH: later compliance audit** |

The separate rolling-feature audit later found 11 of the 20 V2 features consume
close-time data. Those are listed in the Known Corrections section below; this
is a compliance correction to the brief's admissibility narrative, not a change
to the frozen fit.

### Common-split and campaign claims

| claim | stated value | source artifact | recomputed value | status |
|---|---:|---|---:|---|
| model with overrides, C53–C65 | `n=177`, `2.69%`, EW `+10.433`, SW `-33.849`, dollars `-$3,556.81` | [`reports/stage3_backtest.md`](../reports/stage3_backtest.md) | `177`, `177/6,583=2.68874%`, EW `10.4327298`, SW `-33.8485915`, dollars `-3556.81` | MATCH after rounding; denominator scope noted above |
| model with no overrides | `n=183`, `2.78%`, EW `+10.452`, dollars `-$3,534.65` | stage3 backtest report | source backtest reproduces these values | MATCH (historical method) |
| DO NOTHING | `n=0`, `0.00%`, EW `0`, dollars `$0` | stage3 backtest report | `0`, `0%`, `$0` by construction | MATCH |
| FADE EVERYTHING, C53–C65 | `n=6,582`, `100%`, EW `+5.436`, SW `-3.001`, dollars `-$12,108.71` | stage3 backtest report | source C53–C65 totals reproduce; C66-excluded dollar base | MATCH |
| same table labelled C53–C66 | `n=177` model, `n=6,582` fade | `stage3_report.pdf` and duplicated C53–C66 table in backtest report | full evaluation is `n=6,583`, model acted `178`, fade rows `6,583`; C66-excluded dollar subset is `6,582`/`177` | **MISMATCH: scope label** |
| historical model EW account CI | `[-52.786, 72.331]` | stage3 backtest report | source traderKey bootstrap gives `[-52.786,72.331]` | MATCH numerically; cluster label correction below |
| historical model EW IP CI | `[-45.183, 66.523]` | stage3 backtest report | source IP bootstrap gives `[-45.183,66.523]` | MATCH |
| historical model SW account CI | `[-74.360, 1.166]` | stage3 backtest report | source traderKey bootstrap gives `[-74.360,1.166]` | MATCH numerically; cluster label correction below |
| historical fade EW CI | `[-9.339,20.713]` | stage3 backtest report | source traderKey bootstrap gives `[-9.339,20.713]` | MATCH numerically; cluster label correction below |
| historical fade SW CI | `[-11.031,5.381]` | stage3 backtest report | source traderKey bootstrap gives `[-11.031,5.381]` | MATCH numerically; cluster label correction below |
| model fraction of fade dollar loss | `29.37%` | stage3 backtest report | `3,556.81/12,108.71*100=29.3739796%` | MATCH |
| model position share | `2.69%` | stage3 backtest report | `177/6,582=2.68915%` on C53–C65; `177/6,583=2.68874%` on labelled full eval | MATCH after stated denominator |
| model amount share | `2.60%` | stage3 backtest report | `105.08/4,034.37*100=2.60462%` | MATCH |
| position-share multiple | `10.92x` | stage3 backtest report | `29.37398/2.68915=10.9231x` | MATCH |
| amount-share multiple | `11.28x` | stage3 backtest report | `29.37398/2.60462=11.2776x` | MATCH |
| best campaign C53 | `+173.557`, `n=5`, CI `[48.512,510.000]` | stage3 backtest report | source campaign row reproduces all values | MATCH numerically; current accountId CI is `[62.119,411.750]` |
| C53 removed | `+5.691`, `n=172`, CI `[-60.200,66.313]` | stage3 backtest report | source point and n reproduce; accountId recomputation is `[-51.592,64.648]` | MATCH point; CI method differs |
| C59 | `-99.990`, `n=21`, CI `[-221.813,-8.205]` | stage3 backtest report | source point and n reproduce; accountId recomputation is `[-212.512,-13.058]` | MATCH point; CI method differs |
| negative campaigns | `7 of 13` | stage3 backtest report | per-campaign source rows contain 7 negative means among C53–C65 | MATCH |
| Track A pooled own split | `+14.130`, `n=114`, `5.21%`, CI `[-80.926,111.031]` | stage3 backtest report | source values reproduce; accountId CI `[-78.912,101.596]` | MATCH point; CI method differs |
| Track A fade baseline | `+21.711`, CI `[-3.458,44.978]` | stage3 backtest report | source value; accountId CI `[-2.682,45.611]` | MATCH point; CI method differs |
| Track B fold 2 | `-210.475`, CI `[-479.776,-43.912]` | stage3 backtest report | source value; accountId CI `[-463.728,-48.091]` | MATCH point; CI method differs |
| Track B fold coverage | `5.58%`, `1.84%`, `16.14%`, `0.50%` | stage3 backtest report | source four fold values reproduce | MATCH |
| training EW | `+50.897`, `n=4`, CI `[-62.924,193.331]` | stage3 backtest report | source point/n reproduce; accountId CI `[-37.213,142.123]` | MATCH point; CI method differs |
| evaluation EW | `+10.325`, `n=178` | stage3 backtest report | current full C53–C66 prediction gives `178`, `10.325` | MATCH |
| IS-to-OOS gap | `-40.571/lot` | stage3 backtest report | `10.325-50.897=-40.572` using rounded inputs; source unrounded gap `-40.571` | MATCH after rounding |

The brief's prose says “significantly negative” for C59 and Track B fold 2. The
numeric evidence is the displayed CI excluding zero: C59
`[-221.813,-8.205]`, and Track B fold 2 `[-479.776,-43.912]`. No qualitative
label is being used without its interval.

### Power, MDE, and score-distribution claims

| claim | stated value | source artifact | recomputed value | status |
|---|---:|---|---:|---|
| training size and account count | `694` positions, `330` accounts | [`reports/trials_log_and_power.md`](../reports/trials_log_and_power.md), design annex | source counts reproduce | MATCH |
| evaluation size and account count | `6,583` positions, `496` accounts | trials/power report and cluster report | source counts reproduce | MATCH |
| positions per admissible feature | `28.92` | Stage 3 brief | `694/24=28.9167 -> 28.92`; actual V2 fitted denominator is `20`, giving `34.70` | **MISMATCH: uses stale 24 denominator** |
| accounts per admissible feature | `13.75` | Stage 3 brief | `330/24=13.75`; actual V2 fitted denominator gives `330/20=16.50` | **MISMATCH: uses stale 24 denominator** |
| keyed cold-start rate | `79.39%` | common-split viability | `5,214/6,568=79.39%` keyed denominator | MATCH |
| training MDE range | `$65–78/lot` | trials/power report | published traderKey values are `$67.94` winsorized and `$78.20` raw; current accountId recomputation is `$53.02–$61.03` | **MISMATCH: clustering version/label** |
| training ICC/DEFF | `0.162/1.753` account; `0.096/1.615` IP | design annex/trials report | published values `0.162328/1.753221` and `0.096472/1.615386` | MATCH for published method |
| detectable effect count | `1 of 48` | trials/power report | one named effect above floor; 47 below | MATCH |
| regime-break cost | `$12.27/lot` | common-split viability | source flagged mean `12.2731` | MATCH |
| selected threshold support | `theta=-10`, `n=88`, `12.68%` | artifact/backtest report | artifact threshold support `88`, `88/694=12.6801%` | MATCH |
| executable threshold support | grid `[0,500]`, max `n=4`, mean `+50.897` | artifact/backtest report | source executable sweep gives `n=4`, mean `50.897`; floor is `n>=30` | MATCH |
| MDE formula inputs | `2.801585`, alpha `.05`, power `.80`, raw sigma `555.33`, winsorized `482.45` | trials/power report and design annex | source full values `555.3263`, `482.4515`; same formula and inputs | MATCH |
| coverage frontier rows | `1%, 2.7%, 5%, 10%, 25%, 50%, 100% target` | Stage 3 brief power table | seven rows present; last target reaches `85.31%` because overrides cap execution | MATCH with target/achieved distinction |
| frontier row 1% | `n=66`, `1.00%`, `+0.918`, CI `[-116.23,110.63]`, MDE `191.50` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 2.7% | `n=178`, `2.70%`, `+10.325`, CI `[-52.20,72.29]`, MDE `116.61` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 5% | `n=329`, `5.00%`, `+23.329`, CI `[-27.05,75.82]`, MDE `92.28` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 10% | `n=658`, `10.00%`, `+21.691`, CI `[-21.42,66.44]`, MDE `71.30` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 25% | `n=1,646`, `25.00%`, `+31.743`, CI `[-0.61,62.69]`, MDE `43.41` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 50% | `n=3,292`, `50.01%`, `+21.666`, CI `[-0.20,43.67]`, MDE `31.53` | stage3 backtest/trials report | source row reproduces | MATCH point/table; CI historical method |
| frontier row 100% target | `n=5,616`, `85.31%`, `+13.135`, CI `[-2.93,29.41]`, MDE `26.49` | stage3 backtest/trials report | source row reproduces | MATCH; `100%` is target, not achieved coverage |
| acting-subset ICC | `-0.089` account, `-0.098` IP, mean cluster `~2.7` | Stage 3 brief power note | source values reproduce | MATCH for historical power calculation |
| unfloored account MDE at 2.7% | `$107.46` raw, `$93.36` winsorized | Stage 3 brief/trials report | source values reproduce | MATCH |
| frontier clears | `0 of 7` | Stage 3 brief/trials report | all seven source rows have `clears?=no` | MATCH |
| closest frontier ratio | `0.84` at 25% | Stage 3 brief/trials report | `31.743 /` the winsorized 25% MDE `37.71 = 0.8418 -> 0.84`; raw table MDE is `43.41` | MATCH, denominator is winsorized MDE |
| score distribution | median `-29.92`, p75 `-15.29`, p99 `+27.53`, SD `30.36` | stage3 backtest report/artifact prediction | source prediction summary reproduces | MATCH |
| top 1% result | `+0.918/lot` | Stage 3 power section | source frontier row reproduces | MATCH |

### Trials, freeze, forecast, and C66 claims

| claim | stated value | source artifact | recomputed value | status |
|---|---:|---|---:|---|
| trials logged | `101` | [`reports/trials_log_and_power.md`](../reports/trials_log_and_power.md) | ledger sums `10+4+56+4+4+6+1+12+4=101` | MATCH for the old ledger |
| scalar outcome tests corrected | `90` | trials/power report | `14+56+4+4+12=90` | MATCH for the old ledger |
| BH q level | `.05` | trials/power report | source BH q `.05` | MATCH |
| full-log survivors | `sl_distance_pct` tests only | trials/power report | two contaminated `sl_distance_pct` track tests survive full-log correction; no admissible survivor | MATCH for the historical classification; admissibility correction below |
| bootstrap replicates and seed | `n_boot=2,000`, seed `7` | [`reports/trials_log_and_power.md`](../reports/trials_log_and_power.md) | source report and current bootstrap configuration use `2,000` and `7` | MATCH |
| old trial-family ledger | `10 + 4 + 56 + 4 + 4 + 6 + 1 + 12 + 4` | trials/power report | family sum is `101` | MATCH |
| invalidated historical Stage 2 tests | `8` | trials/power report | four invalidated features × two tracks = `8` | MATCH |
| threshold candidate grid | `-100..500` by `1`; executable `[0,500]` | stage3 backtest report | source sweep contains the stated grids | MATCH |
| six conditional states | `6` | Stage 3 brief/trials report | source ledger has six states | MATCH |
| threshold sources | `2`: S1 and S2 | Stage 3 brief/trials report | source ledger has S1/S2 | MATCH |
| S1 scope | campaigns `<=52`, `n=694`, MDE `$65–78` | trials/power report | source scope and published MDE reproduce; current cluster correction changes MDE | MATCH scope; method label correction |
| S2 scope | C53–C65 and leaky | trials/power report | source says C53–C65-derived threshold source | MATCH |
| S2 unadjusted cells | states `3/4` clear zero | trials/power report | source states 3 and 4 clear zero before correction | MATCH |
| frozen artifact and configuration | `stage3_v2.json`, V2, alpha `3162.28`, hurdle `0`, `2` overrides | artifact and stage3 model | artifact and code match these values | MATCH |
| brief test count | `19 tests` | `stage3_report.pdf` | frozen tag `stage3-submission` has 20 tests per the submission record; current worktree has 28 | **MISMATCH** |
| forecast EW | `0.00`, 95% interval `[-62,+62]` | Stage 3 brief | forecast text uses half-width `62.25`, rounded to `62`; it is a forecast, not a new fit | MATCH as forecast rounding |
| forecast coverage | `under 5%` | Stage 3 brief | frozen full evaluation `2.70%`; own-fold coverage range includes `0.50%–17.89%` | MATCH as a forecast statement, not a universal fold bound |
| forecast own-fold range | `0.50%–17.89%` | stage3 backtest report | Track A fold coverage includes `0.89%`/`17.89%`; Track B includes `0.50%`; source broader range reproduces | MATCH |
| forecast SW | negative | stage3 backtest report | frozen model SW is `-33.849/lot` on C53–C65 and `-13.353/lot` full acted C53–C66 | MATCH with numeric evidence |
| forecast half-width | `62.25` | Stage 3 brief | `(72.29 - (-52.20))/2 = 62.245 -> 62.25` | MATCH |
| C53 removal half-width | `63.26` | Stage 3 brief | source C53-removed historical CI `[-60.200,66.313]` has half-width `63.2565 -> 63.26` | MATCH |
| C66 fill collapse | `1,911 fills -> 1 position` | stage3 backtest report and PDF | source C66 row reproduces | MATCH |
| C66 amount | `462.30 lots` | stage3 backtest report/PDF | source C66 sum amount `462.30` | MATCH |
| primary-era maximum collapsed amount | `6.50 lots` | stage3 backtest report/PDF | source C53–C65 maximum `6.50` | MATCH |
| C66 dollar contribution | `-$4,019.40` | stage3 backtest report/PDF | source C66 actual absolute reverseProfit `-4019.40` | MATCH |
| C66 retained per-lot count | `n=178` | stage3 backtest report/PDF | full predict evaluation acts on `178`, including C66 | MATCH |

## Confidence-interval provenance correction

The numeric historical intervals in the brief reproduce the old backtest. Their
unit label does not match the implementation. The old implementation resamples
`traderKey` clusters, falling back to `campaignId::accountId`; it does not
resample `accountId` directly and is not trade-level.

The corrected common-split values in
[`report/clustering_recompute.md`](clustering_recompute.md) are:

| metric | historical brief interval (traderKey) | accountId-clustered recomputation |
|---|---|---|
| model EW, 177 acted C53–C65 | `[-52.786,72.331]` | `[-46.117,66.826]` |
| model SW, 177 acted C53–C65 | `[-74.360,1.166]` | `[-70.260,2.964]` |
| fade EW, C53–C65 | `[-9.339,20.713]` | `[-8.572,20.475]` |
| fade SW, C53–C65 | `[-11.031,5.381]` | `[-10.493,4.840]` |

The earlier interval `[-51.0655,71.3163]` was also not trade-level: it used the
legacy `traderKey` cluster with the campaign-account fallback. The direct
trade-level comparator was `[-50.682,74.119]`; the accountId result is
`[-46.117,66.826]`.

## Known corrections for the addendum

These are corrections to the disclosure, not retrospective model changes:

1. **24 -> 20 feature count (stale docs).** The 24 number was the screened
   admissible family. The frozen V2 artifact/predict path contains 20 raw
   features and 21 transformed columns. The four absent definitions are
   deliberate hardcoded V2 omissions, not a fit/predict mismatch.
2. **CI-unit label.** The interval label in
   `report/clustering_recompute.md` and the related earlier audit path must not
   call `[-51.066,71.316]` trade-level or `accountId`-clustered. Its actual unit
   was legacy `traderKey` clusters with a campaign-account fallback. The direct
   trade-level comparator is `[-50.682,74.119]`; the accountId interval is
   `[-46.117,66.826]`.
3. **11 contaminated V2 features.** The rolling-feature sweep identifies these
   11 V2 inputs as consuming at least one close-time field:

   `loss_streak`, `win_streak`, `pnl_ewm`, `size_after_loss_delta`,
   `sl_usage_rate_5`, `manual_exit_rate_5`, `pnl_pct`, `dd_from_peak_pct`,
   `log_dt_close`, `prior_campaigns_x_loss_streak_ge_2`, and
   `same_direction_reentry`.

   The corresponding sweep reports 9 clean and 11 contaminated, but this does
   not alter `stage3_v2.json` or refit any model.

## Source inventory

- Brief: [`stage3_report.pdf`](../stage3_report.pdf).
- Frozen model: [`artifacts/stage3_v2.json`](../artifacts/stage3_v2.json) and
  [`stage3_model.py`](../stage3_model.py).
- Main backtest/economics: [`reports/stage3_backtest.md`](../reports/stage3_backtest.md).
- Trials and power: [`reports/trials_log_and_power.md`](../reports/trials_log_and_power.md)
  and [`reports/design_annex_stats.md`](../reports/design_annex_stats.md).
- Data identity and viability: [`reports/common_split_viability.md`](../reports/common_split_viability.md)
  and [`reports/decay_and_cost_structure.md`](../reports/decay_and_cost_structure.md).
- Leakage and feature-count corrections: [`audit/tp_admissibility_2026-08-24.md`](../audit/tp_admissibility_2026-08-24.md),
  [`audit/rolling_feature_sweep.md`](../audit/rolling_feature_sweep.md), and
  [`audit/feature_count_reconciliation.md`](../audit/feature_count_reconciliation.md).
- Bootstrap correction: [`report/clustering_recompute.md`](clustering_recompute.md).

## Item C — C66 coverage-scope restatement

C66 is excluded from both the numerator and denominator under the adopted
convention because it is a corrupted single-position export. The corrected V2
common-split result is `177 / 6,582 = 2.6892%` (reported as `2.69%`). V3 is
`5 / 6,582 = 0.0760%`. The frozen full-predict count remains `178 / 6,583`;
that `2.7039%` figure is the superseded mixed-scope result.

| coverage panel | old count / denominator | old coverage | corrected count / denominator | corrected coverage | delta pp |
|---|---:|---:|---:|---:|---:|
| V2 common split | 178 / 6,583 | 2.7039% | 177 / 6,582 | 2.6892% | -0.0148 |
| V3 common split | 6 / 6,583 | 0.0911% | 5 / 6,582 | 0.0760% | -0.0151 |
| V2 IS / training | 4 / 694 | 0.5764% | 4 / 694 | 0.5764% | 0.0000 |
| V3 IS / training | 2 / 694 | 0.2882% | 2 / 694 | 0.2882% | 0.0000 |

The seven V2 coverage-frontier rows are also restated under `n=6,582`:

| target | old count / 6,583 | old coverage | corrected count / 6,582 | corrected coverage | delta pp |
|---:|---:|---:|---:|---:|---:|
| 1% | 66 | 1.0026% | 66 | 1.0027% | +0.0002 |
| 2.7% | 178 | 2.7039% | 177 | 2.6892% | -0.0148 |
| 5% | 329 | 4.9977% | 329 | 4.9985% | +0.0008 |
| 10% | 658 | 9.9954% | 658 | 9.9970% | +0.0015 |
| 25% | 1,646 | 25.0038% | 1,646 | 25.0076% | +0.0038 |
| 50% | 3,292 | 50.0076% | 3,291 | 50.0000% | -0.0076 |
| 100% target | 5,616 | 85.3106% | 5,615 | 85.3084% | -0.0022 |

Superseded coverage figures are stated in `stage3_report.pdf`,
`reports/stage3_backtest.md`, `reports/trials_log_and_power.md`,
`report/dual_split.md`, `report/per_campaign.md`, `report/is_oos_gap.md`, and
`report/baselines_common_split.md`. The old documents mix the C53-C65 dollar
and lot base with a C53-C66 coverage denominator; the tables above are the
explicit restatements.

For the corrected reporting convention, C66 is excluded identically from the
numerator, denominator, dollar totals, and acted-lot bases for DO NOTHING,
MODEL, and FADE EVERYTHING. This is a reporting-scope correction only: the
frozen model, artifact, and feature definitions remain unchanged. The
historical frozen path already excluded C66 from dollar totals but had not
excluded it from the coverage denominator, which explains the superseded
figures.

## Item D — canonical SW/lot definition

Two different denominators had been used for the same headline dollar total:

1. **C66-excluded SW/lot:** `-$3,556.81 / 105.08 lots = -33.84859155`,
   reported as `-33.849/lot`. This uses the 177 non-C66 acted trades and the
   same non-C66 lot base as the dollar total.
2. **C66-included per-lot SW/lot:** total realized reverseProfit including the
   C66 row, `-$7,576.21`, divided by all 178 acted lots, `567.38`, gives
   `-13.35297332`, reported as `-13.353/lot`. Its numerator and denominator
   include C66, while its displayed dollar total excludes C66; it is therefore
   not coherent with the `-$3,556.81` dollar total.

The submission canonical is **`-33.8486/lot` (reported as `-33.849/lot`)**,
with `n=177` and the accountId-clustered 95% CI **`[-70.260, 2.964]`**.

| document | superseded SW/lot | canonical SW/lot | delta |
|---|---:|---:|---:|
| `stage3_report.pdf` | -33.849 | -33.849 | 0.000; CI restated to accountId `[-70.260,2.964]` |
| `reports/stage3_backtest.md` | -33.849 | -33.849 | 0.000; CI restated to accountId `[-70.260,2.964]` |
| `reports/trials_log_and_power.md` | no model SW headline | no model SW headline | no point restatement; baseline scope restated |
| `report/dual_split.md` | -13.3530 | -33.8486 | -20.4956 |
| `report/per_campaign.md` V2 | -13.353 | -33.849 | -20.496 |
| `report/is_oos_gap.md` V2 OOS | -13.3530 | -33.8486 | -20.4956 |
| `report/baselines_common_split.md` MODEL | -13.353 | -33.849 | -20.496 |

For V3, the analogous C66 scope restatement is old SW `-8.0403/lot` on 6
acted rows and 463.58 lots to corrected SW `228.1797/lot` on 5 acted rows and
1.28 lots, a delta of `+236.220/lot`. This is a scope correction, not a model
refit.

## Item E — `ip_cluster_size` and clean detectable effects

`ip_cluster_size` is **CLEAN** and is in V2. It consumes current-entry
`ip_cluster_size` or `ipClusterSize`, whose sanitized origin is
`ipClusterId`/`ip_address` metadata and active `accountId`/account counts.
These are OPEN-TIME/context metadata fields; it consumes no prior close-time
field and no profit, close, SL, or TP field.

Of the 3 point estimates above `$53.02/lot`, **1 is clean**:
`ip_cluster_size` (`n=369`, `67.775/lot`, accountId CI `[3.919,144.992]`).
`manual_exit_rate_5` is contaminated and `trader_prior_survival` is also
contaminated. Therefore **1 of the 48 tested effects is both clean and above
`$53.02/lot`**, namely `ip_cluster_size`.

## Item F — V3 IS interval check

V3 IS contains `n=2` acted trades in two singleton accountId clusters. Re-running
the fixed-seed accountId bootstrap gives the same endpoint interval for both
metrics: EW `-37.2130/lot`, CI `[-62.9240,-11.5020]`; SW `-12.7973/lot`, CI
`[-62.9240,-11.5020]`. Neither interval is incorrect; the identical endpoints
are a consequence of the two-singleton-cluster bootstrap distribution.

## Item G — why the training panel starts at C33

The supplied trade schema contains exactly 34 campaigns, C33-C66, with
`7,277` collapsed positions: C33-C52 contributes `694` and C53-C66
contributes `6,583`. C1-C32 contain **no trades in this dataset**. They were
not filtered after ingestion and no acted/no-acted decision was applied to
them. The loader's `EXPECTED_CAMPAIGNS = set(range(33, 67))` and the
`datasets/user_trades` directory both establish that scope.

## Item H — file-by-file C66 coverage restatements

The old and corrected headline coverage values are:

| file | superseded coverage | corrected coverage | delta |
|---|---:|---:|---:|
| `stage3_report.pdf` headline model | `177/6,583 = 2.6887%` (displayed 2.69%) | `177/6,582 = 2.6892%` | +0.0004 pp exact; displayed value remains 2.69% |
| `stage3_report.pdf` power 2.7% row | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `reports/stage3_backtest.md` | `177/6,583 = 2.6887%` / historical `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0008 pp / -0.0148 pp |
| `reports/trials_log_and_power.md` | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `report/dual_split.md` | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `report/per_campaign.md` V2 | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `report/per_campaign.md` V3 | `6/6,583 = 0.0911%` | `5/6,582 = 0.0760%` | -0.0151 pp |
| `report/is_oos_gap.md` V2 OOS | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `report/is_oos_gap.md` V3 OOS | `6/6,583 = 0.0911%` | `5/6,582 = 0.0760%` | -0.0151 pp |
| `report/baselines_common_split.md` MODEL | `178/6,583 = 2.7039%` | `177/6,582 = 2.6892%` | -0.0148 pp |
| `report/baselines_common_split.md` FADE EVERYTHING | `6,583/6,583 = 100.00%` | `6,582/6,582 = 100.00%` | 0.0000 pp |

The PDF is the frozen binary brief and has no editable source file in this
clone; its superseded values are explicitly enumerated above and in this
addendum. The Markdown reports have been restated to the corrected convention.
