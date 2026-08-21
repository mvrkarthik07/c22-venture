from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from build_features import FEATURE_COLUMNS
from splits import PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN, fold_attrition_report, make_folds

BOOL_FEATURES = {"has_sl", "has_tp", "shared_ip", "is_cold_start"}
CATEGORICAL_FEATURES = {"challenge_type"}
CORRELATION_EXCLUDE = {"challenge_type"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Stage 2 features and write markdown report.")
    parser.add_argument("--features", default="features_v2.csv", help="Path to the feature CSV")
    parser.add_argument(
        "--out",
        default="reports/stage2_validation.md",
        help="Output markdown report path",
    )
    parser.add_argument("--n-folds", type=int, default=4, help="Number of walk-forward folds")
    return parser.parse_args()


def load_primary_era(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    mask = df["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)
    return df.loc[mask].copy()


def bucket_numeric(series: pd.Series) -> pd.Series:
    non_null = series.dropna()
    if non_null.empty:
        return pd.Series(index=series.index, dtype="object")

    try:
        buckets = pd.qcut(non_null, q=5, duplicates="drop")
    except ValueError:
        buckets = pd.cut(non_null, bins=min(5, non_null.nunique()), duplicates="drop")

    labels = pd.Series(index=series.index, dtype="object")
    labels.loc[non_null.index] = buckets.astype(str)
    return labels


def build_univariate_table(primary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for feature in FEATURE_COLUMNS:
        series = primary[feature]

        if feature in CATEGORICAL_FEATURES:
            buckets = series.fillna("missing").astype(str)
        elif feature in BOOL_FEATURES or pd.api.types.is_bool_dtype(series):
            buckets = series.map({True: "True", False: "False"})
            buckets = buckets.fillna("missing")
        else:
            buckets = bucket_numeric(pd.to_numeric(series, errors="coerce"))

        work = primary[["gross_loss_per_lot"]].copy()
        work["feature"] = feature
        work["bucket"] = buckets
        work = work.dropna(subset=["bucket"])

        if work.empty:
            rows.append(
                {
                    "feature": feature,
                    "bucket": "no non-null values",
                    "n": 0,
                    "mean_gross_loss_per_lot": np.nan,
                }
            )
            continue

        grouped = (
            work.groupby(["feature", "bucket"], dropna=False)["gross_loss_per_lot"]
            .agg(["size", "mean"])
            .reset_index()
            .rename(columns={"size": "n", "mean": "mean_gross_loss_per_lot"})
        )
        rows.extend(grouped.to_dict("records"))

    out = pd.DataFrame(rows)
    out["feature_order"] = out["feature"].map({feature: idx for idx, feature in enumerate(FEATURE_COLUMNS)})
    out = out.sort_values(["feature_order", "bucket"]).drop(columns=["feature_order"]).reset_index(drop=True)
    return out


def build_correlation_matrix(primary: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, str, float]]]:
    corr_features = [feature for feature in FEATURE_COLUMNS if feature not in CORRELATION_EXCLUDE]
    work = primary[corr_features].copy()

    for feature in corr_features:
        if feature in BOOL_FEATURES or pd.api.types.is_bool_dtype(work[feature]):
            work[feature] = work[feature].astype(float)
        else:
            work[feature] = pd.to_numeric(work[feature], errors="coerce")

    corr = work.corr(method="spearman")
    flagged_pairs: list[tuple[str, str, float]] = []
    for left_idx, left in enumerate(corr.columns):
        for right in corr.columns[left_idx + 1:]:
            rho = corr.loc[left, right]
            if pd.notna(rho) and abs(rho) > 0.7:
                flagged_pairs.append((left, right, float(rho)))

    return corr, flagged_pairs


def format_number(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (bool, np.bool_)):
        return "True" if value else "False"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.4f}"
    return str(value)


def render_markdown_table(df: pd.DataFrame, *, flagged_pairs: set[tuple[str, str]] | None = None) -> str:
    columns = df.columns.tolist()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]

    for row_name, row in df.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            text = format_number(value)
            if flagged_pairs is not None and column != row_name and text:
                pair = tuple(sorted((str(row_name), str(column))))
                if pair in flagged_pairs:
                    text = f"{text} !"
            cells.append(text)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_standard_markdown_table(df: pd.DataFrame) -> str:
    columns = df.columns.tolist()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(format_number(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    primary = load_primary_era(args.features)

    univariate = build_univariate_table(primary)
    corr_matrix, flagged = build_correlation_matrix(primary)
    flagged_set = {tuple(sorted((left, right))) for left, right, _ in flagged}

    make_folds(primary, n_folds=args.n_folds)
    attrition = fold_attrition_report(primary, n_folds=args.n_folds).copy()
    attrition["train_campaigns"] = attrition["train_campaigns"].map(lambda xs: ", ".join(map(str, xs)))
    attrition["val_campaigns"] = attrition["val_campaigns"].map(lambda xs: ", ".join(map(str, xs)))

    report_lines = [
        "# Stage 2 Validation",
        "",
        f"Primary era sample: campaigns {PRIMARY_CAMPAIGN_MIN}-{PRIMARY_CAMPAIGN_MAX}, "
        f"{len(primary)} rows, {primary['accountId'].nunique()} active accounts.",
        "",
        "## 1. Univariate Gross Loss Per Lot by Feature Bucket",
        "",
        render_standard_markdown_table(univariate),
        "",
        "## 2. Spearman Feature Correlation Matrix",
        "",
        "Cells marked with `!` have `|rho| > 0.70`. `challenge_type` is excluded because it is categorical.",
        "",
        render_markdown_table(corr_matrix, flagged_pairs=flagged_set),
        "",
        "Flagged pairs:",
        "",
    ]

    if flagged:
        for left, right, rho in flagged:
            report_lines.append(f"- `{left}` vs `{right}`: rho={rho:.4f}")
    else:
        report_lines.append("- None")

    report_lines.extend(
        [
            "",
            "## 3. Walk-Forward Fold Attrition",
            "",
            render_standard_markdown_table(attrition),
            "",
        ]
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Primary rows: {len(primary)}")
    print(f"Flagged correlation pairs: {len(flagged)}")
    print("\nPer-fold attrition:")
    print(
        attrition[
            [
                "fold",
                "train_campaigns",
                "val_campaigns",
                "trader_only_rows",
                "ip_only_rows",
                "both_rows",
                "raw_val_rows",
                "purged_val_rows",
                "attrition_pct",
                "raw_val_accounts",
                "purged_val_accounts",
                "account_attrition_pct",
            ]
        ].to_string(index=False, float_format=lambda value: f"{value:.2%}" if 0 <= value <= 1 else f"{value:.4f}")
    )


if __name__ == "__main__":
    main()
