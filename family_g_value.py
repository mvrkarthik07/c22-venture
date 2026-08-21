from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from build_features import attach_gold_vol_prev_day, build_feature_rows, download_xauusd_daily_ohlc, load_positions, load_trader_metadata
from pipeline import DEFAULT_COST_PER_LOT, STARTING_BALANCE
from splits import FLAGGED_SYNCHRONOUS_PAIRS, PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN, get_folds

HURDLE = DEFAULT_COST_PER_LOT
ALPHA_GRID = np.logspace(-3, 3, 13)
REPORT_PATH = Path("reports/family_g_value.md")

M1_FEATURES = [
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
FAMILY_F_SURVIVORS = [
    "sl_widening_delta",
    "same_direction_reentry",
    "size_delta_ratio",
]
FAMILY_G_SURVIVORS = [
    "trader_prior_tilt",
    "trader_prior_sl_discipline",
    "trader_prior_survival",
    "prior_campaigns_x_loss_streak_ge_2",
]
MODEL_FEATURES = {
    "M1": M1_FEATURES,
    "M2": M1_FEATURES + FAMILY_F_SURVIVORS,
    "M3": M1_FEATURES + FAMILY_F_SURVIVORS + FAMILY_G_SURVIVORS,
}


@dataclass
class FoldResult:
    model: str
    track: str
    fold: str
    n_rows: int
    alpha: float | None
    spearman_rho: float
    mae: float
    flagged_mean_loss_per_lot: float
    flagged_coverage: float
    n_flagged: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quantify Family G value on Track A and Track B.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv", help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument(
        "--balance",
        type=float,
        default=STARTING_BALANCE,
        help="Confirmed starting balance per account",
    )
    parser.add_argument("--trader-history-k", type=float, default=5.0, help="Shrinkage hyperparameter for trader memory")
    parser.add_argument("--out", default=str(REPORT_PATH), help="Markdown report output path")
    return parser.parse_args()


def build_primary_sample(args: argparse.Namespace) -> pd.DataFrame:
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
    return primary


def _flagged_sync_mask(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        [
            pd.notna(ip_cluster_id) and (ip_cluster_id, campaign_id) in FLAGGED_SYNCHRONOUS_PAIRS
            for ip_cluster_id, campaign_id in zip(df["ipClusterId"], df["campaignId"])
        ],
        index=df.index,
    )


def make_inner_folds(train_df: pd.DataFrame, track: str) -> list[tuple[np.ndarray, np.ndarray]]:
    campaigns = sorted(train_df["campaignId"].dropna().unique().tolist())
    if len(campaigns) < 3:
        return []

    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for train_end in range(2, len(campaigns)):
        inner_train_campaigns = campaigns[:train_end]
        inner_val_campaign = campaigns[train_end]

        inner_train = train_df.loc[train_df["campaignId"].isin(inner_train_campaigns)]
        raw_val = train_df.loc[train_df["campaignId"] == inner_val_campaign]

        if track == "A":
            train_trader_keys = set(inner_train["traderKey"].dropna().astype(str))
            train_ip_clusters = set(inner_train["ipClusterId"].dropna().tolist())

            trader_overlap = raw_val["traderKey"].astype(str).isin(train_trader_keys) & raw_val["traderKey"].notna()
            ip_overlap = raw_val["ipClusterId"].isin(train_ip_clusters) & raw_val["ipClusterId"].notna()
            targeted_ip_overlap = ip_overlap & _flagged_sync_mask(raw_val)
            val_df = raw_val.loc[~(trader_overlap | targeted_ip_overlap)]
        else:
            val_df = raw_val

        if len(inner_train) == 0 or len(val_df) == 0:
            continue
        folds.append((inner_train.index.to_numpy(), val_df.index.to_numpy()))
    return folds


def build_preprocessor(feature_names: list[str], train_df: pd.DataFrame) -> ColumnTransformer:
    categorical_features = [
        feature
        for feature in feature_names
        if train_df[feature].dtype == object or str(train_df[feature].dtype).startswith("string")
    ]
    numeric_features = [feature for feature in feature_names if feature not in categorical_features]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("to_string", FunctionTransformer(_coerce_categorical_to_string, validate=False)),
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )


def _coerce_categorical_to_string(values: pd.DataFrame | np.ndarray) -> pd.DataFrame:
    frame = pd.DataFrame(values).copy()
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value: np.nan if pd.isna(value) else str(value))
    return frame


def winsorize_train_target(y_train: pd.Series) -> tuple[pd.Series, float, float]:
    lo = float(y_train.quantile(0.01))
    hi = float(y_train.quantile(0.99))
    return y_train.clip(lower=lo, upper=hi), lo, hi


def fit_and_predict(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_names: list[str],
    alpha: float,
) -> np.ndarray:
    X_train = train_df[feature_names]
    y_train = train_df["gross_loss_per_lot"]
    X_val = val_df[feature_names]

    y_train_w, _, _ = winsorize_train_target(y_train)
    preprocessor = build_preprocessor(feature_names, train_df)
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("ridge", Ridge(alpha=alpha)),
        ]
    )
    model.fit(X_train, y_train_w)
    return model.predict(X_val)


def spearman_rho(y_true: pd.Series, y_pred: Iterable[float]) -> float:
    pred_series = pd.Series(np.asarray(list(y_pred)), index=y_true.index)
    return float(y_true.corr(pred_series, method="spearman"))


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float | int]:
    flagged = y_pred > HURDLE
    if flagged.any():
        flagged_mean = float(y_true.loc[flagged].mean())
        coverage = float(flagged.mean())
        n_flagged = int(flagged.sum())
    else:
        flagged_mean = np.nan
        coverage = 0.0
        n_flagged = 0
    return {
        "spearman_rho": spearman_rho(y_true, y_pred),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "flagged_mean_loss_per_lot": flagged_mean,
        "flagged_coverage": coverage,
        "n_flagged": n_flagged,
    }


def select_alpha(train_df: pd.DataFrame, feature_names: list[str], track: str) -> float:
    inner_folds = make_inner_folds(train_df, track=track)
    if not inner_folds:
        return 1.0

    score_rows: list[dict[str, float]] = []
    for alpha in ALPHA_GRID:
        fold_scores = []
        for inner_train_idx, inner_val_idx in inner_folds:
            inner_train = train_df.loc[inner_train_idx]
            inner_val = train_df.loc[inner_val_idx]
            preds = fit_and_predict(inner_train, inner_val, feature_names, alpha)
            metrics = evaluate_predictions(inner_val["gross_loss_per_lot"], preds)
            fold_scores.append(metrics)

        mean_spearman = float(np.nanmean([row["spearman_rho"] for row in fold_scores]))
        mean_mae = float(np.nanmean([row["mae"] for row in fold_scores]))
        score_rows.append({"alpha": alpha, "mean_spearman": mean_spearman, "mean_mae": mean_mae})

    score_df = pd.DataFrame(score_rows).sort_values(
        ["mean_spearman", "mean_mae", "alpha"],
        ascending=[False, True, True],
    )
    return float(score_df.iloc[0]["alpha"])


def evaluate_track(primary: pd.DataFrame, track: str) -> tuple[list[FoldResult], dict[str, pd.DataFrame]]:
    folds = get_folds(primary, track=track)
    results: list[FoldResult] = []
    predictions_by_model: dict[str, list[pd.DataFrame]] = {model: [] for model in MODEL_FEATURES}

    for fold_idx, (train_idx, val_idx) in enumerate(folds, start=1):
        train_df = primary.loc[train_idx].copy()
        val_df = primary.loc[val_idx].copy()
        for model_name, feature_names in MODEL_FEATURES.items():
            alpha = select_alpha(train_df, feature_names, track=track)
            preds = fit_and_predict(train_df, val_df, feature_names, alpha)
            metrics = evaluate_predictions(val_df["gross_loss_per_lot"], preds)
            results.append(
                FoldResult(
                    model=model_name,
                    track=track,
                    fold=f"Fold {fold_idx}",
                    n_rows=int(len(val_df)),
                    alpha=alpha,
                    spearman_rho=metrics["spearman_rho"],
                    mae=metrics["mae"],
                    flagged_mean_loss_per_lot=metrics["flagged_mean_loss_per_lot"],
                    flagged_coverage=metrics["flagged_coverage"],
                    n_flagged=int(metrics["n_flagged"]),
                )
            )
            predictions_by_model[model_name].append(
                pd.DataFrame(
                    {
                        "actual": val_df["gross_loss_per_lot"].to_numpy(),
                        "pred": preds,
                    },
                    index=val_df.index,
                )
            )

    pooled_frames: dict[str, pd.DataFrame] = {}
    for model_name, frames in predictions_by_model.items():
        pooled = pd.concat(frames, axis=0).sort_index()
        pooled_frames[model_name] = pooled
        metrics = evaluate_predictions(pooled["actual"], pooled["pred"].to_numpy())
        results.append(
            FoldResult(
                model=model_name,
                track=track,
                fold="Pooled",
                n_rows=int(len(pooled)),
                alpha=None,
                spearman_rho=metrics["spearman_rho"],
                mae=metrics["mae"],
                flagged_mean_loss_per_lot=metrics["flagged_mean_loss_per_lot"],
                flagged_coverage=metrics["flagged_coverage"],
                n_flagged=int(metrics["n_flagged"]),
            )
        )
    return results, pooled_frames


def render_table(df: pd.DataFrame) -> str:
    lines = [
        "| model | fold | n_rows | alpha | spearman_rho | mae | flagged_mean_loss_per_lot | flagged_coverage | n_flagged |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in df.itertuples(index=False):
        alpha_text = "" if pd.isna(row.alpha) else f"{row.alpha:.4g}"
        flagged_mean = "" if pd.isna(row.flagged_mean_loss_per_lot) else f"{row.flagged_mean_loss_per_lot:.4f}"
        lines.append(
            f"| `{row.model}` | {row.fold} | {int(row.n_rows)} | {alpha_text} | "
            f"{row.spearman_rho:.4f} | {row.mae:.4f} | {flagged_mean} | {row.flagged_coverage:.2%} | {int(row.n_flagged)} |"
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    primary = build_primary_sample(args)

    all_results: list[FoldResult] = []
    pooled_frames_by_track: dict[str, dict[str, pd.DataFrame]] = {}
    for track in ("A", "B"):
        track_results, pooled_frames = evaluate_track(primary, track=track)
        all_results.extend(track_results)
        pooled_frames_by_track[track] = pooled_frames

    results_df = pd.DataFrame([result.__dict__ for result in all_results])

    pooled = results_df.loc[results_df["fold"] == "Pooled"].copy()
    m2_track_b_spearman = float(
        pooled.loc[(pooled["track"] == "B") & (pooled["model"] == "M2"), "spearman_rho"].iloc[0]
    )
    m3_track_b_spearman = float(
        pooled.loc[(pooled["track"] == "B") & (pooled["model"] == "M3"), "spearman_rho"].iloc[0]
    )
    m2_track_a_econ = float(
        pooled.loc[(pooled["track"] == "A") & (pooled["model"] == "M2"), "flagged_mean_loss_per_lot"].iloc[0]
    )
    m3_track_a_econ = float(
        pooled.loc[(pooled["track"] == "A") & (pooled["model"] == "M3"), "flagged_mean_loss_per_lot"].iloc[0]
    )
    decision = (
        m3_track_b_spearman > m2_track_b_spearman
        and (pd.isna(m2_track_a_econ) or pd.isna(m3_track_a_econ) or m3_track_a_econ >= 0.9 * m2_track_a_econ)
    )
    track_a_retention = np.nan
    if not pd.isna(m2_track_a_econ) and m2_track_a_econ != 0:
        track_a_retention = m3_track_a_econ / m2_track_a_econ

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Family G Value",
        "",
        "## Pre-Committed Interpretation",
        "",
        "Track B is expected to outperform Track A for `M3` specifically. This is mechanical: identity overlap is information, and Family G is built to use it, not evidence of superiority. Any `Track B > Track A` gap on `M3` is reported here as expected, not as a finding.",
        "",
        "## Decision Rule",
        "",
        "Include Family G in the Stage 3 composite if `M3` beats `M2` on **Track B pooled Spearman** and does **not** degrade the **Track A pooled economic metric** by more than 10%.",
        "",
        "## Modeling Setup",
        "",
        "- Ridge regression on `gross_loss_per_lot`.",
        "- Target winsorized at the 1st and 99th percentiles using the outer training fold only.",
        "- `alpha` selected by inner expanding campaign CV within each outer training fold.",
        "- Metrics are evaluated on raw validation targets; no validation-row statistics are used in fitting or clipping.",
        "",
        "Feature sets:",
        "",
        f"- `M1`: {', '.join(f'`{feature}`' for feature in MODEL_FEATURES['M1'])}",
        f"- `M2`: `M1` + {', '.join(f'`{feature}`' for feature in FAMILY_F_SURVIVORS)}",
        f"- `M3`: `M2` + {', '.join(f'`{feature}`' for feature in FAMILY_G_SURVIVORS)}",
        "",
    ]

    for track in ("A", "B"):
        lines.extend(
            [
                f"## Track {track}",
                "",
                render_table(
                    results_df.loc[results_df["track"] == track, [
                        "model",
                        "fold",
                        "n_rows",
                        "alpha",
                        "spearman_rho",
                        "mae",
                        "flagged_mean_loss_per_lot",
                        "flagged_coverage",
                        "n_flagged",
                    ]]
                ),
                "",
            ]
        )

    decision_text = "INCLUDE" if decision else "DO NOT INCLUDE"
    lines.extend(
        [
            "## Inclusion Decision",
            "",
            f"Decision: **{decision_text}** Family G in the Stage 3 composite.",
            "",
            f"- `Track B pooled Spearman`: `M2={m2_track_b_spearman:.4f}`, `M3={m3_track_b_spearman:.4f}`.",
            f"- `Track A pooled economic metric` (mean realized gross loss/lot on flagged positions): `M2={m2_track_a_econ:.4f}`, `M3={m3_track_a_econ:.4f}`.",
            f"- `Track A` economic retention versus the 90% floor: `{track_a_retention:.2%}` retained (threshold: `90.00%`).",
            "",
        ]
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(results_df.to_string(index=False, float_format=lambda value: f"{value:.4f}" if isinstance(value, float) else str(value)))


if __name__ == "__main__":
    main()
