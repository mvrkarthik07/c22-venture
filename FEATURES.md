# FEATURES.md — Stage 2 Feature Specification (FROZEN 2026-07)
# Every feature cites its Stage 1 evidence. Do not add features not listed here.
# All features are CAUSAL: computed from information available strictly BEFORE
# the position's outcome is known (i.e., at open time, before updating state).

## Changelog
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
D1 pnl_pct           cumulative netProfit / start_balance
D2 dd_from_peak_pct  (peak_equity - equity) / start_balance
D3 trade_index       1-based position count within account-campaign
D4 log_dt_close      ln(1 + seconds since last close); NaN if first trade
D5 trades_per_hour   trade_index / max(hours since first open, 1/60)
   NOTE: session_pct and trades_remaining_est are EXCLUDED (lookahead).

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

## Targets (never features)
T1 gross_loss_per_lot   -profit/amount
T2 clears_hurdle        gross_loss_per_lot > 7.00 (binary alt-target)

## Unit tests required (tests/test_features.py)
Construct a synthetic 6-trade sequence with hand-computed expected values:
  trades: [win +10 @0.5 lots, loss -20 @0.5, loss -30 @1.0,
           trade @0.2 (features asserted here), win +5 @0.5, loss -10 @2.0]
  Assert at trade 4: loss_streak==2, size_after_loss_delta==0.2-0.5,
  sl_usage_rate_5 per constructed SLs, etc.
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
