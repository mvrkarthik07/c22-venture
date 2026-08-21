# FEATURES.md — Stage 2 Feature Specification (FROZEN 2026-07)
# Every feature cites its Stage 1 evidence. Do not add features not listed here.
# All features are CAUSAL: computed from information available strictly BEFORE
# the position's outcome is known (i.e., at open time, before updating state).

## Changelog
- 2026-07-28: C22 confirmed a fixed `STARTING_BALANCE = 5000.00` for every
  account. The frozen Family D features therefore remain `pnl_pct` and
  `dd_from_peak_pct`, now normalized on `$5,000` instead of the earlier
  assumed `$10,000`. Companion dollar-form columns
  (`cum_pnl_usd`, `dd_from_peak_usd`) are also exported. Because the balance
  is global and constant, the dollar and percent forms are monotone rescalings
  of one another, so rank order and threshold-selected row membership are
  invariant. Reporting now uses the parameterized helper
  `reverse_profit_per_lot(gross_loss_per_lot, cost_per_lot=7.00)`.
- 2026-07-25: pinned the clustered-bootstrap reporting configuration to
  `seed=7` and `n_boot=2000` to preserve Stage 1 confidence-interval
  reproducibility; documented explicitly after the CI diagnosis audit.
- 2026-07-25: applied the pre-committed Stage 2.1 correlation prune on
  training folds only. Dropped `entry_gap_sec` (vs `log_dt_close`) and
  `is_cold_start` (vs `prior_campaigns`) under the unchanged `|rho| > 0.90`
  rule; retained moderate `0.74-0.87` pairs for regularization.
- 2026-07-25: added Family G cross-campaign trader memory
  (`trader_prior_tilt`, `trader_prior_sl_discipline`,
  `trader_prior_survival`, `prior_campaigns_x_loss_streak_ge_2`,
  `is_cold_start`) with campaign-boundary-only updates and
  empirical-Bayes cold-start shrinkage.
- 2026-07-25: added Family F mechanism channels (`sl_widening_delta`,
  `entry_gap_sec`, `same_direction_reentry`, `size_delta_ratio`) with
  entry-time-only semantics and fold-fitted clipping for `entry_gap_sec`.
- 2026-07-12: pruned redundant or deterministic features after Stage 2 validation:
  `dist_to_target`, `dist_to_dd_limit`, `streak_age_s`, `lot_ratio_vs_avg`,
  `size_pctile`, `is_repeat`, `gap_compression`.
- 2026-07-12: walk-forward disjointness updated to traderKey-first purging, with
  `ipClusterId` purging retained only for the 7 CHECK 7 synchronous
  `(ipClusterId, campaignId)` pairs.

## Architecture requirement
Implement a `TraderState` class in a new file `features.py`:

    class TraderState:
        def __init__(self, config): ...
        def compute_features(self, position) -> dict   # BEFORE outcome known
        def update(self, position) -> None             # AFTER outcome known

    One TraderState instance per (campaignId, accountId).
    Batch pipeline: iterate positions in openDateTime order, call
    compute_features() then update(). The SAME class must work when fed
    positions one at a time (streaming) — no batch-only shortcuts, no
    references to future rows, no use of aggregate statistics computed
    over the full account history.

## Family A — Streak & momentum (evidence: memo §3, confirmed triggers 1-2)
A1 loss_streak       int, consecutive positions with netProfit < 0 before this one
A2 win_streak        int, consecutive netProfit > 0
A3 pnl_ewm           exponentially weighted sum of past netProfit, alpha=0.3,
                     computed recursively: ewm = 0.3*last_netProfit + 0.7*ewm_prev

## Family B — Sizing behavior (evidence: memo §4 quartile monotonicity)
B1 lot_zscore        (amount - running_mean) / running_std of prior amounts;
                     NaN if fewer than 3 prior trades
B2 amount            raw lot size (pass-through)
B3 size_after_loss_delta  amount - mean(amounts of trades BEFORE the current
                     loss streak began); NaN if loss_streak == 0 or no
                     pre-streak trades. Positive = escalator, negative = shrinker.

## Family C — Risk discipline (evidence: memo §3 no-SL tail finding)
C1 has_sl            bool, slPrice not null
C2 has_tp            bool, tpPrice not null
C3 sl_distance_pct   abs(openPrice - slPrice)/openPrice if has_sl else NaN
C4 sl_usage_rate_5   fraction of last 5 prior positions with SL set;
                     NaN if fewer than 3 prior
C5 manual_exit_rate_5  fraction of last 5 prior positions with exit_type
                     == 'manual'; NaN if fewer than 3 prior

## Family D — Session & pressure state (evidence: memo §1-2, CLAUDE.md)
D1 pnl_pct           cumulative netProfit / 5000.00 before the current trade
D2 dd_from_peak_pct  (running peak equity - current equity) / 5000.00 before
                     the current trade
D3 trade_index       1-based position count within account-campaign
D4 log_dt_close      ln(1 + seconds since last close); NaN if first trade
D5 trades_per_hour   trade_index / max(hours since first open, 1/60)
   NOTE: session_pct and trades_remaining_est are EXCLUDED (lookahead).

Rationale:
With a confirmed global starting balance of `$5,000`, `pnl_pct` and
`dd_from_peak_pct` are now directly computable without assumption. Their
companion dollar forms are monotone rescalings, so rank order and any
train-selected thresholding logic are unchanged between the two parameterizations.

Companion balance-derived exports:
`cum_pnl_usd` and `dd_from_peak_usd` are also exported as causal pre-trade
state columns, plus `breach_proximity_usd = 200 - current_drawdown_usd` and
`target_proximity_usd = 400 - current_profit_usd`. These are append-only
analysis columns, not part of the frozen v2.1 28.

## Family E — Identity & context (account-level; evidence: memo §2, §2.1)
E1 prior_campaigns   number of DISTINCT campaigns with campaignId < current
                     in which this traderKey has trades. Causal across
                     campaigns by construction. 0 if first appearance or
                     traderKey missing.
E2 shared_ip         sharedIpFlag from traders_sanitized.csv (bool)
E3 ip_cluster_size   count of ACTIVE accounts sharing ipClusterId across
                     the corpus (static join; acceptable — infrastructure
                     property, not outcome-dependent)
E4 challenge_type    challenge_type_id, categorical, 'unknown' if missing
E5 gold_vol_prev_day realized daily range %: (high-low)/close of XAUUSD on
                     the calendar day BEFORE campaignDate. Source: any free
                     daily OHLC (e.g. stooq.com xauusd daily csv). PRIOR day
                     only — same-day vol is lookahead.

## Family F — Mechanism channels (evidence: exploratory, entry-time observable)
F1 sl_widening_delta current `sl_distance_pct` minus the rolling median of
                     prior `sl_distance_pct` values for the same
                     `(campaignId, accountId)`. Requires at least 3 prior
                     SL-set positions; otherwise NaN. If the current position
                     has no SL, emit NaN.
F2 entry_gap_sec     seconds between `openDateTime(t)` and
                     `closeDateTime(t-1)` for the same `(campaignId, accountId)`.
                     First position of a campaign is NaN. Upper-tail clipping
                     is allowed only via a fitted parameter estimated as the
                     99th percentile on training folds; never hardcode it and
                     never fit it on validation/test rows.
F3 same_direction_reentry
                     `1` iff `side(t) == side(t-1)` and position `t-1` had
                     `netProfit < 0`; otherwise `0`. First position of a
                     campaign is `0`.
F4 size_delta_ratio  `amount(t) / amount(t-1)` for the same
                     `(campaignId, accountId)`. First position of a campaign
                     is NaN. If `amount(t-1) == 0`, emit NaN.

Rationale:
These channels target execution mechanics rather than outcome summaries:
whether a trader re-enters quickly, repeats direction after a loss, widens
their stop relative to their own recent baseline, or changes size versus the
immediately prior attempt.

Lookahead classification:
All Family F features are entry-time observable. They may use the current
row's open-time fields plus state accumulated from positions `1..t-1` only.
They must not use hold duration, MAE, realized excursion, close price, or the
profit of position `t`.

NaN semantics:
NaNs are propagated as missing information and must not be filled in the
feature builder. For `sl_widening_delta`, insufficient prior SL history or a
missing current SL yields NaN. For `entry_gap_sec` and `size_delta_ratio`, the
first position of a campaign yields NaN; `size_delta_ratio` is also NaN when
the prior amount is zero.

## Family G — Cross-Campaign Trader Memory (evidence: confirmed experience gradient)
Architecture:
Implement a second state object, `TraderHistory`, keyed by `traderKey` and
updated only at campaign boundaries. For campaign `c`, Family G features must
use state accumulated from campaigns with `campaignId < c` only. Never read
same-campaign rows, and never read future campaigns. Code should assert that
no stored campaign number is `>= current campaignId`.

G1 trader_prior_tilt
                     EWMA, halflife `= 2` campaigns, of the trader's realized
                     mean `gross_loss_per_lot` on positions where
                     `loss_streak >= 2`, across prior campaigns only.
G2 trader_prior_sl_discipline
                     mean `sl_distance_pct` across the trader's prior campaigns.
G3 trader_prior_survival
                     mean active span across prior campaigns,
                     `(last_close - first_open)` in hours, divided by `1.99`
                     (the population median active span).
G4 prior_campaigns_x_loss_streak_ge_2
                     explicit interaction term:
                     `prior_campaigns * 1(loss_streak >= 2)`.
G5 is_cold_start     boolean companion column: `True` when the trader has zero
                     prior campaigns in history, else `False`.

Cold-start shrinkage:
For the three trader-history estimates above, use empirical-Bayes shrinkage
toward a population mean computed on TRAINING FOLDS ONLY:

    value = w * trader_estimate + (1 - w) * population_mean
    w = n / (n + k)

`k` is a fitted hyperparameter, default `5` for the first run, and must be
tuned inside training folds only. Do not fit `k` globally. Do not impute zero:
a first-campaign trader is not a zero-tilt trader.

For `trader_prior_tilt`, `n` is the number of prior positions with
`loss_streak >= 2`. For `trader_prior_sl_discipline`, `n` is the number of
prior positions with non-null `sl_distance_pct`. For
`trader_prior_survival`, `n` is the number of prior positions contained in the
campaign-span estimates.

Lookahead classification:
Family G is entry-time observable because it is loaded once per campaign from
strictly lower campaign IDs, then held constant within the campaign while
`TraderState` advances position by position.

NaN semantics:
Do not fill NaNs inside feature engineering. The cold-start path should emit a
shrunk value using the train-fold population mean plus the explicit
`is_cold_start` flag, rather than replacing missing trader memory with zero.

Effective sample size note:
These are trader-level features. Their effective sample size is the number of
repeat traders in the primary era, not the number of positions (`~338` repeat
traders out of `496` active accounts, versus `6,582` positions). This is why
the family is capped at 3 trader-memory channels plus the explicit promotion.

## Analysis Reproducibility
Clustered bootstrap reporting in `pipeline.py` is pinned to the Stage 1
configuration: `seed=7` and `n_boot=2000`. Those values are analysis settings,
not feature definitions, but they are documented here because several headline
confidence intervals in the memo and downstream audits depend on them.

## Final Frozen v2.1 List (28)
Retained frozen features:
`loss_streak`, `win_streak`, `pnl_ewm`,
`lot_zscore`, `amount`, `size_after_loss_delta`,
`has_sl`, `has_tp`, `sl_distance_pct`, `sl_usage_rate_5`, `manual_exit_rate_5`,
`pnl_pct`, `dd_from_peak_pct`, `trade_index`, `log_dt_close`, `trades_per_hour`,
`prior_campaigns`, `shared_ip`, `ip_cluster_size`, `challenge_type`, `gold_vol_prev_day`,
`sl_widening_delta`, `same_direction_reentry`, `size_delta_ratio`,
`trader_prior_tilt`, `trader_prior_sl_discipline`, `trader_prior_survival`,
`prior_campaigns_x_loss_streak_ge_2`.

Dropped by the unchanged `|rho| > 0.90` prune rule:
- `entry_gap_sec` dropped in favor of older frozen `log_dt_close` because
  coverage was within 2 percentage points and Family D is older than Family F.
- `is_cold_start` dropped in favor of older frozen `prior_campaigns` because
  coverage was within 2 percentage points and Family E is older than Family G.

## Targets (never features)
T1 gross_loss_per_lot   -profit/amount
T2 clears_hurdle        gross_loss_per_lot > cost_per_lot (binary alt-target)

## Reporting Unit
For analysis and validation reporting after 2026-07-28, use:

    reverse_profit_per_lot(gross_loss_per_lot, cost_per_lot=7.00)
        = gross_loss_per_lot - cost_per_lot

This is a reporting transformation, not a feature.

## Unit tests required (tests/test_features.py)
Construct a synthetic 6-trade sequence with hand-computed expected values:
  trades: [win +10 @0.5 lots, loss -20 @0.5, loss -30 @1.0,
           trade @0.2 (features asserted here), win +5 @0.5, loss -10 @2.0]
  Assert at trade 4: loss_streak==2, size_after_loss_delta==0.2-0.5,
  sl_usage_rate_5 per constructed SLs, etc.
  Extend the truncated-sequence identity assertions to cover all Family F
  outputs as well.
  Add a campaign-boundary leakage test for Family G: construct one trader
  appearing in 3 campaigns and verify campaign-2 history features depend only
  on campaign-1 data, not on same-campaign rows or campaign 3.
  Assert NO feature at trade k changes if trades k+1..n are modified
  (mechanical lookahead test: compute features on truncated vs full
  sequence, assert identical).

## Walk-forward harness (splits.py)
Function make_folds(features_df, n_folds=4):
  - primary era only (campaignId 53-65)
  - campaign-blocked, chronological: e.g. train {53-56}, val {57-58}, then
    expanding-window forward
  - DISJOINTNESS: any traderKey appearing in a train fold is REMOVED from that
    fold's validation set
  - EXCEPTION: retain ipClusterId purging only for the 7 CHECK 7 synchronous
    pairs: (1,63), (8,63), (21,54), (31,57), (31,59), (42,59), (42,60)
  - print fold attrition, plus the broad-rule traderKey-only/ipClusterId-only/
    both decomposition for audit
  - returns list of (train_idx, val_idx); no model fitting in this stage
