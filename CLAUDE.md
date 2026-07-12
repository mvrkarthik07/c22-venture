# C22 veNTUre — behavioral fade analysis
Solo entry, NTU veNTUre challenge. EDA memo due 24 Jul. See docs PDFs in repo root.

## Data (NDA + PDPA — proprietary)
- datasets/user_trades/: per-campaign XAUUSD fill-level csvs (C33-C66)
- datasets/user_data/: per-campaign registrant files — CONTAIN RAW PII
  (email, ip_address, telegram_username). NEVER read raw values into
  outputs, logs, or commits. Sanitize via sanitize_traders() only.
  traders_sanitized.csv is the only permitted derived traders file.
- NEVER commit datasets/, features.csv, traders_sanitized.csv (gitignore them).

## Established facts (do not re-derive; do not contradict without evidence)
- Fills collapse to positions on (campaignId, positionId); 46,520 -> 7,277
- reverseProfit = -profit - 7.00*amount exactly (C41 test campaign: 6.50).
  Fade hurdle = $7/lot. Model target: gross_loss_per_lot = -profit/amount
- Era break at C53: participation ~5x, SL usage -25pp, gross skill collapse.
  Primary era = C53-C65 (90% of volume). C33-C52 = prelude, report separately
- Campaigns 41, 66 are n=1 test runs — exclude
- Registration cap 500/campaign; ~6% activate. Trader stats must use ACTIVE traders
- Confirmed trigger: loss_streak>=2 -> E[loss/lot]~40, 95% CI [11.4,70.2]
  (trader-clustered bootstrap). Other 9 conditions: positive, not individually sig
- no-SL edge is tail-driven (top 1% of fades = 276% of P&L) — frame accordingly
- Suspected: amount negatively correlated with loss/lot (unverified — check first)

## Methodology constraints (non-negotiable)
- All state features causal (as-of open time). session_pct is descriptive-only
- CV: walk-forward by campaign within C53-C65 AND traderKey-disjoint splits
  (2,506 registrant-level repeaters)
- Condition list in condition_masks() is pre-registered/frozen; new = exploratory
- Cluster bootstrap by traderKey (fallback campaignId_accountId), never by trade

## Stage 2 status (12 Jul 2026)
- `features.py` implemented with streaming-safe `TraderState`; tests in
  `tests/test_features.py` include the mechanical lookahead identity check
- `build_features.py` builds `features_v2.csv` from trade loaders in
  `pipeline.py`, joins trader metadata from `traders_sanitized.csv` only,
  and caches prior-day XAUUSD OHLC in `cache/xauusd_daily_ohlc.csv`
- `validate_features.py` writes `reports/stage2_validation.md`
- `splits.py` now uses traderKey purging as the main disjointness rule, with
  IP-cluster purging retained only for the 7 CHECK 7 synchronous pairs:
  `(1,63)`, `(8,63)`, `(21,54)`, `(31,57)`, `(31,59)`, `(42,59)`, `(42,60)`

## Retained feature set (21)
- Removed under redundancy/deterministic pruning:
  `dist_to_target`, `dist_to_dd_limit`, `streak_age_s`, `lot_ratio_vs_avg`,
  `size_pctile`, `is_repeat`, `gap_compression`
- Remaining moderate correlations above `|rho| > 0.70`:
  `loss_streak` vs `dd_from_peak_pct` (`0.7383`),
  `pnl_ewm` vs `pnl_pct` (`0.8537`),
  `lot_zscore` vs `size_after_loss_delta` (`0.8612`)

## Current validation snapshot
- Primary-era sample: `6,582` positions, `496` active accounts
- Walk-forward purged validation rows by fold: `371`, `454`, `464`, `901`
  with row attrition `60.9%`, `56.1%`, `52.3%`, `43.3%`
- Broad-rule purge decomposition: no traderKey-only overlaps; overlaps are
  either IP-only or both traderKey and IP cluster
- `gold_vol_prev_day` in `features_v2.csv` has `0.0%` NaN rate
- `trades_per_hour > 60`: `176` positions across `142` distinct
  `(campaignId, accountId)` pairs; treat as possible automation signal,
  not a concluded rule violation

## Drafting artifacts
- `stage2_brief.tex` exists and includes Appendix A/B/C content sourced from
  `FEATURES.md` and `reports/stage2_validation.md`
- TeX source row-count check passed for Appendix B (`74` rows), but local
  XeLaTeX compilation is still blocked because `xelatex` is not installed
