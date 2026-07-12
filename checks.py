# checks.py — run: python checks.py
import numpy as np
import pandas as pd

sv = pd.read_csv("features.csv")

# csv round-trip: booleans come back as strings
for col in ("has_sl", "has_tp", "fast_reentry_after_loss",
            "same_side_after_sl", "rule_b_breach_if_filled", "grid_flag",
            "small_size_flag"):
    if col in sv.columns and sv[col].dtype == object:
        sv[col] = sv[col].map({"True": True, "False": False}).astype(bool)

# derived columns (est_cost_gross is not persisted by pipeline.py)
sv["est_cost_gross"] = -(sv["reverseProfit"] + sv["profit"])
sv["cost_per_lot"] = sv["est_cost_gross"] / sv["amount"]
sv["gross_loss_per_lot"] = -sv["profit"] / sv["amount"]   # model target; hurdle = 7.00

HURDLE = 7.00
PRIMARY = sv["campaignId"] >= 53   # primary era (90% of volume)

# ----------------------------------------------------------------------
# CHECK 1: is the $7/lot cost constant across campaigns? (era-dependence)
# ----------------------------------------------------------------------
print("=== cost per lot by campaign (mean) ===")
print(sv.groupby("campaignId")["cost_per_lot"].mean().round(3).to_string())

# ----------------------------------------------------------------------
# CHECK 2: fade table on the per-lot target, primary era only
# ----------------------------------------------------------------------
def masks(d):
    return {
        "baseline": pd.Series(True, index=d.index),
        "no SL set": ~d["has_sl"],
        "loss_streak >= 2": d["loss_streak"] >= 2,
        "loss_streak >= 3": d["loss_streak"] >= 3,
        "same side after SL hit": d["same_side_after_sl"],
        "fast re-entry after loss": d["fast_reentry_after_loss"],
        "size escalation (>1.5x)": d["lot_ratio_vs_avg"] > 1.5,
        "near rule-B cliff (>2.0x)": d["lot_ratio_vs_avg"] > 2.0,
        "deep drawdown (>2%)": d["dd_from_peak_pct"] > 0.02,
        "late session (>0.75)": d["session_pct"] > 0.75,
        "late + underwater": (d["session_pct"] > 0.75) & (d["pnl_pct"] < 0),
    }

def fade_table(d, label):
    print(f"\n=== E[gross loss/lot] by condition — {label} (hurdle = {HURDLE}) ===")
    rows = []
    for name, m in masks(d).items():
        s = d.loc[m.fillna(False)]
        if len(s) == 0:
            continue
        rows.append({"condition": name, "n": len(s),
                     "E_loss_per_lot": s["gross_loss_per_lot"].mean(),
                     "clears_hurdle": s["gross_loss_per_lot"].mean() > HURDLE})
    print(pd.DataFrame(rows).sort_values("E_loss_per_lot", ascending=False)
          .to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

fade_table(sv[PRIMARY], "C53-C65 primary era")
fade_table(sv[~PRIMARY], "C33-C52 prelude era")

# ----------------------------------------------------------------------
# CHECK 3: clustered bootstrap on per-lot target, primary era
# ----------------------------------------------------------------------
def boot(d, cluster_col="cluster", n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    ms = masks(d); ms.pop("baseline")
    work = d[[cluster_col, "gross_loss_per_lot"]].copy()
    for name, m in ms.items():
        work[name] = m.fillna(False).to_numpy()
    groups = [g for _, g in work.groupby(cluster_col)]
    keys = np.arange(len(groups))
    res = {name: [] for name in ms}
    for _ in range(n_boot):
        pick = rng.choice(keys, size=len(keys), replace=True)
        samp = pd.concat([groups[k] for k in pick], ignore_index=True)
        for name in ms:
            sel = samp.loc[samp[name], "gross_loss_per_lot"]
            res[name].append(sel.mean() if len(sel) else np.nan)
    print(f"\n=== bootstrap: E[loss/lot] vs hurdle {HURDLE} — 95% CI ===")
    rows = []
    for name, ds in res.items():
        ds = np.array(ds, float); ds = ds[~np.isnan(ds)]
        if len(ds) == 0:
            continue
        lo, hi = np.percentile(ds, [2.5, 97.5])
        rows.append({"condition": name, "mean": ds.mean(), "ci_lo": lo,
                     "ci_hi": hi, "clears_hurdle_95": bool(lo > HURDLE)})
    print(pd.DataFrame(rows).sort_values("mean", ascending=False)
          .to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

boot(sv[PRIMARY].reset_index(drop=True))

# ----------------------------------------------------------------------
# CHECK 4: challenge_type_id x campaign — locate the C53 product change
# ----------------------------------------------------------------------
tr = pd.read_csv("traders_sanitized.csv")
if "challenge_type_id" in tr.columns:
    ct = pd.crosstab(tr["challenge_type_id"].fillna("unknown"), tr["campaignId"])
    print("\n=== challenge_type_id x campaign ===")
    print(ct.to_string())
else:
    print("\nno challenge_type_id column in traders_sanitized.csv")

# ----------------------------------------------------------------------
# CHECK 5: size vs per-lot fade edge, primary era, excl. test campaigns 41/66
# ----------------------------------------------------------------------
EXCLUDE_CAMPAIGNS = {41, 66}
d5 = sv[PRIMARY & ~sv["campaignId"].isin(EXCLUDE_CAMPAIGNS)].copy()

print(f"\n=== CHECK 5: size vs fade edge — C53-C65 excl. {sorted(EXCLUDE_CAMPAIGNS)} (n={len(d5)}) ===")

print("(a) equal-weighted mean gross_loss_per_lot:", d5["gross_loss_per_lot"].mean())

print("(b) size-weighted -sum(profit)/sum(amount):",
      -d5["profit"].sum() / d5["amount"].sum())

print("(c) Spearman corr(amount, gross_loss_per_lot):",
      d5["amount"].corr(d5["gross_loss_per_lot"], method="spearman"))

d5["amount_quartile"] = pd.qcut(d5["amount"], 4)
print("\n(d) mean gross_loss_per_lot by amount quartile:")
print(d5.groupby("amount_quartile", observed=False)["gross_loss_per_lot"]
      .agg(["mean", "count"]).to_string(float_format=lambda x: f"{x:,.4f}"))

d5_ls2 = d5[d5["loss_streak"] >= 2]
print(f"\n(e) same quartile bins, loss_streak >= 2 only (n={len(d5_ls2)}):")
print(d5_ls2.groupby("amount_quartile", observed=False)["gross_loss_per_lot"]
      .agg(["mean", "count"]).to_string(float_format=lambda x: f"{x:,.4f}"))

# ----------------------------------------------------------------------
# CHECK 6: repeat-participation / shared-IP stats, active traders only
# ----------------------------------------------------------------------
active_keys = set(sv["traderKey"].dropna().unique())
tr_active = tr[tr["traderKey"].isin(active_keys)]

print(f"\n=== CHECK 6: active-trader stats (active = traderKey present in features.csv) ===")

print("active traders total:", len(active_keys))

camp_counts_active = tr_active.groupby("traderKey")["campaignId"].nunique()
n_repeat_active = (camp_counts_active > 1).sum()
print(f"active traders in >1 campaign: {n_repeat_active} "
      f"({100 * n_repeat_active / len(active_keys):.1f}%)")

print("sharedIpFlag rate — all registrants:", tr["sharedIpFlag"].mean())
print("sharedIpFlag rate — active traders: ", tr_active["sharedIpFlag"].mean())

active_accounts_per_camp = sv.groupby("campaignId")["accountId"].nunique()
registrant_rows_per_camp = tr.groupby("campaignId").size()
activation_rate = (active_accounts_per_camp / registrant_rows_per_camp).dropna()
print("\nactivation rate per campaign (active accounts / registrant rows):")
print(activation_rate.to_string(float_format=lambda x: f"{x:.3f}"))

clusters_active = (tr_active[tr_active["ipClusterId"] != -1]
                    .groupby("ipClusterId")["account"].nunique())
shared_clusters_active = clusters_active[clusters_active > 1]
print("\nlargest shared-IP cluster size among active traders:",
      clusters_active.max() if len(clusters_active) else "n/a")

bins = [1, 2, 5, 10, np.inf]
labels = ["size 2", "size 3-5", "size 6-10", "size >10"]
dist = pd.cut(shared_clusters_active, bins=bins, labels=labels, right=True).value_counts().reindex(labels)
print("\nactive shared-IP cluster size distribution:")
print(dist.to_string())

# ----------------------------------------------------------------------
# CHECK 7: shared-IP cluster forensics, active traders only
# ----------------------------------------------------------------------
if "ipClusterId" not in sv.columns:
    ip_map = (tr[["campaignId", "account", "ipClusterId"]].drop_duplicates()
              .rename(columns={"account": "accountId"}))
    sv = sv.merge(ip_map, on=["campaignId", "accountId"], how="left")
sv["ipCluster"] = np.where(
    sv["ipClusterId"].notna() & (sv["ipClusterId"] != -1),
    "ip_" + sv["ipClusterId"].astype("Int64").astype(str),
    "acct_" + sv["campaignId"].astype(str) + "_" + sv["accountId"].astype(str))
sv["openDateTime"] = pd.to_datetime(sv["openDateTime"])

reg_active = tr_active[tr_active["ipClusterId"] != -1].copy()

per_cluster = reg_active.groupby("ipClusterId").agg(
    n_accounts=("account", "nunique"),
    n_campaigns=("campaignId", "nunique"),
    min_campaign=("campaignId", "min"),
    max_campaign=("campaignId", "max"))

same_camp_reg = (reg_active.groupby(["ipClusterId", "campaignId"])["account"]
                 .nunique().rename("n").reset_index())
per_cluster["max_accounts_same_campaign_registered"] = (
    same_camp_reg.groupby("ipClusterId")["n"].max())

sv_active_camp = sv[["campaignId", "accountId"]].drop_duplicates()
traded = reg_active.merge(sv_active_camp, left_on=["campaignId", "account"],
                          right_on=["campaignId", "accountId"], how="inner")
traded_same_camp = (traded.groupby(["ipClusterId", "campaignId"])["account"]
                    .nunique().rename("accounts_traded_in_campaign").reset_index())
per_cluster["max_accounts_same_campaign_traded"] = (
    traded_same_camp.groupby("ipClusterId")["accounts_traded_in_campaign"].max()
    .reindex(per_cluster.index).fillna(0).astype(int))

cluster_141_id = int(clusters_active.idxmax())
top10_ids = per_cluster.sort_values("n_accounts", ascending=False).head(10).index.tolist()
target_ids = sorted(set(top10_ids) | {cluster_141_id})

report = per_cluster.loc[target_ids].sort_values("n_accounts", ascending=False).copy()
report["classification"] = np.where(
    report["max_accounts_same_campaign_traded"] >= 2, "parallel", "serial")

print(f"\n=== CHECK 7: shared-IP cluster forensics — top 10 by active-account count, "
      f"plus cluster {cluster_141_id} (n={clusters_active.max()}) ===")
print("(a)/(b)/(d) per-cluster summary:")
print(report.to_string(float_format=lambda x: f"{x:,.2f}"))

# (c) trading synchrony for parallel clusters: fraction of position opens
# within the same 5-minute bin, cluster accounts vs random account-pair baseline
def synced_frac(campaign_df, accounts, bin_minutes=5):
    d = campaign_df[campaign_df["accountId"].isin(accounts)]
    if len(d) == 0:
        return np.nan
    bins = d["openDateTime"].dt.floor(f"{bin_minutes}min")
    bin_counts = d.groupby(bins)["accountId"].nunique()
    synced_bins = bin_counts[bin_counts >= 2].index
    return bins.isin(synced_bins).mean()

rng = np.random.default_rng(7)
qualifying = traded_same_camp[
    (traded_same_camp["accounts_traded_in_campaign"] >= 2)
    & (traded_same_camp["ipClusterId"].isin(target_ids))]

sync_rows = []
for _, row in qualifying.iterrows():
    cid, camp = int(row["ipClusterId"]), int(row["campaignId"])
    camp_df = sv[sv["campaignId"] == camp]
    cluster_accounts = traded.loc[
        (traded["ipClusterId"] == cid) & (traded["campaignId"] == camp), "accountId"].unique()
    all_accounts = camp_df["accountId"].unique()
    n_draw = len(cluster_accounts)

    frac_cluster = synced_frac(camp_df, cluster_accounts)
    base_fracs = [synced_frac(camp_df, rng.choice(all_accounts, size=n_draw, replace=False))
                  for _ in range(100)]

    sync_rows.append({"ipClusterId": cid, "campaignId": camp, "n_accounts": n_draw,
                      "frac_synced_cluster": frac_cluster,
                      "frac_synced_baseline": np.nanmean(base_fracs)})

sync_df = pd.DataFrame(sync_rows).sort_values(["ipClusterId", "campaignId"])
print("\n(c) trading synchrony (5-min bins) — parallel clusters vs random-account-pair baseline:")
print(sync_df.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))

# ----------------------------------------------------------------------
# CHECK 8: loss_streak>=2 bootstrap, primary era excl. 41/66 —
# traderKey clustering vs ipClusterId clustering, side by side
# ----------------------------------------------------------------------
d8 = sv[PRIMARY & ~sv["campaignId"].isin(EXCLUDE_CAMPAIGNS)].copy()
d8_ls2 = (d8["loss_streak"] >= 2).to_numpy()

def boot_single(d, sel_mask, cluster_col, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    work = d[[cluster_col, "gross_loss_per_lot"]].copy()
    work["_sel"] = sel_mask
    groups = [g for _, g in work.groupby(cluster_col)]
    keys = np.arange(len(groups))
    means = []
    for _ in range(n_boot):
        pick = rng.choice(keys, size=len(keys), replace=True)
        samp = pd.concat([groups[k] for k in pick], ignore_index=True)
        sel = samp.loc[samp["_sel"], "gross_loss_per_lot"]
        means.append(sel.mean() if len(sel) else np.nan)
    ds = np.array(means, float)
    ds = ds[~np.isnan(ds)]
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return {"cluster_by": cluster_col, "n_clusters": len(groups),
            "mean": ds.mean(), "ci_lo": lo, "ci_hi": hi,
            "clears_hurdle_95": bool(lo > HURDLE)}

res_trader = boot_single(d8, d8_ls2, "cluster")
res_ip = boot_single(d8, d8_ls2, "ipCluster")

print(f"\n=== CHECK 8: loss_streak>=2 bootstrap — traderKey vs ipClusterId clustering "
      f"(C53-C65 excl {sorted(EXCLUDE_CAMPAIGNS)}, B=2000) ===")
print(pd.DataFrame([res_trader, res_ip]).to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

# ----------------------------------------------------------------------
# CHECK 9: primary-era size relationship, excl. test campaigns 41/66
# ----------------------------------------------------------------------
d9 = sv[PRIMARY & ~sv["campaignId"].isin(EXCLUDE_CAMPAIGNS)].copy()

print(f"\n=== CHECK 9: primary-era size vs gross_loss_per_lot — "
      f"C53-C65 excl. {sorted(EXCLUDE_CAMPAIGNS)} (n={len(d9)}) ===")

eq_mean = d9["gross_loss_per_lot"].mean()
size_weighted = -d9["profit"].sum() / d9["amount"].sum()
print("(a) equal-weighted mean vs size-weighted -sum(profit)/sum(amount): "
      f"{eq_mean:,.6f} vs {size_weighted:,.6f}")

print("(b) Spearman corr(amount, gross_loss_per_lot):",
      d9["amount"].corr(d9["gross_loss_per_lot"], method="spearman"))

quartiles, amount_bins = pd.qcut(d9["amount"], 4, retbins=True, duplicates="drop")
d9["amount_quartile"] = quartiles

print("\n(c) mean gross_loss_per_lot by amount quartile (bin edges shown below):")
print("bin edges:", [round(float(x), 6) for x in amount_bins])
print(d9.groupby("amount_quartile", observed=False)["gross_loss_per_lot"]
      .agg(["mean", "count"]).to_string(float_format=lambda x: f"{x:,.4f}"))

d9_ls2 = d9[d9["loss_streak"] >= 2].copy()
d9_ls2["amount_quartile"] = pd.cut(
    d9_ls2["amount"],
    bins=amount_bins,
    include_lowest=True,
    duplicates="drop")

print(f"\n(d) same quartile breakdown, loss_streak >= 2 only (n={len(d9_ls2)}):")
print("bin edges:", [round(float(x), 6) for x in amount_bins])
print(d9_ls2.groupby("amount_quartile", observed=False)["gross_loss_per_lot"]
      .agg(["mean", "count"]).to_string(float_format=lambda x: f"{x:,.4f}"))

# ----------------------------------------------------------------------
# CHECK 10: loss_streak>=2 AND small_size_flag campaign means + tail share
# ----------------------------------------------------------------------
if "small_size_flag" not in d9.columns:
    small_size_edge = amount_bins[1]
    d9["small_size_flag"] = d9["amount"] <= small_size_edge

d10 = d9[(d9["loss_streak"] >= 2) & d9["small_size_flag"]].copy()

per_campaign_d10 = (d10.groupby("campaignId")["gross_loss_per_lot"]
                    .agg(mean="mean", count="count"))
per_campaign_d10_qual = per_campaign_d10[per_campaign_d10["count"] >= 10] \
    .sort_values("mean", ascending=False)

top_n = max(int(np.ceil(len(d10) * 0.05)), 1)
top_tail = d10.nlargest(top_n, "reverseProfit")
tail_share = top_tail["reverseProfit"].sum() / d10["reverseProfit"].sum()

print(f"\n=== CHECK 10: loss_streak>=2 AND small_size_flag "
      f"(n={len(d10)}, qualifying campaigns={len(per_campaign_d10_qual)}) ===")
print("(a) per-campaign mean gross_loss_per_lot for campaigns with n >= 10, sorted:")
print(per_campaign_d10_qual.to_string(float_format=lambda x: f"{x:,.4f}"))

print(f"\n(b) top 5% trade contribution to total reverseProfit within condition "
      f"(tail-driven check; n_top={top_n}):")
print(f"top_5pct_reverseProfit_share: {tail_share:,.4f}")
print(f"top_5pct_reverseProfit_sum: {top_tail['reverseProfit'].sum():,.4f}")
print(f"condition_total_reverseProfit: {d10['reverseProfit'].sum():,.4f}")
