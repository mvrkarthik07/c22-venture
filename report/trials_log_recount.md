# Trials-log recount

Date: 2026-08-26
Branch: stage3-submission
Frozen source audited: tag stage3-submission-2026-08-21, commit
06efdd595f890857a8ece7f587be5d35f83644c0.

## Verdict

**TRUE PRE-FREEZE SEARCH COUNT: 4,626 auditable trial attempts.**

The published **101** is a narrower endpoint ledger. It counts named
feature/condition results and model comparisons, but not the candidate
evaluations inside the selection loops. It therefore does not answer C22's
question, “how many feature sets, model variants and thresholds did you try?”

The count below is deliberately conservative. A trial attempt means a
data-dependent candidate evaluated by a committed script, a documented
pre-freeze selection grid, or the frozen artifact's fit path. Repeated execution
of the same candidate in an outer fold is counted when it was an independent
fold evaluation. Post-freeze compliance sensitivity is segregated below and is
not included in 4,626.

## Reconciliation of 4,626 against 101

### What the original 101 counted

| Ledger family | Count | Exact contents |
|---|---:|---|
| Stage 1 pre-registered triggers | 10 | The ten named condition definitions: no-SL, loss streak 2, loss streak 3, same-side re-entry, fast re-entry, size escalation, near Rule-B, drawdown, late session, late plus underwater |
| Stage 1 rejected H5 boundaries | 4 | Rule-B, 4% drawdown, 8% target, and ATLSR boundary probes |
| Stage 2 feature endpoints | 56 | 28 frozen features × Track A/Track B |
| Stage 2 composite endpoints | 4 | Two composites × two tracks |
| Stage 2 threshold-protocol endpoints | 4 | Unconstrained versus n>=30, × two tracks |
| Family-G Ridge endpoints | 6 | M1/M2/M3 × Track A/Track B |
| SL-distance recovery diagnosis | 1 | sl_distance_pct_at_open recovery attempt |
| Stage 3 narrow conditional endpoints | 12 | Six states × S1/S2 threshold source |
| Cold-start model endpoints | 4 | V1/V2 × Track A/Track B |
| **Published total** | **101** | **Endpoint/result inventory, not the internal candidate search space** |

The ledger's BH family was smaller still: **90 scalar outcome tests**—14 Stage 1,
56 Stage 2 feature cells, 4 composites, 4 threshold protocols, and 12
conditional cells. The six Family-G model comparisons, the recovery diagnosis,
and the four V1/V2 comparisons were recorded as diagnostics rather than given
zero-edge p-values.

### Previously omitted candidate attempts

| Omitted search component | Count used | Reconciliation evidence |
|---|---:|---|
| Stage 2 fold-local feature-bucket candidates | 770 | feature_checks_walkforward.py:137-216 evaluates each candidate category, binary value, or quantile bucket before retaining one per feature/fold. Recomputed over 28 features, four folds, and two tracks from the local ignored features_v2.csv. The four history features are included: prior_campaigns, trader_prior_tilt, trader_prior_sl_discipline, and trader_prior_survival. |
| Stage 2 amount cutoffs | 714 | feature_checks_walkforward.py:588-617 sweeps every observed eligible amount in folds 3 and 4, for both tracks: (164 + 193) × 2 = 714 candidate evaluations. There are 193 distinct cutoff values; the execution count is retained because the same cutoff was re-evaluated in separate fold/track searches. |
| Family-G alpha candidates | 1,560 | family_g_value.py:22,246-269,272-309: 3 models × 2 tracks × 13 alpha values across inner-fold counts 2, 4, 6, and 8 per outer fold: 3 × 2 × 13 × (2+4+6+8) = 1,560. The 78 distinct model×track×alpha configurations are a subset of these fold evaluations. |
| Frozen V2 alpha grid | 234 | stage3_model.py:135,468-499: 13 values evaluated across the 18 inner expanding-campaign folds in C33-C52: 13 × 18 = 234. |
| Frozen V2 derived final alpha fit | 1 | The selected CV alpha is multiplied by sqrt(10) before the frozen fit; 3162.27766017 is distinct from the grid. |
| Frozen V2 score-threshold grid | 601 | stage3_model.py:136,501-525: integer thresholds -100,-99,...,500, with the n>=30 support rule. The artifact retains 92 eligible candidates, but the loop tests all 601 grid values. |
| S1 conditional-rule candidate grid | 228 | The documented pre-freeze grid in reports/trials_log_and_power.md:241-247: state 1 3×24=72; state 2 3×14=42; state 3 6×3×4=72; state 4 3; state 5 5×3=15; state 6 8×3=24; total 228. |
| Abstain-policy variants | 2 | Frozen V2 comparison: both overrides enabled versus apply_overrides=False, rendered in stage3_model.py:1807-1808. No evidence was found for separate single-override variants. |
| Additional feature definitions in the prune path | 2 | entry_gap_sec and is_cold_start were each evaluated as distinct feature candidates before being dropped. Their pairwise correlations are also included in the separate 406-cell matrix count. |
| Correlation-prune comparisons | 406 | prune_features_v21.py constructs 29 numeric columns (FEATURE_COLUMNS plus entry_gap_sec and is_cold_start, excluding categorical challenge_type) and evaluates every pair: 29×28/2 = 406. |
| Seven earlier documented prune candidates | 7 | FEATURES.md names dist_to_target, dist_to_dd_limit, streak_age_s, lot_ratio_vs_avg, size_pctile, is_repeat, and gap_compression as screened then pruned. They have no standalone scalar p-value in the frozen report, but are retained rather than silently omitted. |
| **Omitted attempts added to the 101** | **4,525** | Sum of the rows above |

Thus, **101 + 4,525 = 4,626**.

The 770 bucket count and 714 amount-cutoff count are search attempts, not extra
held-out outcome rows. They are included because C22 asks for the search space,
not only the post-selection endpoints. The same distinction applies to the 406
correlation comparisons and the alpha candidates.

## Complete feature-set inventory

### Stage 2 feature definitions

The committed build_features.FEATURE_COLUMNS list contains 28 definitions:

    loss_streak
    win_streak
    pnl_ewm
    lot_zscore
    amount
    size_after_loss_delta
    has_sl
    has_tp
    sl_distance_pct
    sl_usage_rate_5
    manual_exit_rate_5
    pnl_pct
    dd_from_peak_pct
    trade_index
    log_dt_close
    trades_per_hour
    prior_campaigns
    prior_campaigns_x_loss_streak_ge_2
    shared_ip
    ip_cluster_size
    challenge_type
    gold_vol_prev_day
    sl_widening_delta
    same_direction_reentry
    size_delta_ratio
    trader_prior_tilt
    trader_prior_sl_discipline
    trader_prior_survival

The four history definitions explicitly screened and then dropped from final V2
were:

    prior_campaigns
    trader_prior_tilt
    trader_prior_sl_discipline
    trader_prior_survival

They are not absent from the original 56 Stage 2 feature endpoints: each has a
Track A and Track B result. They are also included in the 770 internal bucket
candidate count. The final V2 list retains 20 raw features, including
prior_campaigns_x_loss_streak_ge_2.

The four close-time-contaminated definitions removed before the 24-feature
admissible family were:

    has_sl
    has_tp
    sl_distance_pct
    sl_widening_delta

The 24-feature admissible family was therefore the 28-feature list minus those
four. The V2 list was the 24-feature family minus the four history fields above.
This is the exact origin of the “24 screened, 20 selected” distinction.

Two additional fields were tested in the mandated correlation-prune path and
then removed from the feature list:

    entry_gap_sec
    is_cold_start

The seven older names in the count table are documented in the July changelog,
but no committed script in the frozen Stage 2 tree emits a separate outcome
table for them. They are counted as documented screening attempts, with no
p-values fabricated for them.

### Ridge model sets and estimator families

Only one estimator family is evidenced in the committed model-search code:

    Ridge(fit_intercept=True)

The OLS regression in reports/sl_leak_audit_v2.md is a leakage diagnostic, not
a competing predictive estimator. No committed search for Random Forest, Lasso,
Elastic Net, logistic regression, or another estimator was found.

The feature-set variants actually evaluated were:

| Set | Definition |
|---|---|
| M1 | Original Family-A–E set in family_g_value.py, including the then-undropped history and SL/TP fields |
| M2 | M1 plus sl_widening_delta, same_direction_reentry, and size_delta_ratio |
| M3 | M2 plus trader_prior_tilt, trader_prior_sl_discipline, trader_prior_survival, and prior_campaigns_x_loss_streak_ge_2 |
| V1 | The 24 admissible fields plus is_cold_start |
| V2 cold-start comparison | The 24 admissible fields with the four history fields dropped, retaining the interaction; 20 inputs |
| Frozen Stage 3 V2 | The same 20 raw inputs, frozen alpha 3162.27766017, score threshold -10, hurdle 0, and both overrides |
| S1 states | Six fixed conditional states below, with train-only candidate selection |
| S2 states | The same six states using carried-forward Stage 1/2 thresholds; documented as leaky provenance |

The six conditional states were:

1. loss_streak >= 2 AND trades_per_hour in [20, 60]
2. loss_streak >= 2 AND pnl_pct in [-0.033, 0]
3. pnl_ewm in [-31.428, 0] AND trade_index <= 3
4. prior_campaigns == 0 AND loss_streak >= 2
5. ip_cluster_size <= 3 AND loss_streak >= 2
6. loss_streak >= 2 AND manual_exit_rate_5 in [0.25, 0.75]

### Alpha values

The exact 13-value Ridge grid was:

    0.001, 0.00316227766017, 0.01, 0.0316227766017, 0.1,
    0.316227766017, 1.0, 3.16227766017, 10.0, 31.6227766017,
    100.0, 316.227766017, 1000.0

Family-G evaluates these values inside each model/track/fold selection. Frozen
V2 selects 1000.0 by inner CV and fits at the derived 3162.27766017.

## Thresholds, hurdles, coverage, and overrides

| Search item | Values or range | Count/status |
|---|---|---:|
| Stage 1 named trigger cutpoints | loss_streak 2/3; size 1.5/2.0; drawdown 2%; session 0.75; fast re-entry 60s; plus fixed composite definitions | 10 endpoints, in 101 |
| H5 boundary probes | Rule-B 2.5x; drawdown 4%; target 8%; ATLSR 2.5x | 4 endpoints, in 101 |
| Stage 2 amount cutpoints | Every eligible observed amount in folds 3/4, 164 and 193 candidates per track | 714 attempts |
| Stage 2 bucket cutpoints | Per-fold qcut/cut buckets and exact binary/categorical levels | 770 attempts |
| Conditional S1 grid | Exact six-state factorization above | 228 candidates |
| Frozen Stage 3 score threshold | Every integer from -100 through 500 inclusive | 601 candidates |
| Frozen economic hurdle | 0.00 on reverseProfit/lot | Fixed; not swept |
| Earlier gross hurdle | 7.00 on gross_loss_per_lot | Fixed; not swept |
| Coverage frontier | 1%, 2.7%, 5%, 10%, 25%, 50%, 100% | 7 post-freeze diagnostic levels; excluded from pre-freeze m |
| Executable-grid diagnostic | 0..500 by 1 after artifact freeze | 501 post-freeze diagnostic values; excluded from pre-freeze m |
| Abstain overrides | Both enabled; both disabled | 2 variants |

The fixed zero hurdle is not a hidden hurdle search. Negative selected score
thresholds are made executable only through max(selected_threshold, hurdle); the
artifact effective threshold is therefore zero.

## BH correction at the corrected denominator

The corrected pre-freeze family denominator is **m = 4,626**, while the
committed ledger supplies **90 scalar outcome p-values**. I reran the BH
survivor decision using those 90 outcome values with the full C22 search-space
denominator. Internal candidate searches with no scalar held-out outcome
p-value remain in the denominator, which is conservative and avoids treating a
training-selection candidate as an independent p-value.

Result at q=0.05:

| Family | P-value rows | Survivors at original m=90 | Survivors at corrected m=4,626 |
|---|---:|---:|---:|
| All logged scalar outcomes | 90 | 2 contaminated sl_distance_pct cells | **0** |
| Valid Stage 2 feature cells | 48 | 0 | **0** |
| All Stage 2 feature cells, including contaminated | 56 | 2 contaminated cells | **0** |

The original two survivors were the two smallest logged p-values, both
p=0.0005. At m=4,626 their BH values are at least 0.0005 × 4,626 / 2 =
1.1565, even granting the second-smallest p the favorable rank 2. The rank-1
value is 2.313; a rank-1 result would need raw p <= 0.00001081 to reach q=0.05.
Therefore no logged outcome can survive at the larger denominator. No p-value
was invented for the 4,525 internal attempts.

The committed Markdown omits the raw p-value text for eight composite and
threshold-protocol rows, although it records that the full original m=90
correction had only the two p=0.0005 contaminated survivors. The survivor
decision above is therefore an exact conservative recount of the committed
full-log result, not a fabricated per-row q table for those eight omitted
values.

## Degenerate history interaction

prior_campaigns_x_loss_streak_ge_2 consumed one feature definition trial (two
Track A/B endpoint cells) and was carried into V2. The authoritative
field-class audit in audit/bcd_followup.md reports:

| Scope | n | Variance, ddof=0 | Non-zero | Distribution |
|---|---:|---:|---:|---|
| Full dataset | 7,277 | 1.104608 | 6.7748% | 0: 6,784; 1: 130; 2: 118; 3: 61; 4: 50; 5: 46; 6: 32; 7: 19; 8: 10; 9: 15; 10: 6; 11: 4; 12: 2 |
| Seed-7 causal sample | 64 | 0.441162 | 3.1250% | 0: 62; 2: 1; 5: 1 |

This is **sample-degenerate**, not literally near-zero variance over the full
dataset: the full variance is 1.104608. The zero mismatch in the 64-row causal
rebuild reflects the sample's two non-zero values and does not establish
admissibility. The feature consumes prior campaign history (OPEN-TIME) and a
prior loss-streak indicator based on realised netProfit or its
profit+commission+swap fallback and close-time update gate (CLOSE-TIME), so it
remains contaminated under the field-class audit.

## POST-HOC COMPLIANCE SENSITIVITY (not pre-freeze search)

These items were run after the frozen V2 submission or as compliance follow-up.
They are not added to the pre-freeze denominator m=4,626.

| Post-hoc item | What was recorded | Included in pre-freeze m? |
|---|---|---:|
| Drop-2-contaminated ablation | A distinct two-feature contamination-remediation ablation was requested, but no committed artifact, report, or branch result for that exact ablation is present in the audited Git refs. No number is fabricated. | No |
| Drop-challenge_type ablation | Branch-only diagnostic; acted set changed 177 → 188; ablation EW -0.8740/lot, SW -34.6854/lot (audit/challenge_type_deconfound.md). | No |
| Fixed-acted-set counterfactual | Original 177 rows held fixed; challenge-type score contribution set to zero without refit/reselection; EW remained 10.4327/lot, SW -33.8486/lot, delta 0.0000 because realised outcomes were unchanged. | No |
| V3 clean-9 refit | Branch stage3-tp-remediation, clean-9 artifact; OOS acted 6/6,583, EW 201.0611/lot, SW -8.0403/lot, dollar total +$292.07 with C66 excluded (report/is_oos_gap.md). | No |

The challenge-type ablation, fixed-set counterfactual, and V3 refit are
post-hoc compliance sensitivities. They must not be described as pre-registered
search results or used to shrink the corrected denominator.

## Git-history limits and provenance

The repository has only one commit containing the complete Stage 3 source and
trial report: 06efdd5 on 2026-08-21. dd51d7a only reorganizes the PDF/report
submission. There is no finer-grained commit history showing an uncommitted
alternative estimator or omitted threshold sweep.

- Ridge is the only evidenced predictive estimator family.
- The 13 alpha values, 601 score thresholds, 228 conditional candidates, 770
  bucket candidates, 714 amount cutoffs, and 406 correlation comparisons are
  counted from committed code or committed selection documentation.
- The seven older prune names are counted because the committed changelog
  explicitly says they were screened and pruned, but they have no standalone
  p-values in the frozen reports.
- No unseen threshold or estimator is inferred from prose alone.

**Final one-line verdict: 4,626 pre-freeze search attempts; 101 was only the
named endpoint ledger, and 0 of 90 scalar outcome tests survive BH at the
corrected denominator.**
