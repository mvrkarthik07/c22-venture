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