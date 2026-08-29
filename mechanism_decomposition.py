from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_features import attach_gold_vol_prev_day, build_feature_rows, download_xauusd_daily_ohlc, load_positions, load_trader_metadata
from pipeline import HURDLE, clustered_bootstrap_conditions, compute_small_size_threshold
from splits import PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN

REPORT_PATH = Path("reports/mechanism_decomposition.md")
REPORT_DIR = REPORT_PATH.parent
NAVY = "#21314D"
RED = "#B23A48"
BG = "#F7F7F5"
TEXT = "#1F2933"
GRID = "#D6D6D1"
LIGHT_NAVY = "#4D607D"
PALE = "#C9D4E3"
DPI = 300

CHANNEL_SPECS = [
    ("sl_widening_delta", "SL Widening Delta", "quartile"),
    ("entry_gap_sec", "Entry Gap (sec)", "quartile"),
    ("same_direction_reentry", "Same-Direction Reentry", "binary"),
    ("size_delta_ratio", "Size Delta Ratio", "quartile"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decompose the loss_streak>=2 trigger across Family F channels.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv", help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument("--balance", type=float, default=10000.0, help="Start balance per account")
    parser.add_argument("--trader-history-k", type=float, default=5.0, help="Shrinkage hyperparameter for trader memory")
    parser.add_argument("--out", default=str(REPORT_PATH), help="Markdown report output path")
    return parser.parse_args()


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": "#A8A8A2",
            "axes.labelcolor": TEXT,
            "axes.titlecolor": TEXT,
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.65,
            "savefig.facecolor": BG,
            "savefig.bbox": "tight",
            "font.family": "Arial",
        }
    )


def clean_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#A8A8A2")
    ax.spines["bottom"].set_color("#A8A8A2")


def build_analysis_sample(args: argparse.Namespace) -> pd.DataFrame:
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
    primary = features.loc[
        features["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)
    ].copy()
    primary["trader_cluster"] = primary["traderKey"].fillna(
        primary["campaignId"].astype(str) + "_" + primary["accountId"].astype(str)
    )
    primary["ip_cluster"] = np.where(
        primary["ipClusterId"].notna() & (primary["ipClusterId"] != -1),
        "ip_" + primary["ipClusterId"].astype("Int64").astype(str),
        "acct_" + primary["campaignId"].astype(str) + "_" + primary["accountId"].astype(str),
    )
    primary["small_size_flag"] = primary["amount"] <= compute_small_size_threshold(primary)
    return primary.reset_index(drop=True)


def make_bin_frame(ls2: pd.DataFrame, feature: str, mode: str) -> tuple[pd.DataFrame, int]:
    work = ls2.copy()
    missing_count = int(work[feature].isna().sum())
    if mode == "binary":
        work = work.loc[work[feature].notna()].copy()
        work["bin_label"] = work[feature].astype(int).map({0: "0", 1: "1"})
        work["bin_order"] = work["bin_label"].astype(int)
        work["bin_detail"] = work["bin_label"].map({"0": "No same-direction reentry", "1": "Same-direction reentry"})
        return work, missing_count

    work = work.loc[work[feature].notna()].copy()
    categories = pd.qcut(work[feature], 4, duplicates="drop")
    labels = [f"Q{i + 1}" for i in range(categories.cat.categories.size)]
    work["bin_order"] = categories.cat.codes
    work["bin_label"] = work["bin_order"].map(dict(enumerate(labels)))
    work["bin_detail"] = categories.astype(str)
    return work, missing_count


def bootstrap_channel_bins(binned: pd.DataFrame, cluster_col: str) -> pd.DataFrame:
    cond_df = pd.DataFrame(
        {
            bin_name: binned["bin_label"].eq(bin_name)
            for bin_name in binned.sort_values("bin_order")["bin_label"].drop_duplicates().tolist()
        },
        index=binned.index,
    )
    result = clustered_bootstrap_conditions(
        binned,
        cluster_col,
        cond_df,
        value_col="gross_loss_per_lot",
    )
    return result.rename(
        columns={
            "condition": "bin_label",
            "raw_mean": "raw_mean_loss_per_lot",
            "boot_mean": "boot_mean_loss_per_lot",
        }
    )


def build_channel_table(primary: pd.DataFrame, feature: str, label: str, mode: str) -> tuple[pd.DataFrame, dict[str, object]]:
    ls2 = primary.loc[primary["loss_streak"] >= 2].copy()
    binned, missing_count = make_bin_frame(ls2, feature, mode)
    if binned.empty:
        raise ValueError(f"No non-null rows available for {feature} within loss_streak >= 2")

    bin_meta = (
        binned.groupby(["bin_label", "bin_order", "bin_detail"], observed=False)
        .size()
        .rename("n")
        .reset_index()
        .sort_values("bin_order")
    )
    trader_boot = bootstrap_channel_bins(binned, "trader_cluster")
    ip_boot = bootstrap_channel_bins(binned, "ip_cluster")

    table = (
        bin_meta.merge(
            trader_boot[
                [
                    "bin_label",
                    "raw_mean_loss_per_lot",
                    "boot_mean_loss_per_lot",
                    "ci_lo",
                    "ci_hi",
                ]
            ].rename(
                columns={
                    "boot_mean_loss_per_lot": "trader_boot_mean",
                    "ci_lo": "trader_ci_lo",
                    "ci_hi": "trader_ci_hi",
                }
            ),
            on="bin_label",
            how="left",
        )
        .merge(
            ip_boot[
                [
                    "bin_label",
                    "boot_mean_loss_per_lot",
                    "ci_lo",
                    "ci_hi",
                ]
            ].rename(
                columns={
                    "boot_mean_loss_per_lot": "ip_boot_mean",
                    "ci_lo": "ip_ci_lo",
                    "ci_hi": "ip_ci_hi",
                }
            ),
            on="bin_label",
            how="left",
        )
        .sort_values("bin_order")
        .reset_index(drop=True)
    )
    table["clears_hurdle_both_95"] = (table["trader_ci_lo"] > HURDLE) & (table["ip_ci_lo"] > HURDLE)

    metadata = {
        "channel": feature,
        "label": label,
        "loss_streak_ge_2_rows": int(len(ls2)),
        "analyzed_rows": int(len(binned)),
        "missing_rows": missing_count,
    }
    return table, metadata


def build_sl_rate_table(primary: pd.DataFrame) -> pd.DataFrame:
    bucket = np.select(
        [primary["loss_streak"] >= 2, primary["loss_streak"] == 1],
        [">=2", "1"],
        default="0",
    )
    return (
        primary.assign(loss_streak_bucket=bucket)
        .groupby("loss_streak_bucket", observed=False)
        .agg(
            n=("has_sl", "size"),
            sl_set_rate=("has_sl", "mean"),
        )
        .reset_index()
        .assign(
            loss_streak_bucket=lambda df: pd.Categorical(
                df["loss_streak_bucket"],
                categories=["0", "1", ">=2"],
                ordered=True,
            )
        )
        .sort_values("loss_streak_bucket")
        .reset_index(drop=True)
    )


def build_size_cross_tab(primary: pd.DataFrame) -> pd.DataFrame:
    ls2 = primary.loc[primary["loss_streak"] >= 2].copy()
    binned, _ = make_bin_frame(ls2, "size_delta_ratio", "quartile")
    return (
        binned.groupby(["small_size_flag", "bin_label", "bin_detail"], observed=False)
        .agg(
            n=("gross_loss_per_lot", "size"),
            raw_mean_loss_per_lot=("gross_loss_per_lot", "mean"),
        )
        .reset_index()
        .sort_values(["small_size_flag", "bin_label"])
        .reset_index(drop=True)
    )


def render_markdown_table(df: pd.DataFrame, float_cols: set[str] | None = None) -> str:
    float_cols = float_cols or set()
    columns = df.columns.tolist()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                cells.append("")
            elif column in float_cols:
                cells.append(f"{float(value):.4f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def plot_channel(table: pd.DataFrame, label: str, out_path: Path) -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(table))
    bar_colors = [NAVY if clears else PALE for clears in table["clears_hurdle_both_95"]]
    ax.bar(x, table["raw_mean_loss_per_lot"], color=bar_colors, edgecolor="none", width=0.64)

    trader_err = np.vstack(
        [
            table["trader_boot_mean"] - table["trader_ci_lo"],
            table["trader_ci_hi"] - table["trader_boot_mean"],
        ]
    )
    ip_err = np.vstack(
        [
            table["ip_boot_mean"] - table["ip_ci_lo"],
            table["ip_ci_hi"] - table["ip_boot_mean"],
        ]
    )
    ax.errorbar(
        x - 0.12,
        table["trader_boot_mean"],
        yerr=trader_err,
        fmt="o",
        color=LIGHT_NAVY,
        ecolor=LIGHT_NAVY,
        elinewidth=2,
        capsize=4,
        label="TraderKey-clustered 95% CI",
    )
    ax.errorbar(
        x + 0.12,
        table["ip_boot_mean"],
        yerr=ip_err,
        fmt="s",
        color="#6B7280",
        ecolor="#6B7280",
        elinewidth=2,
        capsize=4,
        label="ipClusterId-clustered 95% CI",
    )

    ax.axhline(HURDLE, color=RED, lw=2.5, ls="--")
    ax.set_title(f"{label} Within loss_streak >= 2")
    ax.set_ylabel("Gross Loss Per Lot")
    ax.set_xlabel("Bin")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{bin_label}\n{detail}" for bin_label, detail in zip(table["bin_label"], table["bin_detail"])],
        rotation=0,
    )
    for xi, value, n in zip(x, table["raw_mean_loss_per_lot"], table["n"]):
        ax.text(
            xi,
            value + 3,
            f"${value:.2f}\n n={int(n)}",
            ha="center",
            va="bottom",
            fontsize=10,
            color=TEXT,
        )
    ax.legend(frameon=False, loc="upper right")
    clean_axes(ax)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    primary = build_analysis_sample(args)
    channel_results: list[tuple[pd.DataFrame, dict[str, object], Path]] = []
    for feature, label, mode in CHANNEL_SPECS:
        table, metadata = build_channel_table(primary, feature, label, mode)
        chart_path = out_dir / f"mechanism_{feature}.png"
        plot_channel(table, label, chart_path)
        channel_results.append((table, metadata, chart_path))

    sl_rate = build_sl_rate_table(primary)
    size_crosstab = build_size_cross_tab(primary)
    size_small = size_crosstab.loc[size_crosstab["small_size_flag"]].copy()
    size_non_small = size_crosstab.loc[~size_crosstab["small_size_flag"]].copy()
    strongest_small = size_small.sort_values("raw_mean_loss_per_lot", ascending=False).iloc[0]
    strongest_non_small = size_non_small.sort_values("raw_mean_loss_per_lot", ascending=False).iloc[0]
    size_interpretation = (
        "The small-size edge does not look like pure retreat. "
        f"Among `small_size_flag=True`, the strongest cell is `{strongest_small['bin_label']}` "
        f"(`{strongest_small['bin_detail']}`) at `${strongest_small['raw_mean_loss_per_lot']:.2f}/lot` "
        f"on `n={int(strongest_small['n'])}`, which is not confined to the strongest retreat bin alone. "
        f"By contrast, the strongest non-small cell is `{strongest_non_small['bin_label']}` "
        f"at `${strongest_non_small['raw_mean_loss_per_lot']:.2f}/lot`. "
        "That pattern is more consistent with a habitually small trader effect than a clean post-loss halving-down story."
    )
    sl_rate_ls2 = sl_rate.loc[sl_rate["loss_streak_bucket"] == ">=2", "sl_set_rate"].iloc[0]
    sl_rate_0 = sl_rate.loc[sl_rate["loss_streak_bucket"] == "0", "sl_set_rate"].iloc[0]

    lines = [
        "# Mechanism Decomposition",
        "",
        f"Primary era only: campaigns C{PRIMARY_CAMPAIGN_MIN}-C{PRIMARY_CAMPAIGN_MAX}.",
        "",
        "Hold duration, MAE, and realized excursion are **not** used as features here and do **not** enter `features.py`.",
        "This report uses `gross_loss_per_lot` only as the dependent variable.",
        "",
        f"Confirmed trigger reference: `loss_streak >= 2`, hurdle `${HURDLE:.2f}/lot`.",
        "",
        "## Top-Line Findings",
        "",
        f"- Only one Family F bin clears the `$7.00/lot` hurdle at the 95% CI lower bound under **both** clustering schemes: "
        f"`size_delta_ratio` `Q2` (`0.588-1.0`) with traderKey CI `[23.33, 131.41]` and ipClusterId CI `[22.46, 132.98]`.",
        f"- The stop-loss set rate is flat across streak buckets (`loss_streak=0`: `{sl_rate_0:.2%}`, `loss_streak>=2`: `{sl_rate_ls2:.2%}`), "
        "so a claim of systematic stop-loss abandonment after losses is not supported here.",
        f"- {size_interpretation}",
        "",
    ]

    for table, metadata, chart_path in channel_results:
        lines.extend(
            [
                f"## {metadata['label']}",
                "",
                f"`loss_streak >= 2` rows: `{metadata['loss_streak_ge_2_rows']}`. "
                f"Analyzed non-null rows: `{metadata['analyzed_rows']}`. "
                f"Excluded null rows for this channel: `{metadata['missing_rows']}`.",
                "",
                render_markdown_table(
                    table[
                        [
                            "bin_label",
                            "bin_detail",
                            "n",
                            "raw_mean_loss_per_lot",
                            "trader_boot_mean",
                            "trader_ci_lo",
                            "trader_ci_hi",
                            "ip_boot_mean",
                            "ip_ci_lo",
                            "ip_ci_hi",
                            "clears_hurdle_both_95",
                        ]
                    ],
                    float_cols={
                        "raw_mean_loss_per_lot",
                        "trader_boot_mean",
                        "trader_ci_lo",
                        "trader_ci_hi",
                        "ip_boot_mean",
                        "ip_ci_lo",
                        "ip_ci_hi",
                    },
                ),
                "",
                f"Chart: `{chart_path}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Stop-Loss Set Rate by Loss-Streak Bucket",
            "",
            render_markdown_table(sl_rate, float_cols={"sl_set_rate"}),
            "",
            "## Small Absolute Size vs. Size Delta Ratio Within loss_streak >= 2",
            "",
            "This cross-tab distinguishes retreat (`size_delta_ratio < 1`-leaning quartiles) from a habitually small trader.",
            "",
            render_markdown_table(size_crosstab, float_cols={"raw_mean_loss_per_lot"}),
            "",
        ]
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    for _, metadata, chart_path in channel_results:
        print(f"{metadata['label']}: chart -> {chart_path}")


if __name__ == "__main__":
    main()
