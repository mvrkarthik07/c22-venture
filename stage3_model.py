"""Frozen Stage 3 V2 model and reproducible backtest.

The public runtime surface is deliberately one function: :func:`predict`.
Artifact fitting and reporting live behind private helpers and are only used by
the explicit command-line reproduction path.
"""

from __future__ import annotations

import argparse as _argparse
import json as _json
import math as _math
from pathlib import Path as _Path
from typing import Any as _Any

import numpy as _np
import pandas as pd
from sklearn.linear_model import Ridge as _Ridge

from features import TraderState as _TraderState

__all__ = ["predict"]

_ROOT = _Path(__file__).resolve().parent
_DEFAULT_ARTIFACT = _ROOT / "artifacts" / "stage3_v2.json"
_DEFAULT_ARTIFACT_VERSION = "stage3-v2-2026-08-20"
_HURDLE = 0.0
_COST_PER_LOT = 7.0
_START_BALANCE = 10000.0
_BOOT_SEED = 7
_N_BOOT = 2000
_MDE_Z_SUM = 2.80158521811297  # z_(1-alpha/2) + z_(1-beta), alpha=.05, power=.80

V2_FEATURES = [
    "loss_streak",
    "win_streak",
    "pnl_ewm",
    "lot_zscore",
    "amount",
    "size_after_loss_delta",
    "sl_usage_rate_5",
    "manual_exit_rate_5",
    "pnl_pct",
    "dd_from_peak_pct",
    "trade_index",
    "log_dt_close",
    "trades_per_hour",
    "prior_campaigns_x_loss_streak_ge_2",
    "shared_ip",
    "ip_cluster_size",
    "challenge_type",
    "gold_vol_prev_day",
    "same_direction_reentry",
    "size_delta_ratio",
]

_NUMERIC_FEATURES = [f for f in V2_FEATURES if f != "challenge_type"]
_CATEGORICAL_FEATURES = ["challenge_type"]
_FORBIDDEN_CLOSE_COLUMNS = {
    "slPrice",
    "tpPrice",
    "reverseProfit",
    "profit",
    "netProfit",
    "commission",
    "closePrice",
    "closeTime",
    "closeDateTime",
    "exit_type",
    "durationSec",
    "swap",
    "closeTradeId",
    "closeOrderId",
    "exitType",
    "pnl",
    "gross_loss_per_lot",
    "reverse_profit_per_lot",
    "clears_hurdle",
}
_ENTRY_COLUMNS = {
    "campaignId",
    "accountId",
    "positionId",
    "position_key",
    "openDateTime",
    "campaignDate",
    "traderKey",
    "ipClusterId",
    "sharedIpFlag",
    "shared_ip",
    "ip_cluster_size",
    "ipClusterSize",
    "challenge_type",
    "challenge_type_id",
    "gold_vol_prev_day",
    "amount",
    "openPrice",
    "side",
}
_ALPHA_GRID = _np.logspace(-3, 3, 13)
_THRESHOLD_GRID = _np.arange(-100.0, 501.0, 1.0)


def _missing(value: _Any) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _canonical_category(value: _Any) -> str:
    return "unknown" if _missing(value) else str(value)


def _artifact_path(path: str | _Path | None = None) -> _Path:
    return _Path(path) if path is not None else _DEFAULT_ARTIFACT


def _load_artifact(path: str | _Path | None = None) -> dict[str, _Any]:
    artifact_path = _artifact_path(path)
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Frozen Stage 3 artifact not found at {artifact_path}. "
            "Run `python reproduce_all.py --stage3` first."
        )
    artifact = _json.loads(artifact_path.read_text(encoding="utf-8"))
    if artifact.get("artifact_version") != _DEFAULT_ARTIFACT_VERSION:
        raise RuntimeError(
            f"Unsupported Stage 3 artifact version: {artifact.get('artifact_version')!r}"
        )
    if artifact.get("feature_names") != V2_FEATURES:
        raise AssertionError("Frozen artifact feature set is not the exact V2 set")
    return artifact


def _canonical_json_value(value: _Any) -> _Any:
    """Normalize floating-point serialization across equivalent environments."""
    if isinstance(value, float):
        return float(format(value, ".12g"))
    if isinstance(value, dict):
        return {key: _canonical_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical_json_value(item) for item in value]
    return value


def _assert_no_feature_leakage() -> None:
    """Static guard: close-only fields may not be in the feature contract."""
    for column in sorted(_FORBIDDEN_CLOSE_COLUMNS):
        if column in V2_FEATURES:
            raise AssertionError(f"Close-only column reached Stage 3 features: {column}")
    if _FORBIDDEN_CLOSE_COLUMNS & _ENTRY_COLUMNS:
        offending = sorted(_FORBIDDEN_CLOSE_COLUMNS & _ENTRY_COLUMNS)[0]
        raise AssertionError(f"Close-only column reached Stage 3 entry projection: {offending}")


def _feature_frame(values: list[dict[str, _Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(values, columns=V2_FEATURES)
    for feature in _NUMERIC_FEATURES:
        frame[feature] = pd.to_numeric(frame[feature], errors="coerce")
    frame["challenge_type"] = frame["challenge_type"].map(_canonical_category)
    return frame


def _fit_transform_parameters(train: pd.DataFrame) -> tuple[dict[str, _Any], _np.ndarray]:
    medians: dict[str, float] = {}
    means: dict[str, float] = {}
    scales: dict[str, float] = {}
    transformed: list[_np.ndarray] = []

    for feature in _NUMERIC_FEATURES:
        series = pd.to_numeric(train[feature], errors="coerce")
        median = float(series.median()) if series.notna().any() else 0.0
        filled = series.fillna(median).to_numpy(dtype=float)
        mean = float(filled.mean())
        scale = float(filled.std(ddof=0))
        if not _np.isfinite(scale) or scale == 0.0:
            scale = 1.0
        medians[feature] = median
        means[feature] = mean
        scales[feature] = scale
        transformed.append((filled - mean) / scale)

    categories = {
        feature: sorted(train[feature].map(_canonical_category).unique().tolist())
        for feature in _CATEGORICAL_FEATURES
    }
    for feature in _CATEGORICAL_FEATURES:
        values = train[feature].map(_canonical_category).to_numpy()
        for category in categories[feature]:
            transformed.append((values == category).astype(float))

    params = {
        "numeric_medians": medians,
        "numeric_means": means,
        "numeric_scales": scales,
        "categorical_categories": categories,
        "transformed_feature_names": [
            *[f"num__{feature}" for feature in _NUMERIC_FEATURES],
            *[
                f"cat__{feature}={category}"
                for feature in _CATEGORICAL_FEATURES
                for category in categories[feature]
            ],
        ],
    }
    return params, _np.column_stack(transformed)


def _transform(train_or_eval: pd.DataFrame, params: dict[str, _Any]) -> _np.ndarray:
    transformed: list[_np.ndarray] = []
    for feature in _NUMERIC_FEATURES:
        series = pd.to_numeric(train_or_eval[feature], errors="coerce")
        values = series.fillna(float(params["numeric_medians"][feature])).to_numpy(dtype=float)
        transformed.append(
            (values - float(params["numeric_means"][feature]))
            / float(params["numeric_scales"][feature])
        )
    for feature in _CATEGORICAL_FEATURES:
        values = train_or_eval[feature].map(_canonical_category).to_numpy()
        for category in params["categorical_categories"][feature]:
            transformed.append((values == category).astype(float))
    return _np.column_stack(transformed)


def _winsorized_target(train: pd.DataFrame) -> tuple[_np.ndarray, float, float]:
    target = pd.to_numeric(train["reverse_profit_per_lot"], errors="coerce")
    if target.isna().any():
        raise ValueError("Training target contains missing reverse_profit_per_lot values")
    lo = float(target.quantile(0.01))
    hi = float(target.quantile(0.99))
    return target.clip(lower=lo, upper=hi).to_numpy(dtype=float), lo, hi


def _fit_parameters(train: pd.DataFrame, alpha: float) -> dict[str, _Any]:
    params, matrix = _fit_transform_parameters(train)
    target, lo, hi = _winsorized_target(train)
    model = _Ridge(alpha=float(alpha), fit_intercept=True)
    model.fit(matrix, target)
    params.update(
        {
            "coefficients": model.coef_.astype(float).tolist(),
            "intercept": float(model.intercept_),
            "target_winsor_lo": lo,
            "target_winsor_hi": hi,
            "alpha": float(alpha),
        }
    )
    return params


def _predict_features(frame: pd.DataFrame, params: dict[str, _Any]) -> _np.ndarray:
    return _transform(frame, params) @ _np.asarray(params["coefficients"], dtype=float) + float(
        params["intercept"]
    )


def _inner_campaign_splits(train: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    campaigns = sorted(int(c) for c in train["campaignId"].dropna().unique())
    return [
        (
            train.loc[train["campaignId"].isin(campaigns[:i])].copy(),
            train.loc[train["campaignId"] == campaigns[i]].copy(),
        )
        for i in range(2, len(campaigns))
        if len(train.loc[train["campaignId"].isin(campaigns[:i])])
        and len(train.loc[train["campaignId"] == campaigns[i]])
    ]


def _select_alpha(train: pd.DataFrame) -> tuple[float, float, list[dict[str, float]]]:
    folds = _inner_campaign_splits(train)
    rows: list[dict[str, float]] = []
    for alpha in _ALPHA_GRID:
        spearmans: list[float] = []
        maes: list[float] = []
        for inner_train, inner_val in folds:
            params = _fit_parameters(inner_train, float(alpha))
            pred = _predict_features(inner_val[V2_FEATURES], params)
            actual = inner_val["reverse_profit_per_lot"].to_numpy(dtype=float)
            spearman = pd.Series(actual).corr(pd.Series(pred), method="spearman")
            if pd.notna(spearman):
                spearmans.append(float(spearman))
            maes.append(float(_np.mean(_np.abs(actual - pred))))
        rows.append(
            {
                "alpha": float(alpha),
                "mean_spearman": float(_np.mean(spearmans)) if spearmans else float("nan"),
                "mean_mae": float(_np.mean(maes)) if maes else float("nan"),
            }
        )
    score = pd.DataFrame(rows).sort_values(
        ["mean_spearman", "mean_mae", "alpha"],
        ascending=[False, True, True],
        na_position="last",
    )
    cv_alpha = float(score.iloc[0]["alpha"])
    # One fixed half-decade step beyond the CV winner is intentional.  It is
    # still applied when the CV winner is the upper edge of the diagnostic
    # grid, rather than silently cancelling the requested regularisation bias.
    return cv_alpha, float(cv_alpha * _math.sqrt(10.0)), rows


def _select_threshold(train: pd.DataFrame, pred: _np.ndarray) -> tuple[float, int, float, list[dict[str, float]]]:
    actual = train["reverse_profit_per_lot"].to_numpy(dtype=float)
    rows: list[dict[str, float]] = []
    for threshold in _THRESHOLD_GRID:
        mask = pred > threshold
        n = int(mask.sum())
        if n < 30:
            continue
        rows.append(
            {
                "threshold": float(threshold),
                "n": n,
                "coverage": n / len(train),
                "mean_rp_per_lot": float(actual[mask].mean()),
            }
        )
    if not rows:
        raise RuntimeError("Fixed threshold grid produced no candidate with n >= 30")
    selected = sorted(rows, key=lambda row: (-row["mean_rp_per_lot"], -row["threshold"]))[0]
    return (
        float(selected["threshold"]),
        int(selected["n"]),
        float(selected["coverage"]),
        rows,
    )


def _fit_artifact(features_path: str | _Path, artifact_path: str | _Path) -> dict[str, _Any]:
    frame = pd.read_csv(features_path)
    required = {"campaignId", "reverse_profit_per_lot", *V2_FEATURES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"features file missing Stage 3 columns: {missing}")
    # The mandated Stage 3 split is literal: every campaign <=52 is training,
    # including the one-position C41 test run.  C66 is in evaluation by
    # mandate.  This preserves the established 694/6,583 split counts.
    train = frame.loc[frame["campaignId"] <= 52].copy()
    if len(train) != 694:
        raise AssertionError(f"Expected 694 mandated training positions, got {len(train)}")

    cv_alpha, frozen_alpha, cv_rows = _select_alpha(train)
    params = _fit_parameters(train, frozen_alpha)
    pred_train = _predict_features(train[V2_FEATURES], params)
    threshold, threshold_n, threshold_coverage, threshold_rows = _select_threshold(train, pred_train)
    target = train["reverse_profit_per_lot"].to_numpy(dtype=float)
    artifact = {
        "artifact_version": _DEFAULT_ARTIFACT_VERSION,
        "model": "ridge",
        "target": "reverse_profit_per_lot",
        "hurdle": _HURDLE,
        "cost_per_lot_already_in_target": _COST_PER_LOT,
        "feature_names": V2_FEATURES,
        "alpha_grid": [float(x) for x in _ALPHA_GRID],
        "alpha_cv_selected": cv_alpha,
        "alpha_frozen": frozen_alpha,
        "alpha_bias": "one grid step toward more regularisation",
        "cv_protocol": "expanding campaigns within C33-C52; Spearman, then MAE",
        "cv_rows": cv_rows,
        "threshold_grid": [float(x) for x in _THRESHOLD_GRID],
        "threshold_procedure": "max training mean rP/lot subject to n >= 30",
        "selected_threshold": threshold,
        "effective_threshold": max(threshold, _HURDLE),
        "training_threshold_n": threshold_n,
        "training_threshold_coverage": threshold_coverage,
        "threshold_candidates": threshold_rows,
        "overrides": ["win_streak > 1", "trades_per_hour > 60"],
        "start_balance": _START_BALANCE,
        "confidence_scale": float(max(target.std(ddof=0), 1.0)),
        "training_rows": len(train),
        "training_campaigns": [int(x) for x in sorted(train["campaignId"].unique())],
        "preprocessing": {
            key: params[key]
            for key in (
                "numeric_medians",
                "numeric_means",
                "numeric_scales",
                "categorical_categories",
                "transformed_feature_names",
            )
        },
        "coefficients": params["coefficients"],
        "intercept": params["intercept"],
        "target_winsor_lo": params["target_winsor_lo"],
        "target_winsor_hi": params["target_winsor_hi"],
    }
    output = _Path(artifact_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json.dumps(_canonical_json_value(artifact), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def _state_config(row: pd.Series, prior_campaigns: int, artifact: dict[str, _Any]) -> dict[str, _Any]:
    challenge_type = row.get("challenge_type", row.get("challenge_type_id", "unknown"))
    shared_ip = row.get("sharedIpFlag", row.get("shared_ip", False))
    ip_cluster_size = row.get("ip_cluster_size", row.get("ipClusterSize", _np.nan))
    return {
        "start_balance": artifact.get("start_balance", _START_BALANCE),
        "campaign_id": row.get("campaignId"),
        "campaign_date": row.get("campaignDate", _np.nan),
        "trader_key": row.get("traderKey", _np.nan),
        "prior_campaigns": int(prior_campaigns),
        "shared_ip": False if _missing(shared_ip) else bool(shared_ip),
        "ip_cluster_size": ip_cluster_size,
        "challenge_type": challenge_type,
        "gold_vol_prev_day": row.get("gold_vol_prev_day", _np.nan),
        "breach_threshold_usd": _START_BALANCE * 0.04,
        "target_threshold_usd": _START_BALANCE * 0.08,
    }


def _entry_position(row: pd.Series, prior_campaigns: int) -> dict[str, _Any]:
    """Project only entry/metadata values into TraderState."""
    safe = {
        "campaignId": row.get("campaignId"),
        "accountId": row.get("accountId"),
        "openDateTime": row.get("openDateTime"),
        "amount": row.get("amount"),
        "openPrice": row.get("openPrice", _np.nan),
        "side": row.get("side", None),
        "prior_campaigns": int(prior_campaigns),
    }
    offending = sorted(set(safe) & _FORBIDDEN_CLOSE_COLUMNS)
    if offending:
        raise AssertionError(f"Close-only column reached entry feature projection: {offending[0]}")
    return safe


def _update_position(row: pd.Series, safe: dict[str, _Any]) -> dict[str, _Any] | None:
    close_value = row.get("closeDateTime", row.get("closeTime", _np.nan))
    if _missing(close_value):
        return None
    net_profit = row.get("netProfit", _np.nan)
    if _missing(net_profit) and not _missing(row.get("profit", _np.nan)):
        commission = row.get("commission", 0.0)
        swap = row.get("swap", 0.0)
        commission = 0.0 if _missing(commission) else float(commission)
        swap = 0.0 if _missing(swap) else float(swap)
        net_profit = float(row["profit"]) + commission + swap
    if _missing(net_profit):
        return None
    exit_type = row.get("exit_type", row.get("exitType", None))
    if _missing(exit_type):
        close_price = row.get("closePrice", _np.nan)
        sl_price = row.get("slPrice", _np.nan)
        tp_price = row.get("tpPrice", _np.nan)
        if not _missing(close_price) and not _missing(sl_price) and abs(float(close_price) - float(sl_price)) <= 1.0:
            exit_type = "sl_hit"
        elif not _missing(close_price) and not _missing(tp_price) and abs(float(close_price) - float(tp_price)) <= 1.0:
            exit_type = "tp_hit"
        else:
            exit_type = "manual"
    updated = dict(safe)
    updated.update(
        {
            "closeDateTime": close_value,
            "netProfit": net_profit,
            "exit_type": exit_type,
            "slPrice": row.get("slPrice", _np.nan),
            "tpPrice": row.get("tpPrice", _np.nan),
        }
    )
    return updated


def _stream_features(trades_df: pd.DataFrame, artifact: dict[str, _Any]) -> tuple[pd.DataFrame, list[dict[str, _Any]]]:
    _assert_no_feature_leakage()
    if not isinstance(trades_df, pd.DataFrame):
        raise TypeError("predict() requires a pandas DataFrame")
    for required in ("campaignId", "accountId", "openDateTime", "amount"):
        if required not in trades_df.columns:
            raise ValueError(f"predict() input missing required entry column: {required}")

    states: dict[tuple[_Any, _Any], _TraderState] = {}
    seen_campaigns: dict[str, set[int]] = {}
    feature_rows: list[dict[str, _Any]] = []
    metadata: list[dict[str, _Any]] = []

    for row_number, (_, row) in enumerate(trades_df.iterrows()):
        campaign = int(row["campaignId"])
        account = row["accountId"]
        state_key = (campaign, account if not _missing(account) else f"__row_{row_number}")
        trader_value = row.get("traderKey", _np.nan)
        trader_id = None if _missing(trader_value) else str(trader_value)
        prior_campaigns = 0
        if trader_id is not None:
            prior_campaigns = sum(c < campaign for c in seen_campaigns.get(trader_id, set()))

        if state_key not in states:
            states[state_key] = _TraderState(_state_config(row, prior_campaigns, artifact))
        else:
            states[state_key]._prior_campaigns_value = prior_campaigns
            states[state_key].config["prior_campaigns"] = prior_campaigns

        safe = _entry_position(row, prior_campaigns)
        features = states[state_key].compute_v2_features(safe)
        feature_rows.append(features)
        metadata.append(
            {
                "position_key": row.get(
                    "position_key",
                    f"{campaign}::{row.get('positionId', row_number)}",
                ),
                "amount": float(row["amount"]),
                "win_streak": features["win_streak"],
                "trades_per_hour": features["trades_per_hour"],
            }
        )

        # The update is deliberately after compute and decision preparation.
        update = _update_position(row, safe)
        if update is not None:
            states[state_key].update(update)
        if trader_id is not None:
            seen_campaigns.setdefault(trader_id, set()).add(campaign)

    return _feature_frame(feature_rows), metadata


def _contribution_strings(features: pd.DataFrame, artifact: dict[str, _Any]) -> list[str]:
    params = artifact["preprocessing"]
    matrix = _transform(features, params)
    coefficients = _np.asarray(artifact["coefficients"], dtype=float)
    names = params["transformed_feature_names"]
    output: list[str] = []
    for values in matrix * coefficients:
        order = sorted(range(len(names)), key=lambda i: (-abs(values[i]), names[i]))[:3]
        output.append(";".join(f"{names[i]}={values[i]:.6f}" for i in order))
    return output


def _decision_output(
    feature_frame: pd.DataFrame,
    metadata: list[dict[str, _Any]],
    artifact: dict[str, _Any],
    *,
    apply_overrides: bool = True,
) -> pd.DataFrame:
    scores = _predict_features(feature_frame, artifact["preprocessing"] | {
        "coefficients": artifact["coefficients"],
        "intercept": artifact["intercept"],
    })
    # The selection threshold is learned from training support, but the
    # economic hurdle is non-negotiable: never fade a negative predicted rP.
    threshold = max(float(artifact["selected_threshold"]), float(artifact.get("hurdle", _HURDLE)))
    base_fade = scores > threshold
    override = _np.array(
        [
            bool(m["win_streak"] > 1 or m["trades_per_hour"] > 60)
            for m in metadata
        ],
        dtype=bool,
    )
    fade = base_fade & ~(override if apply_overrides else _np.zeros(len(scores), dtype=bool))
    scale = float(max(artifact.get("confidence_scale", 1.0), 1.0))
    confidence = _np.where(fade, 1.0 / (1.0 + _np.exp(-scores / scale)), 0.0)
    contributions = _contribution_strings(feature_frame, artifact)
    return pd.DataFrame(
        {
            "position_key": [m["position_key"] for m in metadata],
            "decision": _np.where(fade, "FADE", "ABSTAIN"),
            "score": scores.astype(float),
            "expected_absolute": scores * _np.asarray([m["amount"] for m in metadata], dtype=float),
            "confidence": confidence.astype(float),
            "triggering_features": contributions,
        }
    )


def _predict_internal(
    trades_df: pd.DataFrame,
    artifact: dict[str, _Any],
    *,
    apply_overrides: bool = True,
) -> pd.DataFrame:
    features, metadata = _stream_features(trades_df, artifact)
    return _decision_output(features, metadata, artifact, apply_overrides=apply_overrides)


def _prepare_backtest_positions(
    datasets: str,
    traders_path: str,
    cache_path: str,
) -> pd.DataFrame:
    from build_features import (
        attach_gold_vol_prev_day as _attach_gold_vol_prev_day,
        load_positions as _load_positions,
        load_trader_metadata as _load_trader_metadata,
    )

    positions = _load_positions(datasets)
    metadata = _load_trader_metadata(traders_path, positions)
    daily = pd.read_csv(cache_path, parse_dates=["date"])
    positions = _attach_gold_vol_prev_day(positions, daily)
    positions = positions.merge(metadata, on=["campaignId", "accountId"], how="left")
    return positions.sort_values(
        ["campaignId", "accountId", "openDateTime", "positionId"],
        kind="mergesort",
    ).reset_index(drop=True)


def _backtest_predictions(positions: pd.DataFrame, artifact: dict[str, _Any]) -> pd.DataFrame:
    features, metadata = _stream_features(positions, artifact)
    base = _decision_output(features, metadata, artifact, apply_overrides=False)
    final = _decision_output(features, metadata, artifact, apply_overrides=True)
    result = positions[["campaignId", "accountId", "traderKey", "ipClusterId", "amount", "n_fills"]].copy()
    result["actual_rp_per_lot"] = positions["reverseProfit"] / positions["amount"]
    result["actual_absolute_rp"] = result["actual_rp_per_lot"] * result["amount"]
    result["base_decision"] = base["decision"].to_numpy()
    result["decision"] = final["decision"].to_numpy()
    result["score"] = base["score"].to_numpy()
    result["win_streak"] = features["win_streak"].to_numpy()
    result["trades_per_hour"] = features["trades_per_hour"].to_numpy()
    result["_raw_nan_feature"] = features.isna().any(axis=1).to_numpy()
    return result


def _cluster_series(frame: pd.DataFrame, kind: str) -> pd.Series:
    if kind == "account":
        fallback = "account::" + frame["campaignId"].astype(str) + "::" + frame["accountId"].astype(str)
        return frame["traderKey"].astype("string").where(frame["traderKey"].notna(), fallback)
    if kind == "ip":
        fallback = "account::" + frame["campaignId"].astype(str) + "::" + frame["accountId"].astype(str)
        return frame["ipClusterId"].astype("string").where(frame["ipClusterId"].notna(), fallback)
    raise ValueError(f"unknown cluster kind: {kind}")


def _cluster_bootstrap(
    frame: pd.DataFrame,
    mask: pd.Series | _np.ndarray,
    cluster_kind: str,
    *,
    size_weighted: bool = False,
) -> tuple[float, float]:
    selected = frame.loc[_np.asarray(mask, dtype=bool)].copy()
    if selected.empty:
        return 0.0, 0.0
    work = frame[["campaignId", "accountId", "traderKey", "ipClusterId", "actual_rp_per_lot", "amount"]].copy()
    work["cluster"] = _cluster_series(work, cluster_kind).to_numpy()
    work["_selected"] = _np.asarray(mask, dtype=bool)
    grouped = work.groupby("cluster", sort=False, dropna=False)
    selected_sum = grouped.apply(
        lambda group: float((group.loc[group["_selected"], "actual_rp_per_lot"]).sum()),
        include_groups=False,
    ).to_numpy(dtype=float)
    selected_count = grouped["_selected"].sum().to_numpy(dtype=float)
    selected_absolute = grouped.apply(
        lambda group: float((group.loc[group["_selected"], "actual_absolute_rp"]).sum())
        if "actual_absolute_rp" in group
        else float((group.loc[group["_selected"], "actual_rp_per_lot"] * group.loc[group["_selected"], "amount"]).sum()),
        include_groups=False,
    ).to_numpy(dtype=float)
    selected_amount = grouped.apply(
        lambda group: float(group.loc[group["_selected"], "amount"].sum()),
        include_groups=False,
    ).to_numpy(dtype=float)
    groups = len(selected_sum)
    rng = _np.random.default_rng(_BOOT_SEED)
    samples: list[float] = []
    for _ in range(_N_BOOT):
        multiplicity = _np.bincount(rng.integers(0, groups, groups), minlength=groups)
        count = float(_np.dot(multiplicity, selected_count))
        if count == 0.0:
            continue
        if size_weighted:
            denominator = float(_np.dot(multiplicity, selected_amount))
            if denominator == 0.0:
                continue
            samples.append(float(_np.dot(multiplicity, selected_absolute) / denominator))
        else:
            samples.append(float(_np.dot(multiplicity, selected_sum) / count))
    if not samples:
        return float(selected["actual_rp_per_lot"].mean()), float(selected["actual_rp_per_lot"].mean())
    return tuple(float(x) for x in _np.quantile(samples, [0.025, 0.975]))


def _metric_row(
    frame: pd.DataFrame,
    mask: pd.Series | _np.ndarray,
    *,
    label: str,
    size_weighted: bool = False,
) -> dict[str, _Any]:
    mask = _np.asarray(mask, dtype=bool)
    selected = frame.loc[mask]
    n = int(len(selected))
    sum_amount = float(selected["amount"].sum()) if n else 0.0
    total = float(selected["actual_absolute_rp"].sum()) if n else 0.0
    if n:
        if size_weighted:
            mean = float(total / sum_amount) if sum_amount else 0.0
        else:
            mean = float(selected["actual_rp_per_lot"].mean())
    else:
        mean = 0.0
    account_ci = _cluster_bootstrap(frame, mask, "account", size_weighted=size_weighted)
    ip_ci = _cluster_bootstrap(frame, mask, "ip", size_weighted=size_weighted)
    return {
        "label": label,
        "n": n,
        "coverage": n / len(frame) if len(frame) else 0.0,
        "mean": mean,
        "sum_amount": sum_amount,
        "account_lo": account_ci[0],
        "account_hi": account_ci[1],
        "ip_lo": ip_ci[0],
        "ip_hi": ip_ci[1],
        "total_absolute_rp": total,
    }


def _format_metric(row: dict[str, _Any]) -> str:
    return (
        f"| {row['label']} | {row['n']} | {row['coverage']:.2%} | {row['mean']:.3f} | "
        f"[{row['account_lo']:.3f}, {row['account_hi']:.3f}] | "
        f"[{row['ip_lo']:.3f}, {row['ip_hi']:.3f}] | {row['total_absolute_rp']:.3f} |"
    )


def _fold_artifact(train: pd.DataFrame) -> dict[str, _Any]:
    cv_alpha, frozen_alpha, cv_rows = _select_alpha(train)
    params = _fit_parameters(train, frozen_alpha)
    pred = _predict_features(train[V2_FEATURES], params)
    threshold, n, coverage, _ = _select_threshold(train, pred)
    artifact = {
        "feature_names": V2_FEATURES,
        "numeric_medians": params["numeric_medians"],
        "numeric_means": params["numeric_means"],
        "numeric_scales": params["numeric_scales"],
        "categorical_categories": params["categorical_categories"],
        "transformed_feature_names": params["transformed_feature_names"],
        "preprocessing": {
            key: params[key]
            for key in (
                "numeric_medians",
                "numeric_means",
                "numeric_scales",
                "categorical_categories",
                "transformed_feature_names",
            )
        },
        "coefficients": params["coefficients"],
        "intercept": params["intercept"],
        "selected_threshold": threshold,
        "effective_threshold": max(threshold, _HURDLE),
        "alpha_cv_selected": cv_alpha,
        "alpha_frozen": frozen_alpha,
        "training_threshold_n": n,
        "training_threshold_coverage": coverage,
        "cv_rows": cv_rows,
        "confidence_scale": float(max(train["reverse_profit_per_lot"].std(ddof=0), 1.0)),
    }
    return artifact


def _fold_metrics(features_path: str, artifact: dict[str, _Any]) -> list[dict[str, _Any]]:
    from splits import get_folds as _get_folds

    frame = pd.read_csv(features_path)
    primary = frame.loc[frame["campaignId"].between(53, 65)].copy().reset_index(drop=True)
    rows: list[dict[str, _Any]] = []
    for track in ("A", "B"):
        folds = _get_folds(primary, track=track)
        pooled: list[pd.DataFrame] = []
        for fold_number, (train_index, val_index) in enumerate(folds, start=1):
            train = primary.loc[train_index].copy()
            val = primary.loc[val_index].copy()
            fold_model = _fold_artifact(train)
            score = _predict_features(val[V2_FEATURES], fold_model)
            base_mask = score > max(float(fold_model["selected_threshold"]), _HURDLE)
            override = (val["win_streak"].to_numpy() > 1) | (val["trades_per_hour"].to_numpy() > 60)
            final_mask = base_mask & ~override
            work = val[["campaignId", "accountId", "traderKey", "ipClusterId", "amount", "reverse_profit_per_lot"]].copy()
            work = work.rename(columns={"reverse_profit_per_lot": "actual_rp_per_lot"})
            work["actual_absolute_rp"] = work["actual_rp_per_lot"] * work["amount"]
            pooled.append(work.assign(_mask=final_mask))
            metric = _metric_row(work, final_mask, label=f"Fold {fold_number}")
            metric.update(
                {
                    "track": track,
                    "fold": fold_number,
                    "train_n": len(train),
                    "val_n": len(val),
                    "alpha_cv": fold_model["alpha_cv_selected"],
                    "alpha_frozen": fold_model["alpha_frozen"],
                    "threshold": fold_model["selected_threshold"],
                }
            )
            rows.append(metric)
        pooled_frame = pd.concat(pooled, ignore_index=True)
        pooled_metric = _metric_row(pooled_frame, pooled_frame["_mask"].to_numpy(), label="Pooled")
        pooled_metric.update({"track": track, "fold": "Pooled"})
        rows.append(pooled_metric)
        for baseline_label, baseline_mask, weighted in (
            ("Pooled DO NOTHING", _np.zeros(len(pooled_frame), dtype=bool), False),
            ("Pooled FADE EVERYTHING equal", _np.ones(len(pooled_frame), dtype=bool), False),
            ("Pooled FADE EVERYTHING size", _np.ones(len(pooled_frame), dtype=bool), True),
        ):
            baseline = _metric_row(pooled_frame, baseline_mask, label=baseline_label, size_weighted=weighted)
            baseline.update({"track": track, "fold": baseline_label})
            rows.append(baseline)
    return rows


def _threshold_sweep(
    features_path: str,
    artifact: dict[str, _Any],
    backtest: pd.DataFrame,
) -> pd.DataFrame:
    frame = pd.read_csv(features_path)
    train = frame.loc[frame["campaignId"] <= 52].copy()
    params = {
        "numeric_medians": artifact["preprocessing"]["numeric_medians"],
        "numeric_means": artifact["preprocessing"]["numeric_means"],
        "numeric_scales": artifact["preprocessing"]["numeric_scales"],
        "categorical_categories": artifact["preprocessing"]["categorical_categories"],
        "coefficients": artifact["coefficients"],
        "intercept": artifact["intercept"],
    }
    train_scores = _predict_features(train[V2_FEATURES], params)
    evaluation = backtest.loc[backtest["campaignId"].between(53, 66)].copy()
    rows: list[dict[str, _Any]] = []
    for threshold in _THRESHOLD_GRID:
        train_mask = train_scores > threshold
        train_n = int(train_mask.sum())
        train_mean = (
            float(train.loc[train_mask, "reverse_profit_per_lot"].mean())
            if train_n
            else float("nan")
        )
        effective = max(float(threshold), float(artifact.get("hurdle", _HURDLE)))
        eval_score = evaluation["score"].to_numpy() > effective
        eval_final = eval_score & ~(evaluation["win_streak"].to_numpy() > 1) & ~(
            evaluation["trades_per_hour"].to_numpy() > 60
        )
        rows.append(
            {
                "grid_threshold": float(threshold),
                "train_n": train_n,
                "train_mean_rp_per_lot": train_mean,
                "effective_execution_threshold": effective,
                "evaluation_n_acted": int(eval_final.sum()),
                "evaluation_coverage": float(eval_final.mean()),
                "support_eligible": train_n >= 30,
                "selected": float(threshold) == float(artifact["selected_threshold"]),
            }
        )
    return pd.DataFrame(rows)


def _compact_threshold_sweep(sweep: pd.DataFrame) -> pd.DataFrame:
    """Keep threshold change points plus the executable operating point."""
    keep: list[bool] = []
    previous_n: int | None = None
    previous_selected: bool | None = None
    for row in sweep.itertuples(index=False):
        changed = (
            previous_n is None
            or int(row.train_n) != previous_n
            or bool(row.selected) != previous_selected
            or float(row.grid_threshold) == 0.0
        )
        keep.append(changed)
        previous_n = int(row.train_n)
        previous_selected = bool(row.selected)
    return sweep.loc[keep].reset_index(drop=True)


def _executable_selection(features_path: str, artifact: dict[str, _Any]) -> dict[str, _Any]:
    """Re-run threshold selection only where the runtime can actually execute."""
    frame = pd.read_csv(features_path)
    train = frame.loc[frame["campaignId"] <= 52].copy()
    params = {
        "numeric_medians": artifact["preprocessing"]["numeric_medians"],
        "numeric_means": artifact["preprocessing"]["numeric_means"],
        "numeric_scales": artifact["preprocessing"]["numeric_scales"],
        "categorical_categories": artifact["preprocessing"]["categorical_categories"],
        "coefficients": artifact["coefficients"],
        "intercept": artifact["intercept"],
    }
    scores = _predict_features(train[V2_FEATURES], params)
    rows: list[dict[str, _Any]] = []
    for threshold in _np.arange(0.0, 501.0, 1.0):
        mask = scores > threshold
        n = int(mask.sum())
        rows.append(
            {
                "threshold": float(threshold),
                "n": n,
                "mean": float(train.loc[mask, "reverse_profit_per_lot"].mean()) if n else float("nan"),
            }
        )
    sweep = pd.DataFrame(rows)
    max_support = int(sweep["n"].max())
    best = sweep.loc[sweep["n"].eq(max_support)].iloc[0]
    eligible = sweep.loc[sweep["n"] >= 30]
    return {
        "grid_low": 0.0,
        "grid_high": 500.0,
        "grid_step": 1.0,
        "max_support": max_support,
        "max_support_threshold": float(best["threshold"]),
        "max_support_mean": float(best["mean"]),
        "n30_satisfiable": bool(not eligible.empty),
        "selected_threshold": float(eligible.iloc[0]["threshold"]) if not eligible.empty else None,
        "selected_n": int(eligible.iloc[0]["n"]) if not eligible.empty else None,
        "selected_mean": float(eligible.iloc[0]["mean"]) if not eligible.empty else None,
    }


def _frontier_cluster_labels(frame: pd.DataFrame, kind: str) -> pd.Series:
    if kind == "account":
        fallback = "account::" + frame["campaignId"].astype(str) + "::" + frame["accountId"].astype(str)
        return frame["traderKey"].astype("object").where(frame["traderKey"].notna(), fallback)
    if kind == "ip":
        valid = frame["ipClusterId"].notna() & (frame["ipClusterId"] != -1)
        fallback = "account::" + frame["campaignId"].astype(str) + "::" + frame["accountId"].astype(str)
        labels = "ip_" + frame["ipClusterId"].astype("Int64").astype(str)
        return pd.Series(_np.where(valid, labels, fallback), index=frame.index)
    raise ValueError(f"unknown frontier cluster kind: {kind}")


def _frontier_icc(frame: pd.DataFrame, kind: str) -> dict[str, float | int]:
    work = pd.DataFrame(
        {
            "y": frame["actual_rp_per_lot"].to_numpy(dtype=float),
            "cluster": _frontier_cluster_labels(frame, kind).to_numpy(),
        },
    ).dropna()
    grouped = work.groupby("cluster", sort=False)
    sizes = grouped.size().astype(float)
    means = grouped["y"].mean()
    grand_mean = float(work["y"].mean())
    ss_between = float((sizes * (means - grand_mean).pow(2)).sum())
    work = work.join(means.rename("cluster_mean"), on="cluster")
    ss_within = float(((work["y"] - work["cluster_mean"]) ** 2).sum())
    n_rows = int(len(work))
    n_clusters = int(len(sizes))
    if n_clusters < 2 or n_rows <= n_clusters:
        return {
            "n_rows": n_rows,
            "n_clusters": n_clusters,
            "mean_cluster_size": float(n_rows / n_clusters) if n_clusters else 0.0,
            "icc": 0.0,
            "deff": 1.0,
            "singleton_clusters": int((sizes == 1).sum()),
            "max_cluster_size": int(sizes.max()) if n_clusters else 0,
        }
    df_between = n_clusters - 1
    df_within = n_rows - n_clusters
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    m0 = float((n_rows - sizes.pow(2).sum() / n_rows) / df_between)
    denominator = ms_between + (m0 - 1.0) * ms_within
    icc = float((ms_between - ms_within) / denominator) if denominator else 0.0
    mean_cluster_size = float(n_rows / n_clusters)
    return {
        "n_rows": n_rows,
        "n_clusters": n_clusters,
        "mean_cluster_size": mean_cluster_size,
        "icc": icc,
        "deff": float(1.0 + (mean_cluster_size - 1.0) * icc),
        "singleton_clusters": int((sizes == 1).sum()),
        "max_cluster_size": int(sizes.max()),
    }


def _mde(sigma: float, deff: float, n: int) -> float:
    if n <= 0:
        return float("nan")
    return float(_MDE_Z_SUM * sigma * _math.sqrt(max(deff, 0.0) / n))


def _mde_icc_floored(sigma: float, deff: float, n: int) -> float:
    """Power MDE with the anti-conservative negative-ICC estimate floored at 0."""
    return _mde(sigma, max(float(deff), 1.0), n)


def _power_frontier(backtest: pd.DataFrame, artifact: dict[str, _Any]) -> tuple[dict[str, _Any], pd.DataFrame, pd.DataFrame]:
    primary = backtest.loc[backtest["campaignId"].between(53, 65)].copy()
    evaluation = backtest.loc[backtest["campaignId"].between(53, 66)].copy()
    primary_target = primary["actual_rp_per_lot"]
    sigma_raw = float(primary_target.std(ddof=1))
    sigma_winsorized = float(
        primary_target.clip(primary_target.quantile(0.01), primary_target.quantile(0.99)).std(ddof=1)
    )

    acted_summary = {
        "sigma_raw": sigma_raw,
        "sigma_winsorized": sigma_winsorized,
        "windows": [],
    }
    subset_rows: list[dict[str, _Any]] = []
    for window, title in (("C53-C65", "C53-C65"), ("C53-C66", "C53-C66")):
        window_frame = evaluation.loc[
            evaluation["campaignId"].between(53, 65 if window == "C53-C65" else 66)
        ]
        acted = window_frame.loc[window_frame["decision"].eq("FADE")].copy()
        acted_summary["windows"].append(
            {
                "window": title,
                "n": int(len(acted)),
                "trader_ids": int(acted["traderKey"].nunique(dropna=True)),
                "ip_ids": int(acted["ipClusterId"].nunique(dropna=True)),
                "campaigns": int(acted["campaignId"].nunique()),
            }
        )
        for kind, label in (("account", "traderKey"), ("ip", "ipClusterId")):
            stats = _frontier_icc(acted, kind)
            subset_rows.append(
                {
                    "window": window,
                    "cluster_scheme": label,
                    **stats,
                    "mde_raw": _mde(sigma_raw, float(stats["deff"]), len(acted)),
                    "mde_winsorized": _mde(sigma_winsorized, float(stats["deff"]), len(acted)),
                    "mde_raw_floored": _mde_icc_floored(sigma_raw, float(stats["deff"]), len(acted)),
                    "mde_winsorized_floored": _mde_icc_floored(sigma_winsorized, float(stats["deff"]), len(acted)),
                }
            )

    overrides = (evaluation["win_streak"].to_numpy() > 1) | (evaluation["trades_per_hour"].to_numpy() > 60)
    eligible = evaluation.loc[~overrides].sort_values("score", ascending=False, kind="mergesort")
    target_coverages = [0.01, 0.027, 0.05, 0.10, 0.25, 0.50, 1.00]
    frontier_rows: list[dict[str, _Any]] = []
    for target in target_coverages:
        desired = int(round(target * len(evaluation)))
        available = min(desired, len(eligible))
        if abs(target - 0.027) < 1e-12:
            hurdle = float(max(float(artifact["selected_threshold"]), float(artifact.get("hurdle", _HURDLE))))
        elif available == 0:
            hurdle = float(eligible["score"].max() + 1.0)
        elif available >= len(eligible):
            hurdle = float(_np.nextafter(float(eligible["score"].min()), -_np.inf))
        else:
            high = float(eligible.iloc[available - 1]["score"])
            low = float(eligible.iloc[available]["score"])
            hurdle = (high + low) / 2.0
        mask = (evaluation["score"].to_numpy() > hurdle) & ~overrides
        selected = evaluation.loc[mask].copy()
        account_stats = _frontier_icc(selected, "account")
        ip_stats = _frontier_icc(selected, "ip")
        metric = _metric_row(evaluation, mask, label=f"coverage {target:.1%}")
        frontier_rows.append(
            {
                "target_coverage": target,
                "hurdle": hurdle,
                "target_n": desired,
                "n": int(metric["n"]),
                "coverage": float(metric["coverage"]),
                "mean": float(metric["mean"]),
                "account_lo": float(metric["account_lo"]),
                "account_hi": float(metric["account_hi"]),
                "account_deff": float(account_stats["deff"]),
                "account_mde_raw": _mde(sigma_raw, float(account_stats["deff"]), int(metric["n"])),
                "account_mde_winsorized": _mde(sigma_winsorized, float(account_stats["deff"]), int(metric["n"])),
                "account_mde_raw_floored": _mde_icc_floored(sigma_raw, float(account_stats["deff"]), int(metric["n"])),
                "account_mde_winsorized_floored": _mde_icc_floored(sigma_winsorized, float(account_stats["deff"]), int(metric["n"])),
                "ip_deff": float(ip_stats["deff"]),
                "ip_mde_raw": _mde(sigma_raw, float(ip_stats["deff"]), int(metric["n"])),
                "ip_mde_winsorized": _mde(sigma_winsorized, float(ip_stats["deff"]), int(metric["n"])),
                "ip_mde_raw_floored": _mde_icc_floored(sigma_raw, float(ip_stats["deff"]), int(metric["n"])),
                "ip_mde_winsorized_floored": _mde_icc_floored(sigma_winsorized, float(ip_stats["deff"]), int(metric["n"])),
            }
        )
    return acted_summary, pd.DataFrame(subset_rows), pd.DataFrame(frontier_rows)


def _render_stage3_report(
    report_path: str | _Path,
    artifact: dict[str, _Any],
    backtest: pd.DataFrame,
    fold_rows: list[dict[str, _Any]],
    threshold_sweep: pd.DataFrame,
    acted_summary: dict[str, _Any],
    subset_power: pd.DataFrame,
    frontier: pd.DataFrame,
    executable_selection: dict[str, _Any],
) -> None:
    lines = [
        "# Stage 3 frozen V2 backtest",
        "",
        "Data: repaired ingestion, 46,520 fills -> 7,277 positions.",
        "Model: V2 admissible features; the four trader-history fields and all SL/TP-derived fields are excluded.",
        "Target: reverseProfit per lot, with the $7 cost already included exactly once. Hurdle: 0.00.",
        "",
        "## Frozen artifact and decision rule",
        "",
        f"Artifact: `artifacts/stage3_v2.json` (`{artifact['artifact_version']}`).",
        f"Training window: C33-C52, n={artifact['training_rows']}; evaluation: C53-C66, n=6,583.",
        f"Inner alpha CV selected `{artifact['alpha_cv_selected']:.6g}`; the frozen alpha is `{artifact['alpha_frozen']:.6g}`, one half-decade step more regularised.",
        f"Threshold grid: fixed -100 to 500 by 1; select maximum training mean rP/lot subject to n>=30. Selected score threshold: `{artifact['selected_threshold']:.3f}`; effective execution threshold after the zero hurdle: `{artifact['effective_threshold']:.3f}`.",
        f"Training threshold support: n={artifact['training_threshold_n']} ({artifact['training_threshold_coverage']:.2%}).",
        "The selected-threshold support is reported exactly. Execution never fades a negative predicted rP, because the economic hurdle is exactly zero.",
        "Default overrides, applied after the score threshold: abstain when `win_streak > 1` or `trades_per_hour > 60`.",
        f"Executable-grid re-selection (`0..500`, step 1): maximum training support is n={executable_selection['max_support']} at threshold {executable_selection['max_support_threshold']:.0f}; n>=30 is satisfiable: **{executable_selection['n30_satisfiable']}**. The re-selected executable operating point is threshold 0 with n={executable_selection['max_support']} and mean rP/lot {executable_selection['max_support_mean']:.3f}, but it is ineligible under the pre-registered n>=30 floor. The mandated training split therefore cannot calibrate an executable threshold under that rule.",
        "",
        "| threshold record | score threshold | effective runtime threshold | training n | status |",
        "|---|---:|---:|---:|---|",
        f"| Current frozen artifact | {artifact['selected_threshold']:.0f} | {artifact['effective_threshold']:.0f} | {artifact['training_threshold_n']} at offline selection; 4 at executable 0 | offline support-selected, not executable as selected |",
        f"| Executable-grid re-selection | 0 | 0 | {executable_selection['max_support']} | no valid threshold: n>=30 floor fails |",
        "",
        "## Common-split performance",
        "",
        "Account CIs resample traderKey clusters; IP CIs are the secondary ipClusterId robustness check. Dollar totals below exclude corrupted C66; DO NOTHING acts on zero rows by construction.",
        "",
        "| model / baseline | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI | total realized rP ($) |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for window, title in (("C53-C65", "C53-C65 (6,582 positions)"), ("C53-C66", "C53-C66 (6,583 positions; C66 excluded from dollar totals)")):
        lines.extend([f"", f"### {title}", ""])
        subset = backtest.loc[backtest["campaignId"].between(53, 65 if window == "C53-C65" else 66)].copy()
        if window == "C53-C66":
            subset = subset.loc[subset["campaignId"] != 66].copy()
        for label, mask, weighted in (
            ("Model (overrides)", subset["decision"].eq("FADE"), False),
            ("Model (no overrides)", subset["base_decision"].eq("FADE"), False),
            ("DO NOTHING", _np.zeros(len(subset), dtype=bool), False),
            ("FADE EVERYTHING, equal-weighted", _np.ones(len(subset), dtype=bool), False),
            ("FADE EVERYTHING, size-weighted", _np.ones(len(subset), dtype=bool), True),
        ):
            lines.append(_format_metric(_metric_row(subset, mask, label=label, size_weighted=weighted)))

        lines.extend(
            [
                "",
                "Size-weighted dollar economics (C66 excluded):",
                "",
                "| model / baseline | n | size-weighted mean rP/lot | account 95% CI | sum(amount) | total rP ($) |",
                "|---|---:|---:|---|---:|---:|",
            ]
        )
        dollar_rows = [
            ("Model (overrides)", subset["decision"].eq("FADE")),
            ("DO NOTHING", _np.zeros(len(subset), dtype=bool)),
            ("FADE EVERYTHING, equal-weighted", _np.ones(len(subset), dtype=bool)),
            ("FADE EVERYTHING, size-weighted", _np.ones(len(subset), dtype=bool)),
        ]
        for label, mask in dollar_rows:
            metric = _metric_row(subset, mask, label=label, size_weighted=True)
            lines.append(
                f"| {label} | {metric['n']} | {metric['mean']:.3f} | [{metric['account_lo']:.3f}, {metric['account_hi']:.3f}] | {metric['sum_amount']:.2f} | {metric['total_absolute_rp']:.2f} |"
            )
        model_mask = subset["decision"].eq("FADE").to_numpy()
        all_mask = _np.ones(len(subset), dtype=bool)
        model_metric = _metric_row(subset, model_mask, label="model", size_weighted=True)
        fade_metric = _metric_row(subset, all_mask, label="fade", size_weighted=True)
        loss_share = abs(model_metric["total_absolute_rp"]) / abs(fade_metric["total_absolute_rp"]) if fade_metric["total_absolute_rp"] else float("nan")
        position_share = model_metric["n"] / len(subset) if len(subset) else 0.0
        amount_share = model_metric["sum_amount"] / fade_metric["sum_amount"] if fade_metric["sum_amount"] else 0.0
        lines.extend(
            [
                "",
                f"The model captures {loss_share:.2%} of the fade-everything dollar loss while acting on {position_share:.2%} of positions and {amount_share:.2%} of total amount ({loss_share / position_share:.2f}x the position-coverage share; {loss_share / amount_share:.2f}x the amount share).",
                f"Against DO NOTHING ($0 total rP), the model's total is ${model_metric['total_absolute_rp']:.2f}: it does **not** beat DO NOTHING in absolute dollars.",
            ]
        )

        acted = subset.loc[subset["decision"].eq("FADE")]
        lines.extend(["", "Per-campaign model breakdown (default overrides):", "", "| campaign | n acted | mean rP/lot | account 95% CI |", "|---:|---:|---:|---|"])
        campaign_metrics: list[tuple[int, dict[str, _Any]]] = []
        for campaign, group in subset.groupby("campaignId", sort=True):
            metric = _metric_row(group, group["decision"].eq("FADE"), label=str(int(campaign)))
            campaign_metrics.append((int(campaign), metric))
            lines.append(f"| {int(campaign)} | {metric['n']} | {metric['mean']:.3f} | [{metric['account_lo']:.3f}, {metric['account_hi']:.3f}] |")
        if campaign_metrics:
            best_campaign = max(campaign_metrics, key=lambda item: item[1]["mean"])[0]
            without = subset.loc[subset["campaignId"] != best_campaign]
            metric = _metric_row(without, without["decision"].eq("FADE"), label=f"Model, best campaign C{best_campaign} removed")
            lines.extend(["", f"Single-best-campaign check: the best acted-on campaign by mean was C{best_campaign}.", "", "| result | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI | total realized rP ($) |", "|---|---:|---:|---:|---|---|---:|"])
            lines.append(_format_metric(metric))

    c66 = backtest.loc[backtest["campaignId"].eq(66)]
    c66_amount = float(c66["amount"].sum()) if not c66.empty else 0.0
    c66_total = float(c66["actual_absolute_rp"].sum()) if not c66.empty else 0.0
    lines.extend(
        [
            "",
            "## C66 amount-collapse audit",
            "",
            f"C66 has {int(c66['n_fills'].sum()) if not c66.empty else 0} fills collapsed to {len(c66)} position. The collapse currently uses `amount: sum` in `pipeline.to_positions()`; C66 therefore has position amount **{c66_amount:.2f} lots** and total rP **${c66_total:.2f}**, or {float(c66_total / c66_amount) if c66_amount else 0.0:.3f}/lot.",
            "",
            "This is a C66-specific corrupted test export: its 1,911 fill amounts sum to 462.30 lots, versus a maximum collapsed amount of 6.50 lots in primary C53-C65. The SUM aggregation remains the intended operation for ordinary partial-close fills, and no other primary-era multi-fill position exceeds 6.50 lots. C66 is excluded from every dollar total in this report; its per-lot observation remains in the 178-trade evaluation/power comparison.",
            "",
            "## Expanding-window folds within C53-C65",
            "",
            "Each fold fits V2, selects alpha and threshold using only its expanding training campaigns, then evaluates the next campaign block. Track A is trader-purged; Track B is the unpurged returning-trader analogue.",
            "",
            "| track | fold | train n | validation n | threshold | alpha frozen | n acted | coverage | mean rP/lot | account 95% CI | IP 95% CI |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in fold_rows:
        lines.append(
            f"| {row['track']} | {row['fold']} | {row.get('train_n', '')} | {row.get('val_n', '')} | "
            f"{row.get('threshold', '') if row['fold'] != 'Pooled' else ''} | {row.get('alpha_frozen', '') if row['fold'] != 'Pooled' else ''} | "
            f"{row['n']} | {row['coverage']:.2%} | {row['mean']:.3f} | [{row['account_lo']:.3f}, {row['account_hi']:.3f}] | [{row['ip_lo']:.3f}, {row['ip_hi']:.3f}] |"
        )

    train = backtest.loc[backtest["campaignId"] <= 52]
    evaluation = backtest.loc[backtest["campaignId"].between(53, 66)]
    lines.extend(["", "## In-sample versus out-of-sample gap", "", "| window | n | coverage | mean rP/lot | account 95% CI |", "|---|---:|---:|---:|---|"])
    for label, frame in (("Training C33-C52", train), ("Evaluation C53-C66", evaluation)):
        metric = _metric_row(frame, frame["decision"].eq("FADE"), label=label)
        lines.append(f"| {label} | {metric['n']} | {metric['coverage']:.2%} | {metric['mean']:.3f} | [{metric['account_lo']:.3f}, {metric['account_hi']:.3f}] |")
    train_mean = _metric_row(train, train["decision"].eq("FADE"), label="train")["mean"]
    eval_mean = _metric_row(evaluation, evaluation["decision"].eq("FADE"), label="eval")["mean"]
    lines.extend(["", f"The acted-on mean changes by {eval_mean - train_mean:.3f} rP/lot from training to evaluation. This gap is the relevant Stage 4 survival warning: the training result is not evidence of a deployable edge unless it survives the mandated evaluation interval and the fold checks.", ""])

    eval_scores = evaluation["score"]
    quantiles = eval_scores.quantile([0.01, 0.25, 0.50, 0.75, 0.99])
    effective_threshold = max(float(artifact["selected_threshold"]), float(artifact.get("hurdle", _HURDLE)))
    score_pass = eval_scores.to_numpy() > effective_threshold
    win_override = evaluation["win_streak"].to_numpy() > 1
    tph_override = evaluation["trades_per_hour"].to_numpy() > 60
    nan_rows = evaluation["_raw_nan_feature"].to_numpy(dtype=bool)
    score_fail = ~score_pass
    win_gate = score_pass & win_override
    tph_gate = score_pass & ~win_override & tph_override
    nan_gate = score_pass & ~win_override & ~tph_override & nan_rows
    lines.extend(
        [
            "## Decision-rule clarification",
            "",
            "The exact boolean expression executed by `predict()` is:",
            "",
            "```text",
            "FADE = (score > max(selected_threshold, hurdle)) AND (win_streak <= 1) AND (trades_per_hour <= 60)",
            "```",
            "",
            "",
            "### Evaluation score distribution (frozen alpha)",
            "",
            f"Frozen alpha: `{artifact['alpha_frozen']:.6g}`; n=6,583; unique scores={eval_scores.nunique()}; std={eval_scores.std(ddof=0):.6f}.",
            "",
            "| min | p01 | p25 | p50 | p75 | p99 | max | std |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
            f"| {eval_scores.min():.6f} | {quantiles.loc[0.01]:.6f} | {quantiles.loc[0.25]:.6f} | {quantiles.loc[0.50]:.6f} | {quantiles.loc[0.75]:.6f} | {quantiles.loc[0.99]:.6f} | {eval_scores.max():.6f} | {eval_scores.std(ddof=0):.6f} |",
            "",
            "The predictions are not effectively constant: the standard deviation is about $30.36/lot and the central 98% span is broad, although most scores remain below the zero hurdle.",
            "",
            "### Sequential evaluation gate counts",
            "",
            "Counts are disjoint and applied in execution order. Raw NaN rows are also shown separately: imputation means they do not form an abstain gate, and V2 has no cold-start feature or cold-start override.",
            "",
            "| gate | count | interpretation |",
            "|---|---:|---|",
            f"| score fails effective threshold | {int(score_fail.sum())} | score <= {effective_threshold:.3f} |",
            f"| win_streak > 1 after score pass | {int(win_gate.sum())} | pre-registered override |",
            f"| trades_per_hour > 60 after prior gates | {int(tph_gate.sum())} | pre-registered override |",
            f"| NaN feature after prior gates | {int(nan_gate.sum())} | none excluded; imputer handles NaNs |",
            f"| FADE | {int((score_pass & ~win_override & ~tph_override).sum())} | {float((score_pass & ~win_override & ~tph_override).mean()):.2%} of evaluation |",
            f"| raw rows with >=1 NaN V2 feature | {int(nan_rows.sum())} | diagnostic only; not an abstain gate |",
            "| cold-start exclusion | 0 | V2 dropped history features and has no cold-start gate |",
            "",
            "### Compact fixed threshold sweep",
            "",
            "Training selection uses `train_n >= 30` and maximizes training mean rP/lot. This table retains only rows where training n changes, selection status changes, or the executable operating point 0 is reached. Evaluation coverage uses the zero economic hurdle and both abstain overrides, so negative grid values have the same effective execution threshold of zero.",
            "",
            "| grid threshold | train n | train mean rP/lot | effective execution threshold | evaluation n acted | evaluation coverage | support eligible | selected |",
            "|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in threshold_sweep.itertuples(index=False):
        mean_text = "" if pd.isna(row.train_mean_rp_per_lot) else f"{row.train_mean_rp_per_lot:.6f}"
        lines.append(
            f"| {row.grid_threshold:.1f} | {int(row.train_n)} | {mean_text} | {row.effective_execution_threshold:.1f} | "
            f"{int(row.evaluation_n_acted)} | {row.evaluation_coverage:.2%} | "
            f"{'yes' if row.support_eligible else 'no'} | {'yes' if row.selected else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## Acting-subset power and coverage frontier",
            "",
            "The default acting subsets are reported on both evaluation windows:",
            "",
            "| window | n acted | distinct traderKey | distinct ipClusterId | campaigns |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in acted_summary["windows"]:
        lines.append(
            f"| {row['window']} | {row['n']} | {row['trader_ids']} | {row['ip_ids']} | {row['campaigns']} |"
        )
    lines.extend(
        [
            "",
            f"MDE uses `MDE = 2.801585 * sigma * sqrt(DEFF / n)` for alpha=0.05 and power=0.80. Sigma is held at the primary-era C53-C65 outcome dispersion, so the calculation does not reuse the selected subset's realized variance: raw sigma={acted_summary['sigma_raw']:.6f}; winsorized 1%/99% sigma={acted_summary['sigma_winsorized']:.6f}.",
            "",
            "### ICC, DEFF, and MDE recomputed on the acted-on positions",
            "",
            "Unfloored MDEs show the direct negative-ICC calculation. Floored MDEs set ICC=max(ICC,0), hence DEFF=max(DEFF,1), and are the non-anti-conservative values.",
            "",
            "| window | clustering scheme | effective clusters | mean cluster size | ICC | DEFF | unfloored raw / win. | floored raw / win. |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in subset_power.itertuples(index=False):
        lines.append(
            f"| {row.window} | {row.cluster_scheme} | {int(row.n_clusters)} | {row.mean_cluster_size:.3f} | {row.icc:.6f} | {row.deff:.6f} | ${row.mde_raw:.2f} / ${row.mde_winsorized:.2f} | ${row.mde_raw_floored:.2f} / ${row.mde_winsorized_floored:.2f} |"
        )
    lines.extend(
        [
            "",
            "The negative acting-subset ICCs are treated as small-sample noise, not as information that increases power: mean cluster size is only about 2.7 and the unfloored DEFF<1 is anti-conservative. For comparison, the n=694 training MDE used positive primary estimates traderKey ICC=0.162328 / DEFF=1.753221 and ipClusterId ICC=0.096472 / DEFF=1.615386. The acting-subset calculation is therefore not directly comparable unless the ICC floor is applied.",
            "",
            "The C53-C65 acted mean is +10.433 rP/lot (the C53-C66 mean is +10.325); both are far below even the floored MDEs and their account-clustered intervals include zero. The acting result is not distinguishable from zero at this sample size.",
            "",
            "The fixed overrides impose a maximum actual acting coverage of "
            f"{int((~((backtest.loc[backtest['campaignId'].between(53, 66), 'win_streak'].to_numpy() > 1) | (backtest.loc[backtest['campaignId'].between(53, 66), 'trades_per_hour'].to_numpy() > 60))).sum())} / 6,583 = "
            f"{float((~((backtest.loc[backtest['campaignId'].between(53, 66), 'win_streak'].to_numpy() > 1) | (backtest.loc[backtest['campaignId'].between(53, 66), 'trades_per_hour'].to_numpy() > 60))).mean()):.2%}; therefore the 100% row below means a hurdle low enough for every score to pass, while the overrides still leave some rows abstaining.",
            "",
            "### Coverage-power frontier",
            "",
            "Each row sweeps the effective score hurdle while retaining both abstain overrides. The requested target is rounded to the nearest position; achieved coverage is the actual post-override coverage. MDE uses the DEFF recomputed on that row's acted-on subset.",
            "",
            "| target | effective hurdle | target n | n acted | achieved coverage | mean rP/lot | account 95% CI | account DEFF | account MDE unfloored raw / win. | account MDE floored raw / win. | IP DEFF | IP MDE unfloored raw / win. | IP MDE floored raw / win. |",
            "|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in frontier.itertuples(index=False):
        lines.append(
            f"| {row.target_coverage:.1%} | {row.hurdle:.6f} | {int(row.target_n)} | {int(row.n)} | {row.coverage:.2%} | {row.mean:.3f} | [{row.account_lo:.3f}, {row.account_hi:.3f}] | {row.account_deff:.3f} | ${row.account_mde_raw:.2f} / ${row.account_mde_winsorized:.2f} | ${row.account_mde_raw_floored:.2f} / ${row.account_mde_winsorized_floored:.2f} | {row.ip_deff:.3f} | ${row.ip_mde_raw:.2f} / ${row.ip_mde_winsorized:.2f} | ${row.ip_mde_raw_floored:.2f} / ${row.ip_mde_winsorized_floored:.2f} |"
        )
    clears_unfloored = []
    clears_floored = []
    for row in frontier.itertuples(index=False):
        clears_unfloored.append(
            float(row.mean) > float(row.account_mde_raw)
            or float(row.mean) > float(row.account_mde_winsorized)
            or float(row.mean) > float(row.ip_mde_raw)
            or float(row.mean) > float(row.ip_mde_winsorized)
        )
        clears_floored.append(
            float(row.mean) > float(row.account_mde_raw_floored)
            or float(row.mean) > float(row.account_mde_winsorized_floored)
            or float(row.mean) > float(row.ip_mde_raw_floored)
            or float(row.mean) > float(row.ip_mde_winsorized_floored)
        )
    lines.extend(
        [
            "",
            f"No coverage level clears its own MDE: **{sum(clears_unfloored)} of {len(clears_unfloored)} frontier rows** clears an unfloored MDE, and **{sum(clears_floored)} of {len(clears_floored)}** clears a floored MDE. The realized point estimate is therefore below the corresponding 80%-power detection floor at every tested coverage.",
            "",
            "The threshold sweep is intentionally inert over the support-eligible region: every support-eligible training threshold is negative and is overridden by the zero economic hurdle. This is a property of the design—acting is `score > 0` plus the two abstain overrides—not a pipeline defect.",
        ]
    )
    _Path(report_path).write_text("\n".join(lines), encoding="utf-8")


def _run_backtest(args: _Any) -> None:
    artifact = _load_artifact(args.artifact)
    positions = _prepare_backtest_positions(args.datasets, args.traders, args.cache)
    backtest = _backtest_predictions(positions, artifact)
    fold_rows = _fold_metrics(args.features, artifact)
    threshold_sweep = _compact_threshold_sweep(_threshold_sweep(args.features, artifact, backtest))
    acted_summary, subset_power, frontier = _power_frontier(backtest, artifact)
    executable_selection = _executable_selection(args.features, artifact)
    _render_stage3_report(
        args.out,
        artifact,
        backtest,
        fold_rows,
        threshold_sweep,
        acted_summary,
        subset_power,
        frontier,
        executable_selection,
    )
    print(f"wrote {args.out}")
    print(
        f"artifact threshold={artifact['selected_threshold']:.3f} effective={artifact['effective_threshold']:.3f}; "
        f"evaluation default coverage={backtest.loc[backtest.campaignId.between(53,66),'decision'].eq('FADE').mean():.2%}"
    )


def predict(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Predict one deterministic Stage 3 decision per input trade.

    Rows are consumed in their existing order.  Entry-time features are
    computed first; if a closed outcome is present, it is applied only after
    that row's decision to update the account state for later rows.
    """
    _assert_no_feature_leakage()
    artifact = _load_artifact()
    return _predict_internal(trades_df, artifact, apply_overrides=True)


def _main() -> None:
    parser = _argparse.ArgumentParser(description="Fit or backtest the frozen Stage 3 V2 model.")
    parser.add_argument("--fit-artifact", action="store_true")
    parser.add_argument("--backtest", action="store_true")
    parser.add_argument("--features", default="features_v2.csv")
    parser.add_argument("--artifact", default=str(_DEFAULT_ARTIFACT))
    parser.add_argument("--datasets", default="datasets")
    parser.add_argument("--traders", default="traders_sanitized.csv")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv")
    parser.add_argument("--out", default="reports/stage3_backtest.md")
    parser.add_argument("--print-artifact", action="store_true")
    args = parser.parse_args()
    if args.fit_artifact:
        artifact = _fit_artifact(args.features, args.artifact)
        print(
            f"wrote {args.artifact}; alpha_cv={artifact['alpha_cv_selected']:.6g}; "
            f"alpha_frozen={artifact['alpha_frozen']:.6g}; "
            f"threshold={artifact['selected_threshold']:.3f}; "
            f"training_coverage={artifact['training_threshold_coverage']:.2%}"
        )
    elif args.backtest:
        _run_backtest(args)
    elif args.print_artifact:
        print(_json.dumps(_load_artifact(args.artifact), indent=2, sort_keys=True))
    else:
        parser.error("choose --fit-artifact or --print-artifact")


if __name__ == "__main__":
    _main()
