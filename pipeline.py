"""
C22 veNTUre — Stage 1 pipeline (v3)
Batch ingest (C33-C66, two schema eras) -> PII sanitization with hard asserts
-> position-level dedupe -> causal behavioral state vectors -> rule predicates
-> conditional reverseProfit analysis -> cost decomposition
-> clustered bootstrap CIs -> within-campaign robustness.

Usage:
    python pipeline.py ./datasets --balance 10000 --era primary --out features.csv

Expects:
    <folder>/user_trades/Campaign NN Data <date> XAUUSD only (1D).csv
    <folder>/user_data/Campaign NN Data <date> Traders only (1D).xlsx|csv

All state features are computed strictly as-of position open time (no
lookahead). The same update logic ports to the Stage-4 replay engine.
"""

import argparse
import glob
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
SLTP_TOL = 1.0          # gold points; calibrate from residual histogram
IDEA_GAP_MIN = 3.0      # trade-idea grouping: >3 min after a close = new idea
GRID_WINDOW_S = 30      # grid rule: 3+ same-direction entries within 30s, worse price
REVENGE_FAST_S = 60     # "fast re-entry after loss" threshold
WINDOW_HOURS = 24
EXPECTED_CAMPAIGNS = set(range(33, 67))
N_BOOT = 2000
BOOT_SEED = 7
HURDLE = 7.0
EXCLUDE_CAMPAIGNS = {41, 66}

# Canonical column mapping for traders files (two known schema eras).
CANON = {
    "ACCOUNT": "account", "account": "account",
    "EMAIL": "email", "email": "email",
    "IP ADDRESS": "ip_address", "ip_address": "ip_address",
    "telegram_username": "telegram_username",
    "challenge_type_id": "challenge_type_id",
}
PII_PATTERNS = ("email", "ip_address", "telegram", "username", "phone", "name")


# ----------------------------------------------------------------------
# 0. Ingest
# ----------------------------------------------------------------------
def _campaign_meta(filename: str):
    m = re.search(r"Campaign\s+(\d+)\s+Data\s+(.+?)\s+(?:XAUUSD|Traders)", filename)
    if not m:
        raise ValueError(f"Unparseable filename: {filename}")
    return int(m.group(1)), pd.to_datetime(m.group(2), dayfirst=True)


def _skip(path: str) -> bool:
    name = Path(path).name
    return "__MACOSX" in path or name.startswith("._")


def load_all_trades(folder: str) -> pd.DataFrame:
    paths = sorted(p for p in glob.glob(
        f"{folder}/**/Campaign*XAUUSD*only*.csv", recursive=True) if not _skip(p))
    if not paths:
        raise FileNotFoundError(f"No trade CSVs found under {folder}")
    frames, seen = [], set()
    for p in paths:
        camp_id, camp_date = _campaign_meta(Path(p).name)
        df = pd.read_csv(p, parse_dates=["openDateTime", "closeDateTime"])
        df["campaignId"] = camp_id
        df["campaignDate"] = camp_date
        frames.append(df)
        seen.add(camp_id)
    if EXPECTED_CAMPAIGNS - seen:
        print(f"WARNING: missing campaigns: {sorted(EXPECTED_CAMPAIGNS - seen)}")
    if seen - EXPECTED_CAMPAIGNS:
        print(f"WARNING: unexpected campaigns: {sorted(seen - EXPECTED_CAMPAIGNS)}")
    out = pd.concat(frames, ignore_index=True)
    print(f"Trades: {len(out)} fill rows across {len(seen)} campaigns")

    # positionId collision diagnostic (was 0 on first run; keep as guard)
    collisions = (out.groupby("positionId")["campaignId"].nunique() > 1).sum()
    print(f"positionIds spanning >1 campaign: {collisions}")
    if collisions:
        print("NOTE: composite key (campaignId, positionId) in use — safe either way")
    return out


def load_all_traders(folder: str) -> pd.DataFrame:
    paths = sorted(p for p in glob.glob(
        f"{folder}/**/Campaign*Traders*", recursive=True) if not _skip(p))
    if not paths:
        print("WARNING: no traders files found — proceeding without trader metadata")
        return pd.DataFrame()
    frames = []
    for p in paths:
        camp_id, _ = _campaign_meta(Path(p).name)
        reader = pd.read_excel if p.lower().endswith((".xlsx", ".xls")) else pd.read_csv
        df = reader(p)
        # Canonicalize BEFORE concat so both schema eras align on one column set
        df.columns = [CANON.get(c.strip(), c.strip().lower().replace(" ", "_"))
                      for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated()]
        unknown = set(df.columns) - set(CANON.values())
        if unknown:
            print(f"NOTE {Path(p).name}: extra columns {sorted(unknown)}")
        df["campaignId"] = camp_id
        frames.append(df)
    t = pd.concat(frames, ignore_index=True)
    return sanitize_traders(t)


def sanitize_traders(t: pd.DataFrame) -> pd.DataFrame:
    """Hash email -> traderKey, flag shared IPs, drop ALL PII, hard-assert clean."""
    if "email" in t.columns:
        valid = t["email"].notna() & (t["email"].astype(str).str.strip() != "") \
                & (t["email"].astype(str).str.lower() != "nan")
        t.loc[valid, "traderKey"] = (
            t.loc[valid, "email"].astype(str).str.lower().str.strip()
            .map(lambda e: hashlib.sha256(e.encode()).hexdigest()[:12]))
        print(f"Rows without usable email: {(~valid).sum()} of {len(t)} "
              f"(fall back to campaign+account cluster)")
        rep = t.loc[valid].groupby("traderKey")["campaignId"].nunique()
        print(f"Traders: {t['traderKey'].nunique()} unique, "
              f"{(rep > 1).sum()} appear in >1 campaign (split CV by traderKey)")


    if "ip_address" in t.columns and "account" in t.columns:
        counts = t.groupby("ip_address")["account"].nunique()
        t["sharedIpFlag"] = t["ip_address"].map(counts) > 1
        print(f"Shared-IP: {(counts > 1).sum()} IPs on >1 account "
              f"(max accounts on one IP: {counts.max()})")
        # anonymous cluster id — dense integer, not a hash of the IP (IPv4
        # space is brute-forceable). Unlinkable to the raw IP once dropped.
        t["ipClusterId"] = t["ip_address"].factorize()[0]

    pii_cols = [c for c in t.columns if any(p in c.lower() for p in PII_PATTERNS)]
    t = t.drop(columns=pii_cols)

    leftover = [c for c in t.columns if any(p in c.lower() for p in PII_PATTERNS)]
    assert not leftover, f"PII survived sanitization: {leftover}"
    assert not t.columns.duplicated().any(), "duplicate columns after sanitize"
    print(f"Sanitized traders columns: {list(t.columns)}")
    return t


# ----------------------------------------------------------------------
# 1. Position-level dedupe (rows are close-fills; collapse partial closes)
# ----------------------------------------------------------------------
def to_positions(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["profit", "reverseProfit", "netProfit", "commission", "swap",
              "amount", "openPrice", "closePrice", "slPrice", "tpPrice",
              "durationSec", "lotSize"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    n_fills = len(df)
    keys = ["campaignId", "positionId"]
    agg = {
        "campaignDate": "first", "accountId": "first", "instrument": "first",
        "lotSize": "first", "openOrderId": "first", "userGroupId": "first",
        "side": "first", "openDateTime": "first", "closeDateTime": "max",
        "openPrice": "first",
        "profit": "sum", "reverseProfit": "sum", "netProfit": "sum",
        "commission": "sum", "swap": "sum", "amount": "sum",
        "slPrice": "first", "tpPrice": "first",
    }
    g = df.sort_values("closeDateTime").groupby(keys, as_index=False)
    pos = g.agg(agg)

    wp = df.assign(w=df["closePrice"] * df["amount"]).groupby(keys)
    wavg = (wp["w"].sum() / wp["amount"].sum()).rename("closePrice").reset_index()
    pos = pos.merge(wavg, on=keys)
    pos["n_fills"] = df.groupby(keys).size().values
    pos["durationSec"] = (pos["closeDateTime"] - pos["openDateTime"]).dt.total_seconds()

    print(f"fills: {n_fills} -> positions: {len(pos)} "
          f"(partial-close positions: {(pos['n_fills'] > 1).sum()})")
    return pos.sort_values(["campaignId", "accountId", "openDateTime"]).reset_index(drop=True)


# ----------------------------------------------------------------------
# 2. Exit-type inference (schema has no order-type field)
# ----------------------------------------------------------------------
def infer_exit_type(pos: pd.DataFrame, tol: float = SLTP_TOL) -> pd.Series:
    d_sl = (pos["closePrice"] - pos["slPrice"]).abs()
    d_tp = (pos["closePrice"] - pos["tpPrice"]).abs()
    exit_type = pd.Series("manual", index=pos.index)
    exit_type[d_sl <= tol] = "sl_hit"
    exit_type[(d_tp <= tol) & ~(d_sl <= tol)] = "tp_hit"
    return exit_type


# ----------------------------------------------------------------------
# 3. Grid predicate: 3+ same-direction entries within 30s at worse price
# ----------------------------------------------------------------------
def flag_grid(pos: pd.DataFrame) -> pd.Series:
    flags = pd.Series(False, index=pos.index)
    for _, g in pos.groupby(["campaignId", "accountId"]):
        g = g.sort_values("openDateTime")
        for i in range(2, len(g)):
            w = g.iloc[i - 2:i + 1]
            if (w["side"].nunique() == 1
                    and (w["openDateTime"].iloc[-1] - w["openDateTime"].iloc[0]).total_seconds() <= GRID_WINDOW_S):
                worse = (w["openPrice"].is_monotonic_decreasing if w["side"].iloc[0] == "BUY"
                         else w["openPrice"].is_monotonic_increasing)
                if worse:
                    flags.loc[w.index] = True
    return flags


# ----------------------------------------------------------------------
# 4. Per-account event walk: causal state vector at each open
# ----------------------------------------------------------------------
def build_state_vectors(pos: pd.DataFrame, start_balance: float) -> pd.DataFrame:
    rows = []
    for (camp, acct), g in pos.groupby(["campaignId", "accountId"], sort=False):
        g = g.sort_values("openDateTime").reset_index(drop=True)
        t0 = g.loc[0, "openDateTime"]
        t_last_close = g["closeDateTime"].max()
        session_span_s = max((t_last_close - t0).total_seconds(), 1.0)
        window_end = t0 + pd.Timedelta(hours=WINDOW_HOURS)
        n_trades_total = len(g)

        cum_pnl, peak_equity, loss_streak = 0.0, start_balance, 0
        amounts_so_far = []
        last_close_t = last_net = last_side_after_sl = None

        # ---- causal idea grouping (3-min rule) ----
        idea_ids, idea_id = [], 0
        idea_open_t, prev_side, last_close_for_idea = None, None, None
        for _, r in g.iterrows():
            new_idea = True
            if idea_open_t is not None:
                within_3min = (r["openDateTime"] - idea_open_t).total_seconds() <= IDEA_GAP_MIN * 60
                after_close_gap = (
                    last_close_for_idea is not None
                    and (r["openDateTime"] - last_close_for_idea).total_seconds() > IDEA_GAP_MIN * 60)
                if within_3min and r["side"] == prev_side and not after_close_gap:
                    new_idea = False
            if new_idea:
                idea_id += 1
                idea_open_t = r["openDateTime"]
            idea_ids.append(idea_id)
            prev_side = r["side"]
            last_close_for_idea = r["closeDateTime"]
        g["ideaId"] = idea_ids

        for i, r in g.iterrows():
            t = r["openDateTime"]
            hrs_elapsed = (t - t0).total_seconds() / 3600
            dt_since_close = ((t - last_close_t).total_seconds()
                              if last_close_t is not None else np.nan)
            avg_amt = np.mean(amounts_so_far) if amounts_so_far else np.nan
            lot_ratio = r["amount"] / avg_amt if amounts_so_far else np.nan

            equity = start_balance + cum_pnl
            dd_from_peak = (peak_equity - equity) / start_balance
            pnl_pct = cum_pnl / start_balance

            hi = max(amounts_so_far) if amounts_so_far else np.nan
            lo = min(amounts_so_far) if amounts_so_far else np.nan
            atlsr_ratio = (max(hi, r["amount"]) / min(lo, r["amount"])
                           if amounts_so_far else np.nan)

            rows.append({
                "campaignId": camp, "accountId": acct,
                "positionId": r["positionId"],
                "openDateTime": t, "side": r["side"], "amount": r["amount"],
                "ideaId": r["ideaId"],
                # --- state features (causal) ---
                "hrs_elapsed": hrs_elapsed,
                "hrs_remaining_24h": max((window_end - t).total_seconds() / 3600, 0),
                # session-relative clock: position within the account's OWN
                # active span (median span ~2h; 24h clock is mostly dead weight).
                # Uses final span => descriptive/EDA feature only, NOT causal —
                # exclude from any predictive model or replace with a causal
                # proxy (e.g. trades-so-far vs typical pace) at modeling time.
                "session_pct": min((t - t0).total_seconds() / session_span_s, 1.0),
                "trade_index": i + 1,
                "trades_remaining_est": n_trades_total - (i + 1),   # descriptive only
                "pnl_pct": pnl_pct, "dd_from_peak_pct": dd_from_peak,
                "dist_to_target": 0.08 - pnl_pct,
                "dist_to_dd_limit": 0.04 - dd_from_peak,
                "loss_streak": loss_streak,
                "lot_ratio_vs_avg": lot_ratio,
                "atlsr_ratio_if_filled": atlsr_ratio,
                "rule_b_breach_if_filled": bool(lot_ratio > 2.5) if amounts_so_far else False,
                "dt_since_last_close_s": dt_since_close,
                "fast_reentry_after_loss": bool(
                    last_net is not None and last_net < 0
                    and not np.isnan(dt_since_close) and dt_since_close <= REVENGE_FAST_S),
                "same_side_after_sl": bool(
                    last_side_after_sl is not None and r["side"] == last_side_after_sl),
                "has_sl": pd.notna(r["slPrice"]), "has_tp": pd.notna(r["tpPrice"]),
                # --- outcomes (targets only, NEVER model features) ---
                "netProfit": r["netProfit"], "profit": r["profit"],
                "reverseProfit": r["reverseProfit"],
                "exit_type": r["exit_type"], "durationSec": r["durationSec"],
                "gross_loss_per_lot": -r["profit"] / r["amount"] if r["amount"] else np.nan
            })

            cum_pnl += r["netProfit"]
            peak_equity = max(peak_equity, start_balance + cum_pnl)
            loss_streak = loss_streak + 1 if r["netProfit"] < 0 else 0
            amounts_so_far.append(r["amount"])
            last_close_t = r["closeDateTime"]
            last_net = r["netProfit"]
            last_side_after_sl = r["side"] if r["exit_type"] == "sl_hit" else None

    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 5. Era filters + derived analysis columns
# ----------------------------------------------------------------------
def era_mask(campaigns: pd.Series, era: str) -> pd.Series:
    base = ~campaigns.isin(EXCLUDE_CAMPAIGNS)
    if era == "primary":
        return base & (campaigns >= 53)
    if era == "prelude":
        return base & (campaigns < 53)
    if era == "all":
        return base
    raise ValueError(f"Unknown era: {era}")


def compute_small_size_threshold(sv: pd.DataFrame) -> float:
    primary = sv.loc[era_mask(sv["campaignId"], "primary"), "amount"].dropna()
    if primary.empty:
        raise ValueError("No primary-era positions available to compute small_size_flag")
    _, bins = pd.qcut(primary, 4, retbins=True, duplicates="drop")
    if len(bins) < 2:
        raise ValueError("Unable to derive primary-era Q1 upper edge for amount")
    return float(bins[1])


def add_analysis_columns(sv: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    sv = sv.copy()
    sv["est_cost_gross"] = -(sv["reverseProfit"] + sv["profit"])
    sv["est_cost_net"] = -(sv["reverseProfit"] + sv["netProfit"])
    small_size_edge = compute_small_size_threshold(sv)
    sv["small_size_flag"] = sv["amount"] <= small_size_edge
    return sv, small_size_edge


# ----------------------------------------------------------------------
# 6. Conditions + fade table
# ----------------------------------------------------------------------
def condition_masks(sv: pd.DataFrame) -> dict:
    return {
        "baseline (all trades)": pd.Series(True, index=sv.index),
        "no SL set": ~sv["has_sl"],
        "loss_streak >= 2": sv["loss_streak"] >= 2,
        "loss_streak>=2 AND small_size_flag":
            (sv["loss_streak"] >= 2) & sv["small_size_flag"],
        "loss_streak >= 3": sv["loss_streak"] >= 3,
        "same side after SL hit": sv["same_side_after_sl"],
        "fast re-entry after loss (<=60s)": sv["fast_reentry_after_loss"],
        "size escalation (lot_ratio > 1.5)": sv["lot_ratio_vs_avg"] > 1.5,
        "near rule-B cliff (lot_ratio > 2.0)": sv["lot_ratio_vs_avg"] > 2.0,
        "deep drawdown (dd > 2%)": sv["dd_from_peak_pct"] > 0.02,
        "late session (session_pct > 0.75)": sv["session_pct"] > 0.75,
        "late + underwater": (sv["session_pct"] > 0.75) & (sv["pnl_pct"] < 0),
        "grid-flagged": sv.get("grid_flag", pd.Series(False, index=sv.index)),
    }


def conditional_fade_analysis(sv: pd.DataFrame) -> pd.DataFrame:
    out = []
    for name, mask in condition_masks(sv).items():
        s = sv.loc[mask.fillna(False)]
        if len(s) == 0:
            continue
        out.append({
            "condition": name, "n_trades": len(s),
            "n_accounts": s.groupby(["campaignId", "accountId"]).ngroups,
            "n_campaigns": s["campaignId"].nunique(),
            "E_loss_per_lot": s["gross_loss_per_lot"].mean(),
            "clears_hurdle": s["gross_loss_per_lot"].mean() > HURDLE,
            "mean_reverseProfit": s["reverseProfit"].mean(),
            "median_reverseProfit": s["reverseProfit"].median(),
        })
    return pd.DataFrame(out).sort_values("E_loss_per_lot", ascending=False)


# ----------------------------------------------------------------------
# 7. Cost decomposition: reverseProfit = -profit - cost_stack
# ----------------------------------------------------------------------
def cost_decomposition(sv: pd.DataFrame):
    print("\n=== Cost stack per trade (gross basis: -(reverseProfit + profit)) ===")
    print(sv["est_cost_gross"].describe(percentiles=[.1, .25, .5, .75, .9]))
    print(f"baseline mean reverseProfit: {sv['reverseProfit'].mean():.2f}  "
          f"vs mean est_cost_gross: {sv['est_cost_gross'].mean():.2f}")
    print("(if these are close, baseline fade loss ~= pure cost drag => "
          "conditional edges are behavioral signal)")


# ----------------------------------------------------------------------
# 8. Clustered bootstrap CI on E[loss/lot] vs hurdle
# ----------------------------------------------------------------------
def clustered_bootstrap_table(sv: pd.DataFrame, cluster_col: str,
                              n_boot: int = N_BOOT, seed: int = BOOT_SEED):
    rng = np.random.default_rng(seed)
    masks = condition_masks(sv)
    cond_df = pd.DataFrame({name: m.fillna(False) for name, m in masks.items()})
    work = pd.concat([sv[[cluster_col, "gross_loss_per_lot"]], cond_df], axis=1)
    groups = list(work.groupby(cluster_col))
    keys = np.arange(len(groups))
    frames = [g for _, g in groups]

    results = {name: [] for name in masks}
    for _ in range(n_boot):
        pick = rng.choice(keys, size=len(keys), replace=True)
        samp = pd.concat([frames[k] for k in pick], ignore_index=True)
        for name in masks:
            sel = samp.loc[samp[name], "gross_loss_per_lot"]
            results[name].append(sel.mean() if len(sel) else np.nan)

    print(f"\n=== Clustered bootstrap (cluster={cluster_col}, B={n_boot}) — "
          f"E[loss/lot] vs hurdle {HURDLE:.2f}, 95% CI ===")
    rows = []
    for name, ds in results.items():
        ds = np.array(ds, dtype=float)
        ds = ds[~np.isnan(ds)]
        if len(ds) == 0:
            print(f"NOTE: '{name}' matched no trades in any resample — skipped")
            continue
        lo, hi = np.percentile(ds, [2.5, 97.5])
        rows.append({"condition": name, "mean": ds.mean(),
                     "ci_lo": lo, "ci_hi": hi,
                     "clears_hurdle_95": bool(lo > HURDLE)})
    tbl = pd.DataFrame(rows).sort_values("mean", ascending=False)
    print(tbl.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    return tbl


# ----------------------------------------------------------------------
# 9. Dual-cluster bootstrap for key trigger rows
# ----------------------------------------------------------------------
def key_trigger_bootstrap(sv: pd.DataFrame, cluster_cols: dict[str, str],
                          n_boot: int = N_BOOT, seed: int = BOOT_SEED):
    target_names = [
        "loss_streak >= 2",
        "loss_streak>=2 AND small_size_flag",
    ]
    masks = condition_masks(sv)
    rows = []
    for label, cluster_col in cluster_cols.items():
        rng = np.random.default_rng(seed)
        work = sv[[cluster_col, "gross_loss_per_lot"]].copy()
        for name in target_names:
            work[name] = masks[name].fillna(False).to_numpy()
        groups = [g for _, g in work.groupby(cluster_col)]
        keys = np.arange(len(groups))
        for name in target_names:
            means = []
            for _ in range(n_boot):
                pick = rng.choice(keys, size=len(keys), replace=True)
                samp = pd.concat([groups[k] for k in pick], ignore_index=True)
                sel = samp.loc[samp[name], "gross_loss_per_lot"]
                means.append(sel.mean() if len(sel) else np.nan)
            ds = np.array(means, dtype=float)
            ds = ds[~np.isnan(ds)]
            lo, hi = np.percentile(ds, [2.5, 97.5])
            rows.append({
                "condition": name,
                "cluster_by": label,
                "n_clusters": len(groups),
                "mean": ds.mean(),
                "ci_lo": lo,
                "ci_hi": hi,
                "clears_hurdle_95": bool(lo > HURDLE),
            })

    print(f"\n=== Dual-cluster bootstrap for key triggers (B={n_boot}) ===")
    tbl = pd.DataFrame(rows).sort_values(["condition", "cluster_by"])
    print(tbl.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    return tbl


# ----------------------------------------------------------------------
# 10. Within-campaign robustness
# ----------------------------------------------------------------------
def within_campaign_robustness(sv: pd.DataFrame, min_n: int = 10):
    print(f"\n=== Within-campaign E[loss/lot] robustness vs hurdle {HURDLE:.2f} "
          f"(min n={min_n}/campaign) ===")
    masks = condition_masks(sv)

    work = sv[["campaignId", "gross_loss_per_lot"]].copy()
    for name, m in masks.items():
        work[name] = m.reindex(sv.index).fillna(False).to_numpy()

    for name in masks:
        campaign_means = []
        for camp, g in work.groupby("campaignId"):
            sel = g.loc[g[name], "gross_loss_per_lot"]
            if len(sel) < min_n:
                continue
            campaign_means.append(sel.mean())
        if campaign_means:
            d = np.array(campaign_means)
            print(f"{name:42s} campaigns={len(d):3d}  "
                  f"clears-hurdle={100 * (d > HURDLE).mean():3.0f}%  "
                  f"median-mean={np.median(d):7.2f}")
        else:
            print(f"{name:42s} — no campaign with n >= {min_n}")


def memo_numbers(sv: pd.DataFrame, cluster_col: str, ip_cluster_col: str):
    base = sv["gross_loss_per_lot"].mean()
    size_weighted = -sv["profit"].sum() / sv["amount"].sum()
    dual = key_trigger_bootstrap(
        sv,
        cluster_cols={"traderKey": cluster_col, "ipClusterId": ip_cluster_col},
        n_boot=N_BOOT,
        seed=BOOT_SEED,
    )
    ls2 = dual[(dual["condition"] == "loss_streak >= 2")
               & (dual["cluster_by"] == "traderKey")].iloc[0]
    print("\n=== MEMO NUMBERS ===")
    print(f"baseline E[loss/lot]: {base:.6f}")
    print(f"size-weighted E[loss/lot]: {size_weighted:.6f}")
    print(f"loss_streak>=2 CI (traderKey clustered): [{ls2['ci_lo']:.2f}, {ls2['ci_hi']:.2f}]")
    print(f"n_positions: {len(sv)}")
    print(f"n_active_accounts: {sv['accountId'].nunique()}")
    print(f"n_campaigns: {sv['campaignId'].nunique()}")


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_folder", help="dataset root (contains user_data/, user_trades/)")
    ap.add_argument("--balance", type=float, default=10_000.0,
                    help="starting balance per account (VERIFY with C22)")
    ap.add_argument("--era", choices=["primary", "prelude", "all"], default="primary",
                    help="campaign era for summary statistics; campaigns 41 and 66 are always excluded")
    ap.add_argument("--out", default="features.csv")
    args = ap.parse_args()

    trades = load_all_trades(args.data_folder)
    traders = load_all_traders(args.data_folder)

    pos = to_positions(trades)
    pos["exit_type"] = infer_exit_type(pos)
    pos["grid_entry_flag"] = flag_grid(pos)

    print("\nExit-type distribution:")
    print(pos["exit_type"].value_counts())
    print("SL set: {:.0%}   TP set: {:.0%}".format(
        pos["slPrice"].notna().mean(), pos["tpPrice"].notna().mean()))

    per_camp = pos.groupby("campaignId")["accountId"].nunique()
    print(f"\nAccounts/campaign: min {per_camp.min()}  "
          f"median {per_camp.median():.0f}  max {per_camp.max()}")
    tiny = per_camp[per_camp < 5]
    if len(tiny):
        print(f"NOTE: near-empty campaigns (possible test runs, consider excluding): "
              f"{dict(tiny)}")

    span = pos.groupby(["campaignId", "accountId"]).agg(
        first=("openDateTime", "min"), last=("closeDateTime", "max"))
    span_h = (span["last"] - span["first"]).dt.total_seconds() / 3600
    print("\nAccount active span (hours):")
    print(span_h.describe(percentiles=[.25, .5, .75, .9]))
    over = (span_h > WINDOW_HOURS).sum()
    if over:
        print(f"NOTE: {over} account-campaigns span > {WINDOW_HOURS}h — "
              f"inspect (overnight positions? window not enforced?)")

    sv = build_state_vectors(pos, start_balance=args.balance)
    sv = sv.merge(pos[["campaignId", "positionId", "grid_entry_flag"]],
                  on=["campaignId", "positionId"], how="left") \
           .rename(columns={"grid_entry_flag": "grid_flag"})
    print("index unique:", sv.index.is_unique, "| monotonic:", sv.index.is_monotonic_increasing)
    # traderKey join for clustered bootstrap (accountId <-> traders.account)
    cluster_col = "cluster"
    if not traders.empty and {"account", "traderKey"}.issubset(traders.columns):
        key = traders[["campaignId", "account", "traderKey"]].drop_duplicates()
        sv = sv.merge(key, left_on=["campaignId", "accountId"],
                      right_on=["campaignId", "account"], how="left")
        cov = sv["traderKey"].notna().mean()
        print(f"\ntraderKey join coverage: {cov:.0%}")
        # fallback cluster for unjoined rows: (campaignId, accountId)
        sv[cluster_col] = sv["traderKey"].fillna(
            sv["campaignId"].astype(str) + "_" + sv["accountId"].astype(str))
        if "ipClusterId" in traders.columns:
            ip_map = traders[["campaignId", "account", "ipClusterId"]].drop_duplicates()
            sv = sv.merge(ip_map, left_on=["campaignId", "accountId"],
                          right_on=["campaignId", "account"], how="left",
                          suffixes=("", "_ip"))
            sv["ipCluster"] = np.where(
                sv["ipClusterId"].notna() & (sv["ipClusterId"] != -1),
                "ip_" + sv["ipClusterId"].astype("Int64").astype(str),
                "acct_" + sv["campaignId"].astype(str) + "_" + sv["accountId"].astype(str))
        else:
            sv["ipCluster"] = sv["campaignId"].astype(str) + "_" + sv["accountId"].astype(str)
    else:
        sv[cluster_col] = sv["campaignId"].astype(str) + "_" + sv["accountId"].astype(str)
        sv["ipCluster"] = sv[cluster_col]

    sv, small_size_edge = add_analysis_columns(sv)

    sv.to_csv(args.out, index=False)
    print(f"\nState vectors -> {args.out}  ({len(sv)} rows, {sv.shape[1]} cols)")

    sv_stats = sv.loc[era_mask(sv["campaignId"], args.era)].copy()
    print(f"\n=== Analysis sample: era={args.era} excluding {sorted(EXCLUDE_CAMPAIGNS)} ===")
    print(f"positions={len(sv_stats)}  campaigns={sv_stats['campaignId'].nunique()}  "
          f"active_accounts={sv_stats['accountId'].nunique()}  "
          f"small_size_edge_primary_q1={small_size_edge:.6f}")

    print("\n=== Conditional fade analysis (E[loss/lot] by state) ===")
    print(conditional_fade_analysis(sv_stats).to_string(
        index=False, float_format=lambda x: f"{x:,.2f}"))

    cost_decomposition(sv_stats)
    clustered_bootstrap_table(sv_stats, cluster_col=cluster_col)
    within_campaign_robustness(sv_stats)
    memo_numbers(sv_stats, cluster_col=cluster_col, ip_cluster_col="ipCluster")

    if not traders.empty:
        traders.to_csv("traders_sanitized.csv", index=False)
        print("\nSanitized traders -> traders_sanitized.csv "
              "(delete any previous version — earlier runs leaked PII columns)")

if __name__ == "__main__":
    main()
