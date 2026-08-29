from __future__ import annotations

import argparse
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from build_features import (
    attach_gold_vol_prev_day,
    build_feature_rows,
    download_xauusd_daily_ohlc,
    load_positions,
    load_trader_metadata,
)
from splits import PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN

DEFAULT_OUT_PATH = Path("reports/design_annex_stats.md")
PRIMARY_DD_BOUNDARY = 0.04
BOUNDARY_WINDOW = 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute design-annex statistics for primary-era rule-cohort planning.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv", help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument("--balance", type=float, default=10000.0, help="Start balance per account")
    parser.add_argument("--trader-history-k", type=float, default=5.0, help="Shrinkage hyperparameter for trader memory")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Markdown report output path")
    return parser.parse_args()


def fmt(value: object) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if pd.isna(value):
            return "NaN"
        return format(float(value), ".12g")
    return str(value)


def render_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(getattr(row, col)) for col in columns) + " |")
    return "\n".join(lines)


def build_primary_dataset(args: argparse.Namespace) -> pd.DataFrame:
    positions = load_positions(args.datasets)
    trader_meta = load_trader_metadata(args.traders, positions)
    min_required_date = (
        pd.to_datetime(positions["campaignDate"]).dt.normalize().min() - pd.Timedelta(days=1)
    ).date()
    daily_ohlc = download_xauusd_daily_ohlc(args.cache, min_required_date=min_required_date)
    positions_with_gold = attach_gold_vol_prev_day(positions, daily_ohlc)
    feature_rows = build_feature_rows(
        positions_with_gold,
        trader_meta,
        start_balance=args.balance,
        trader_history_params={"shrinkage_k": args.trader_history_k},
    )
    primary_features = (
        feature_rows.loc[feature_rows["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)]
        .copy()
        .reset_index(drop=True)
    )
    primary_positions = (
        positions.loc[positions["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)]
        .copy()
    )
    merged = primary_features.merge(
        primary_positions[["campaignId", "accountId", "positionId", "profit"]],
        on=["campaignId", "accountId", "positionId"],
        how="left",
        validate="one_to_one",
    )
    return merged


def winsorize(series: pd.Series, lower_q: float, upper_q: float) -> tuple[pd.Series, float, float]:
    lower = float(series.quantile(lower_q))
    upper = float(series.quantile(upper_q))
    return series.clip(lower=lower, upper=upper), lower, upper


def trader_clusters(df: pd.DataFrame) -> tuple[pd.Series, int, int]:
    fallback_mask = df["traderKey"].isna()
    fallback = df["campaignId"].astype(str) + "_" + df["accountId"].astype(str)
    cluster = df["traderKey"].astype("object").where(~fallback_mask, fallback)
    return cluster, int(fallback_mask.sum()), int(fallback.loc[fallback_mask].nunique())


def ip_clusters(df: pd.DataFrame) -> tuple[pd.Series, int, int]:
    valid_ip = df["ipClusterId"].notna() & (df["ipClusterId"] != -1)
    fallback_mask = ~valid_ip
    fallback = "acct_" + df["campaignId"].astype(str) + "_" + df["accountId"].astype(str)
    valid_labels = "ip_" + df["ipClusterId"].astype("Int64").astype(str)
    cluster = pd.Series(np.where(valid_ip, valid_labels, fallback), index=df.index)
    return cluster, int(fallback_mask.sum()), int(fallback.loc[fallback_mask].nunique())


def one_way_random_effects_icc(values: pd.Series, clusters: pd.Series) -> dict[str, float | int]:
    work = pd.DataFrame({"y": values, "cluster": clusters}).dropna().copy()
    grouped = work.groupby("cluster", sort=False)
    cluster_sizes = grouped.size().astype(float)
    cluster_means = grouped["y"].mean()
    grand_mean = float(work["y"].mean())

    ssb = float((cluster_sizes * (cluster_means - grand_mean).pow(2)).sum())
    work = work.join(cluster_means.rename("cluster_mean"), on="cluster")
    ssw = float(((work["y"] - work["cluster_mean"]).pow(2)).sum())

    n_total = int(cluster_sizes.sum())
    n_clusters = int(len(cluster_sizes))
    df_between = n_clusters - 1
    df_within = n_total - n_clusters
    ms_between = ssb / df_between
    ms_within = ssw / df_within
    m0 = float((n_total - cluster_sizes.pow(2).sum() / n_total) / df_between)
    icc = float((ms_between - ms_within) / (ms_between + (m0 - 1.0) * ms_within))
    mean_cluster_size = float(n_total / n_clusters)
    deff = float(1.0 + (mean_cluster_size - 1.0) * icc)

    return {
        "n_rows": n_total,
        "n_clusters": n_clusters,
        "mean_cluster_size": mean_cluster_size,
        "ms_between": float(ms_between),
        "ms_within": float(ms_within),
        "m0": m0,
        "icc": icc,
        "deff": deff,
        "singleton_clusters": int((cluster_sizes == 1).sum()),
        "max_cluster_size": int(cluster_sizes.max()),
    }


def main() -> None:
    args = parse_args()
    primary = build_primary_dataset(args)

    outcome = primary["gross_loss_per_lot"].dropna()
    winsorized_outcome, q01, q99 = winsorize(outcome, 0.01, 0.99)
    sigma_raw = float(outcome.std(ddof=1))
    sigma_winsorized = float(winsorized_outcome.std(ddof=1))

    trader_cluster, trader_fallback_rows, trader_fallback_clusters = trader_clusters(primary)
    ip_cluster, ip_fallback_rows, ip_fallback_clusters = ip_clusters(primary)
    trader_icc = one_way_random_effects_icc(primary["gross_loss_per_lot"], trader_cluster)
    ip_icc = one_way_random_effects_icc(primary["gross_loss_per_lot"], ip_cluster)

    positions_per_campaign = primary.groupby("campaignId").size().rename("positions")
    active_accounts_per_campaign = primary.groupby("campaignId")["accountId"].nunique().rename("active_accounts")
    positions_per_active_account = primary.groupby(["campaignId", "accountId"]).size().rename("positions_per_active_account")
    active_span = (
        primary.groupby(["campaignId", "accountId"])
        .agg(first_open=("openDateTime", "min"), last_close=("closeDateTime", "max"))
    )
    active_span_hours = (active_span["last_close"] - active_span["first_open"]).dt.total_seconds() / 3600.0

    boundary_low = PRIMARY_DD_BOUNDARY - BOUNDARY_WINDOW
    boundary_high = PRIMARY_DD_BOUNDARY + BOUNDARY_WINDOW
    near_boundary_mask = primary["dd_from_peak_pct"].between(boundary_low, boundary_high, inclusive="both")

    no_sl_mask = ~primary["has_sl"]
    abs_profit = primary["profit"].abs()

    z_alpha = float(NormalDist().inv_cdf(1.0 - 0.05 / 2.0))
    z_beta = float(NormalDist().inv_cdf(0.80))
    z_sum = z_alpha + z_beta

    n_per_arm_rows: list[dict[str, object]] = []
    sigma_options = {
        "raw": sigma_raw,
        "winsorized_1pct_99pct": sigma_winsorized,
    }
    cluster_options = {
        "traderKey": trader_icc,
        "ipClusterId": ip_icc,
    }
    mean_positions_per_campaign = float(positions_per_campaign.mean())
    mean_active_accounts_per_campaign = float(active_accounts_per_campaign.mean())
    mean_positions_per_active_account = float(positions_per_active_account.mean())

    for sigma_label, sigma in sigma_options.items():
        for cluster_label, cluster_stats in cluster_options.items():
            for delta in (10.0, 20.0, 40.0):
                exact_n = float(
                    2.0 * (z_sum ** 2) * (sigma ** 2) / (delta ** 2) * float(cluster_stats["deff"])
                )
                required_active_accounts = float(exact_n / mean_positions_per_active_account)
                n_per_arm_rows.append(
                    {
                        "sigma_variant": sigma_label,
                        "cluster_scheme": cluster_label,
                        "delta_dollars_per_lot": delta,
                        "n_per_arm_formula": exact_n,
                        "n_per_arm_ceiling": int(np.ceil(exact_n)),
                        "required_active_accounts_per_arm": required_active_accounts,
                        "campaign_waves_per_arm_from_positions": exact_n / mean_positions_per_campaign,
                        "campaign_waves_per_arm_from_active_accounts": required_active_accounts / mean_active_accounts_per_campaign,
                    }
                )

    sample_table = pd.DataFrame(
        [
            {
                "quantity": "primary_positions",
                "value": int(len(primary)),
                "method": "feature rows in campaigns 53-65 merged one-to-one to raw positions",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "primary_campaigns",
                "value": int(primary["campaignId"].nunique()),
                "method": "distinct campaignId in campaigns 53-65",
                "n_basis": int(primary["campaignId"].nunique()),
            },
            {
                "quantity": "distinct_account_ids",
                "value": int(primary["accountId"].nunique()),
                "method": "distinct accountId across the primary era",
                "n_basis": int(primary["accountId"].nunique()),
            },
            {
                "quantity": "campaign_account_pairs",
                "value": int(primary[["campaignId", "accountId"]].drop_duplicates().shape[0]),
                "method": "distinct (campaignId, accountId) pairs",
                "n_basis": int(primary[["campaignId", "accountId"]].drop_duplicates().shape[0]),
            },
        ]
    )

    sigma_table = pd.DataFrame(
        [
            {
                "sigma_variant": "raw",
                "std_dev": sigma_raw,
                "winsor_lower": np.nan,
                "winsor_upper": np.nan,
                "method": "sample standard deviation of gross_loss_per_lot with ddof=1",
                "n_rows": int(len(outcome)),
            },
            {
                "sigma_variant": "winsorized_1pct_99pct",
                "std_dev": sigma_winsorized,
                "winsor_lower": q01,
                "winsor_upper": q99,
                "method": "sample standard deviation after clipping at empirical 1st/99th percentiles; ddof=1",
                "n_rows": int(len(winsorized_outcome)),
            },
        ]
    )

    icc_table = pd.DataFrame(
        [
            {
                "cluster_scheme": "traderKey",
                "icc": trader_icc["icc"],
                "mean_cluster_size": trader_icc["mean_cluster_size"],
                "design_effect": trader_icc["deff"],
                "n_rows": trader_icc["n_rows"],
                "n_clusters": trader_icc["n_clusters"],
                "fallback_rows": trader_fallback_rows,
                "fallback_singleton_clusters": trader_fallback_clusters,
                "singleton_clusters_total": trader_icc["singleton_clusters"],
                "max_cluster_size": trader_icc["max_cluster_size"],
                "method": "one-way random-effects ANOVA ICC with singleton fallback for missing traderKey rows",
            },
            {
                "cluster_scheme": "ipClusterId",
                "icc": ip_icc["icc"],
                "mean_cluster_size": ip_icc["mean_cluster_size"],
                "design_effect": ip_icc["deff"],
                "n_rows": ip_icc["n_rows"],
                "n_clusters": ip_icc["n_clusters"],
                "fallback_rows": ip_fallback_rows,
                "fallback_singleton_clusters": ip_fallback_clusters,
                "singleton_clusters_total": ip_icc["singleton_clusters"],
                "max_cluster_size": ip_icc["max_cluster_size"],
                "method": "one-way random-effects ANOVA ICC with singleton fallback for invalid ipClusterId rows",
            },
        ]
    )

    per_campaign_table = (
        pd.concat([positions_per_campaign, active_accounts_per_campaign], axis=1)
        .reset_index()
        .sort_values("campaignId")
    )

    support_table = pd.DataFrame(
        [
            {
                "quantity": "positions_per_active_account_mean",
                "value": float(positions_per_active_account.mean()),
                "method": "mean of per-(campaignId, accountId) position counts",
                "n_basis": int(len(positions_per_active_account)),
            },
            {
                "quantity": "positions_per_active_account_median",
                "value": float(positions_per_active_account.median()),
                "method": "median of per-(campaignId, accountId) position counts",
                "n_basis": int(len(positions_per_active_account)),
            },
            {
                "quantity": "positions_per_active_account_p90",
                "value": float(positions_per_active_account.quantile(0.9)),
                "method": "90th percentile of per-(campaignId, accountId) position counts",
                "n_basis": int(len(positions_per_active_account)),
            },
            {
                "quantity": "active_span_hours_mean",
                "value": float(active_span_hours.mean()),
                "method": "mean of per-(campaignId, accountId) active span hours from first open to last close",
                "n_basis": int(len(active_span_hours)),
            },
            {
                "quantity": "active_span_hours_median",
                "value": float(active_span_hours.median()),
                "method": "median of per-(campaignId, accountId) active span hours from first open to last close",
                "n_basis": int(len(active_span_hours)),
            },
            {
                "quantity": "active_span_hours_p90",
                "value": float(active_span_hours.quantile(0.9)),
                "method": "90th percentile of per-(campaignId, accountId) active span hours from first open to last close",
                "n_basis": int(len(active_span_hours)),
            },
            {
                "quantity": "near_4pct_drawdown_positions",
                "value": int(near_boundary_mask.sum()),
                "method": "count of positions with dd_from_peak_pct in [0.03, 0.05]",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "near_4pct_drawdown_share",
                "value": float(near_boundary_mask.mean()),
                "method": "share of positions with dd_from_peak_pct in [0.03, 0.05]",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "no_sl_position_count",
                "value": int(no_sl_mask.sum()),
                "method": "count of positions with has_sl == False",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "no_sl_position_share",
                "value": float(no_sl_mask.mean()),
                "method": "share of positions with has_sl == False",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "no_sl_abs_profit_share",
                "value": float(abs_profit.loc[no_sl_mask].sum() / abs_profit.sum()),
                "method": "share of total absolute P&L contributed by positions with has_sl == False, using abs(profit)",
                "n_basis": int(len(primary)),
            },
            {
                "quantity": "total_absolute_profit",
                "value": float(abs_profit.sum()),
                "method": "sum of abs(profit) across all primary-era positions",
                "n_basis": int(len(primary)),
            },
        ]
    )

    n_per_arm_table = pd.DataFrame(n_per_arm_rows)

    lines = [
        "# Design Annex Stats",
        "",
        "## Sample",
        "",
        render_table(sample_table),
        "",
        "## Sigma",
        "",
        render_table(sigma_table),
        "",
        "## ICC, Mean Cluster Size, and Design Effect",
        "",
        render_table(icc_table),
        "",
        "## Campaign Throughput Inputs",
        "",
        f"- `mean_positions_per_campaign` = `{fmt(mean_positions_per_campaign)}` from `n_campaigns={primary['campaignId'].nunique()}`.",
        f"- `mean_active_accounts_per_campaign` = `{fmt(mean_active_accounts_per_campaign)}` from `n_campaigns={primary['campaignId'].nunique()}`.",
        f"- `mean_positions_per_active_account` = `{fmt(mean_positions_per_active_account)}` from `n_campaign_account_pairs={len(positions_per_active_account)}`.",
        "",
        render_table(per_campaign_table),
        "",
        "## Required n Per Arm",
        "",
        f"- Formula: `n_per_arm = 2 * (z_(1-alpha/2) + z_(1-beta))^2 * sigma^2 / delta^2 * DEFF`.",
        f"- `alpha = 0.05`, `power = 0.80`, `z_(1-alpha/2) = {fmt(z_alpha)}`, `z_(1-beta) = {fmt(z_beta)}`, `z_sum = {fmt(z_sum)}`.",
        f"- `campaign_waves_per_arm_from_positions = n_per_arm / mean_positions_per_campaign`.",
        f"- `campaign_waves_per_arm_from_active_accounts = (n_per_arm / mean_positions_per_active_account) / mean_active_accounts_per_campaign`.",
        "",
        render_table(n_per_arm_table),
        "",
        "## Supporting Stats",
        "",
        render_table(support_table),
        "",
    ]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
