from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_features import FEATURE_COLUMNS, attach_gold_vol_prev_day, build_feature_rows, download_xauusd_daily_ohlc, load_positions, load_trader_metadata
from splits import PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN, get_folds

DEFAULT_MARKDOWN_PATH = Path("reports/feature_prune_v21.md")
DEFAULT_HEATMAP_PATH = Path("reports/feature_prune_v21_heatmap.png")
CORR_EXCLUDE = {"challenge_type"}
FROZEN_FAMILIES = {
    "loss_streak": "A",
    "win_streak": "A",
    "pnl_ewm": "A",
    "lot_zscore": "B",
    "amount": "B",
    "size_after_loss_delta": "B",
    "has_sl": "C",
    "has_tp": "C",
    "sl_distance_pct": "C",
    "sl_usage_rate_5": "C",
    "manual_exit_rate_5": "C",
    "pnl_pct": "D",
    "dd_from_peak_pct": "D",
    "trade_index": "D",
    "log_dt_close": "D",
    "trades_per_hour": "D",
    "prior_campaigns": "E",
    "shared_ip": "E",
    "ip_cluster_size": "E",
    "challenge_type": "E",
    "gold_vol_prev_day": "E",
    "sl_widening_delta": "F",
    "entry_gap_sec": "F",
    "same_direction_reentry": "F",
    "size_delta_ratio": "F",
    "trader_prior_tilt": "G",
    "trader_prior_sl_discipline": "G",
    "trader_prior_survival": "G",
    "prior_campaigns_x_loss_streak_ge_2": "G",
    "is_cold_start": "G",
}
FAMILY_AGE = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
FROZEN_21 = [
    "loss_streak",
    "win_streak",
    "pnl_ewm",
    "lot_zscore",
    "amount",
    "size_after_loss_delta",
    "has_sl",
    "has_tp",
    "sl_distance_pct",
    "sl_usage_rate_5",
    "manual_exit_rate_5",
    "pnl_pct",
    "dd_from_peak_pct",
    "trade_index",
    "log_dt_close",
    "trades_per_hour",
    "prior_campaigns",
    "shared_ip",
    "ip_cluster_size",
    "challenge_type",
    "gold_vol_prev_day",
]
NEW_FAMILY_FEATURES = [
    "sl_widening_delta",
    "entry_gap_sec",
    "same_direction_reentry",
    "size_delta_ratio",
    "trader_prior_tilt",
    "trader_prior_sl_discipline",
    "trader_prior_survival",
    "prior_campaigns_x_loss_streak_ge_2",
    "is_cold_start",
]
PRUNE_FEATURE_COLUMNS = FEATURE_COLUMNS + ["entry_gap_sec", "is_cold_start"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Stage 2.1 correlation prune on training folds only.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv", help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument("--balance", type=float, default=10000.0, help="Start balance per account")
    parser.add_argument("--trader-history-k", type=float, default=5.0, help="Shrinkage hyperparameter for trader memory")
    parser.add_argument("--out-md", default=str(DEFAULT_MARKDOWN_PATH), help="Markdown report output path")
    parser.add_argument("--out-png", default=str(DEFAULT_HEATMAP_PATH), help="Heatmap PNG output path")
    return parser.parse_args()


def build_primary_training_sample(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    positions = load_positions(args.datasets)
    trader_meta = load_trader_metadata(args.traders, positions)
    min_required_date = (
        pd.to_datetime(positions["campaignDate"]).dt.normalize().min() - pd.Timedelta(days=1)
    ).date()
    daily_ohlc = download_xauusd_daily_ohlc(args.cache, min_required_date=min_required_date)
    positions = attach_gold_vol_prev_day(positions, daily_ohlc)
    features = build_feature_rows(
        positions,
        trader_meta,
        start_balance=args.balance,
        trader_history_params={"shrinkage_k": args.trader_history_k},
    )
    primary = (
        features.loc[features["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)]
        .copy()
        .reset_index(drop=True)
    )
    folds = get_folds(primary, track="A")
    train_union = sorted({int(idx) for train_idx, _ in folds for idx in train_idx})
    training = primary.loc[train_union].copy().reset_index(drop=True)
    return primary, training


def prepare_correlation_frame(training: pd.DataFrame) -> pd.DataFrame:
    corr_features = [feature for feature in PRUNE_FEATURE_COLUMNS if feature not in CORR_EXCLUDE]
    work = training[corr_features].copy()
    for feature in corr_features:
        if pd.api.types.is_bool_dtype(work[feature]):
            work[feature] = work[feature].astype(float)
        else:
            work[feature] = pd.to_numeric(work[feature], errors="coerce")
    return work


def collect_pairs(corr: pd.DataFrame, threshold: float = 0.74) -> list[dict]:
    rows: list[dict] = []
    columns = corr.columns.tolist()
    for left_idx, left in enumerate(columns):
        for right in columns[left_idx + 1:]:
            rho = corr.loc[left, right]
            if pd.notna(rho) and abs(rho) > threshold:
                rows.append(
                    {
                        "feature_1": left,
                        "feature_2": right,
                        "rho": float(rho),
                    }
                )
    rows.sort(key=lambda row: abs(row["rho"]), reverse=True)
    return rows


def choose_drop_candidate(
    feature_1: str,
    feature_2: str,
    coverage: dict[str, float],
) -> tuple[str, str, str]:
    coverage_1 = coverage[feature_1]
    coverage_2 = coverage[feature_2]
    coverage_gap = abs(coverage_1 - coverage_2)
    if coverage_gap > 0.02:
        if coverage_1 > coverage_2:
            return feature_2, feature_1, (
                f"retain `{feature_1}` for higher coverage ({coverage_1:.2%} vs {coverage_2:.2%})"
            )
        return feature_1, feature_2, (
            f"retain `{feature_2}` for higher coverage ({coverage_2:.2%} vs {coverage_1:.2%})"
        )

    family_1 = FROZEN_FAMILIES[feature_1]
    family_2 = FROZEN_FAMILIES[feature_2]
    age_1 = FAMILY_AGE[family_1]
    age_2 = FAMILY_AGE[family_2]
    if age_1 < age_2:
        return feature_2, feature_1, (
            f"coverage within 2pp; retain older frozen family `{family_1}` feature `{feature_1}`"
        )
    if age_2 < age_1:
        return feature_1, feature_2, (
            f"coverage within 2pp; retain older frozen family `{family_2}` feature `{feature_2}`"
        )
    if feature_1 <= feature_2:
        return feature_2, feature_1, (
            f"coverage within 2pp and same family; retain lexicographically earlier `{feature_1}`"
        )
    return feature_1, feature_2, (
        f"coverage within 2pp and same family; retain lexicographically earlier `{feature_2}`"
    )


def apply_prune(pair_rows: list[dict], coverage: dict[str, float]) -> tuple[pd.DataFrame, list[str], dict[str, dict[str, str]]]:
    active = {feature for feature in PRUNE_FEATURE_COLUMNS if feature not in CORR_EXCLUDE}
    dropped_meta: dict[str, dict[str, str]] = {}
    output_rows: list[dict] = []

    for row in pair_rows:
        feature_1 = row["feature_1"]
        feature_2 = row["feature_2"]
        abs_rho = abs(row["rho"])

        if abs_rho <= 0.9:
            row["action"] = "RETAINED for regularization"
            row["tie_break_reason"] = "|rho| <= 0.90 threshold"
            output_rows.append(row)
            continue

        if feature_1 in active and feature_2 in active:
            drop_feature, keep_feature, reason = choose_drop_candidate(feature_1, feature_2, coverage)
            active.remove(drop_feature)
            dropped_meta[drop_feature] = {
                "kept_feature": keep_feature,
                "reason": reason,
            }
            row["action"] = "DROPPED"
            row["tie_break_reason"] = f"drop `{drop_feature}`; {reason}"
        else:
            already_dropped = feature_1 if feature_1 not in active else feature_2
            metadata = dropped_meta[already_dropped]
            row["action"] = "DROPPED"
            row["tie_break_reason"] = (
                f"`{already_dropped}` already removed by stronger pair; "
                f"{metadata['reason']}"
            )
        output_rows.append(row)

    surviving = [feature for feature in PRUNE_FEATURE_COLUMNS if feature in active or feature in CORR_EXCLUDE]
    return pd.DataFrame(output_rows), surviving, dropped_meta


def render_markdown_table(df: pd.DataFrame) -> str:
    lines = [
        "| feature_1 | feature_2 | rho | action | tie_break_reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in df.itertuples(index=False):
        lines.append(
            f"| `{row.feature_1}` | `{row.feature_2}` | {row.rho:.4f} | {row.action} | {row.tie_break_reason} |"
        )
    return "\n".join(lines)


def write_heatmap(corr: pd.DataFrame, out_path: Path) -> None:
    heatmap = corr.loc[NEW_FAMILY_FEATURES, [feature for feature in FROZEN_21 if feature != "challenge_type"]]
    fig_width = max(10, len(heatmap.columns) * 0.55)
    fig_height = max(4, len(heatmap.index) * 0.55)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(heatmap.to_numpy(), cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(heatmap.columns)))
    ax.set_xticklabels(heatmap.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(heatmap.index)))
    ax.set_yticklabels(heatmap.index)
    ax.set_title("Spearman rho: New Families vs Frozen 21 (training rows only)")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("Spearman rho")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    _, training = build_primary_training_sample(args)
    corr_frame = prepare_correlation_frame(training)
    coverage = corr_frame.notna().mean().to_dict()
    corr = corr_frame.corr(method="spearman")
    pair_rows = collect_pairs(corr, threshold=0.74)
    table, surviving, _ = apply_prune(pair_rows, coverage)

    out_md = Path(args.out_md)
    out_png = Path(args.out_png)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    actual_tilt_rho = float(corr.loc["prior_campaigns", "trader_prior_tilt"])
    markdown_lines = [
        "# Stage 2.1 Correlation Prune",
        "",
        f"Training-only sample: primary era C{PRIMARY_CAMPAIGN_MIN}-C{PRIMARY_CAMPAIGN_MAX}, "
        f"{len(training)} deduplicated rows appearing in at least one training fold.",
        "",
        f"Prunable feature count for Spearman: `{len(corr.columns)}` "
        f"(categorical `challenge_type` excluded from the matrix).",
        "",
        f"`prior_campaigns` vs `trader_prior_tilt`: rho=`{actual_tilt_rho:.4f}`. "
        "This does not cross the `|rho| > 0.90` prune threshold, so it is retained mechanically.",
        "",
        "## Pairs Above |rho| > 0.74",
        "",
        render_markdown_table(table),
        "",
        f"## Final Surviving Feature List ({len(surviving)})",
        "",
        ", ".join(f"`{feature}`" for feature in surviving),
        "",
        f"Heatmap: `{out_png}`",
        "",
    ]
    out_md.write_text("\n".join(markdown_lines), encoding="utf-8")
    write_heatmap(corr, out_png)

    print(f"Wrote {out_md}")
    print(f"Wrote {out_png}")
    print(f"Surviving feature count: {len(surviving)}")
    print(f"prior_campaigns vs trader_prior_tilt rho: {actual_tilt_rho:.4f}")
    print("\nPairs above |rho| > 0.74:")
    print(
        table.to_string(
            index=False,
            formatters={"rho": lambda value: f"{value:.4f}"},
        )
    )


if __name__ == "__main__":
    main()
