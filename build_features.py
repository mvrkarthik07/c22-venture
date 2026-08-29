from __future__ import annotations

import argparse
import gzip
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import requests

from features import TraderHistory, TraderState
from pipeline import (
    BREACH_THRESHOLD_USD,
    HURDLE,
    STARTING_BALANCE,
    TARGET_THRESHOLD_USD,
    infer_exit_type,
    load_all_trades,
    reverse_profit_per_lot,
    to_positions,
)
from splits import PRIMARY_CAMPAIGN_MAX, PRIMARY_CAMPAIGN_MIN

FOREXSB_INFO_URL = "https://data.forexsb.com/datafeed/info/premium.json.gz"
FOREXSB_XAUUSD_M30_URL = "https://data.forexsb.com/datafeed/data/dukascopy/XAUUSD30.lb.gz"
DEFAULT_CACHE_PATH = Path("cache/xauusd_daily_ohlc.csv")
DEFAULT_OUT_PATH = Path("features_v2.csv")

FEATURE_COLUMNS = [
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
    "prior_campaigns_x_loss_streak_ge_2",
    "shared_ip",
    "ip_cluster_size",
    "challenge_type",
    "gold_vol_prev_day",
    "sl_widening_delta",
    "same_direction_reentry",
    "size_delta_ratio",
    "trader_prior_tilt",
    "trader_prior_sl_discipline",
    "trader_prior_survival",
]

COMPANION_BALANCE_COLUMNS = [
    "cum_pnl_usd",
    "dd_from_peak_usd",
]

SUPPLEMENTAL_FEATURE_COLUMNS = [
    "breach_proximity_usd",
    "target_proximity_usd",
]
ALL_FEATURE_COLUMNS = (
    FEATURE_COLUMNS
    + ["entry_gap_sec", "is_cold_start"]
    + COMPANION_BALANCE_COLUMNS
    + SUPPLEMENTAL_FEATURE_COLUMNS
)

IDENTIFIER_COLUMNS = [
    "campaignId",
    "accountId",
    "positionId",
    "openDateTime",
    "closeDateTime",
    "campaignDate",
    "traderKey",
    "ipClusterId",
]

TARGET_COLUMNS = [
    "gross_loss_per_lot",
    "reverse_profit_per_lot",
    "clears_hurdle",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Stage 2 causal trader features.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Output CSV path")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument(
        "--balance",
        type=float,
        default=STARTING_BALANCE,
        help="Confirmed starting balance per account",
    )
    parser.add_argument(
        "--trader-history-k",
        type=float,
        default=5.0,
        help="Empirical-Bayes shrinkage hyperparameter for cross-campaign trader history",
    )
    return parser.parse_args()


def load_positions(dataset_root: str) -> pd.DataFrame:
    trades = load_all_trades(dataset_root)
    positions = to_positions(trades)
    positions["exit_type"] = infer_exit_type(positions)
    return positions


def normalize_challenge_type(value):
    if pd.isna(value):
        return "unknown"
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def load_trader_metadata(traders_path: str | Path, positions: pd.DataFrame) -> pd.DataFrame:
    traders = pd.read_csv(traders_path)
    traders = traders[
        ["campaignId", "account", "challenge_type_id", "traderKey", "sharedIpFlag", "ipClusterId"]
    ].drop_duplicates()

    active_accounts = positions[["campaignId", "accountId"]].drop_duplicates()
    trader_meta = active_accounts.merge(
        traders,
        left_on=["campaignId", "accountId"],
        right_on=["campaignId", "account"],
        how="left",
    ).drop(columns=["account"])

    trader_meta["sharedIpFlag"] = trader_meta["sharedIpFlag"].astype("boolean").fillna(False).astype(bool)
    valid_ip_mask = trader_meta["ipClusterId"].notna() & (trader_meta["ipClusterId"] != -1)
    ip_cluster_sizes = (
        trader_meta.loc[valid_ip_mask]
        .groupby("ipClusterId")["accountId"]
        .nunique()
    )
    trader_meta["ip_cluster_size"] = trader_meta["ipClusterId"].map(ip_cluster_sizes)

    campaigns_by_trader = (
        trader_meta.loc[trader_meta["traderKey"].notna()]
        .groupby("traderKey")["campaignId"]
        .agg(lambda s: sorted(pd.unique(s)))
        .to_dict()
    )

    trader_meta["prior_campaigns"] = trader_meta.apply(
        lambda row: sum(
            campaign_id < row["campaignId"]
            for campaign_id in campaigns_by_trader.get(row["traderKey"], [])
        )
        if pd.notna(row["traderKey"])
        else 0,
        axis=1,
    )
    trader_meta["challenge_type"] = trader_meta["challenge_type_id"].map(normalize_challenge_type)
    trader_meta["challenge_type"] = trader_meta["challenge_type"].fillna("unknown")
    return trader_meta.drop(columns=["challenge_type_id"])


def download_xauusd_daily_ohlc(cache_path: str | Path, min_required_date) -> pd.DataFrame:
    cache_path = Path(cache_path)
    if cache_path.exists():
        cached = pd.read_csv(cache_path, parse_dates=["date"])
        if not cached.empty and cached["date"].max().date() >= min_required_date:
            return cached

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    info = session.get(FOREXSB_INFO_URL, timeout=60)
    info.raise_for_status()
    price_scale = info.json()["XAUUSD"]["priceScale"]

    response = session.get(FOREXSB_XAUUSD_M30_URL, timeout=120)
    response.raise_for_status()
    raw = response.content
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)

    records = np.frombuffer(raw, dtype="<i4").reshape(-1, 7)
    timestamps = pd.Timestamp("2000-01-01", tz="UTC") + pd.to_timedelta(records[:, 0], unit="m")
    intraday = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": records[:, 1] / price_scale,
            "high": records[:, 2] / price_scale,
            "low": records[:, 3] / price_scale,
            "close": records[:, 4] / price_scale,
        }
    )
    intraday["date"] = intraday["timestamp"].dt.floor("D").dt.tz_localize(None)
    daily = (
        intraday.groupby("date", sort=True)
        .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .reset_index()
    )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(cache_path, index=False)
    return daily


def attach_gold_vol_prev_day(positions: pd.DataFrame, daily_ohlc: pd.DataFrame) -> pd.DataFrame:
    daily = daily_ohlc.copy()
    daily["gold_vol_prev_day"] = (daily["high"] - daily["low"]) / daily["close"]
    gold_vol_lookup = daily.set_index("date")["gold_vol_prev_day"]

    positions = positions.copy()
    positions["campaignDate"] = pd.to_datetime(positions["campaignDate"]).dt.normalize()
    positions["gold_vol_prev_day"] = (
        positions["campaignDate"] - pd.Timedelta(days=1)
    ).map(gold_vol_lookup)
    return positions


def fit_trader_history_params(
    positions: pd.DataFrame,
    trader_meta: pd.DataFrame,
    start_balance: float,
    *,
    shrinkage_k: float = 5.0,
) -> dict[str, float]:
    base_rows = _build_feature_rows_internal(
        positions,
        trader_meta,
        start_balance,
        trader_history_params=None,
        use_trader_history=False,
    )

    tilt_mask = base_rows["loss_streak"] >= 2
    trader_prior_tilt = base_rows.loc[tilt_mask, "gross_loss_per_lot"].mean()
    trader_prior_sl_discipline = base_rows["sl_distance_pct"].mean()

    history_entity = base_rows["traderKey"].astype("object").where(
        base_rows["traderKey"].notna(),
        base_rows["campaignId"].astype(str) + "::" + base_rows["accountId"].astype(str),
    )
    survival = (
        base_rows.assign(_history_entity=history_entity)
        .groupby(["campaignId", "_history_entity"], dropna=False)
        .agg(first_open=("openDateTime", "min"), last_close=("closeDateTime", "max"))
        .reset_index()
    )
    trader_prior_survival = np.nan
    if not survival.empty:
        spans = (
            survival["last_close"] - survival["first_open"]
        ).dt.total_seconds() / 3600.0
        trader_prior_survival = (spans / TraderHistory.SURVIVAL_SPAN_MEDIAN_HOURS).mean()

    return {
        "shrinkage_k": float(shrinkage_k),
        "population_trader_prior_tilt": float(trader_prior_tilt)
        if pd.notna(trader_prior_tilt)
        else np.nan,
        "population_trader_prior_sl_discipline": float(trader_prior_sl_discipline)
        if pd.notna(trader_prior_sl_discipline)
        else np.nan,
        "population_trader_prior_survival": float(trader_prior_survival)
        if pd.notna(trader_prior_survival)
        else np.nan,
    }


def build_feature_rows(
    positions: pd.DataFrame,
    trader_meta: pd.DataFrame,
    start_balance: float,
    *,
    trader_history_params: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    resolved_history_params = _resolve_trader_history_params(
        positions,
        trader_meta,
        start_balance,
        trader_history_params,
    )
    return _build_feature_rows_internal(
        positions,
        trader_meta,
        start_balance,
        trader_history_params=resolved_history_params,
        use_trader_history=True,
    )


def _resolve_trader_history_params(
    positions: pd.DataFrame,
    trader_meta: pd.DataFrame,
    start_balance: float,
    trader_history_params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    resolved = dict(trader_history_params or {})
    required_keys = {
        "population_trader_prior_tilt",
        "population_trader_prior_sl_discipline",
        "population_trader_prior_survival",
    }
    if required_keys.issubset(resolved.keys()):
        resolved.setdefault("shrinkage_k", 5.0)
        return resolved

    fitted = fit_trader_history_params(
        positions,
        trader_meta,
        start_balance,
        shrinkage_k=float(resolved.get("shrinkage_k", 5.0)),
    )
    fitted.update(resolved)
    return fitted


def _build_feature_rows_internal(
    positions: pd.DataFrame,
    trader_meta: pd.DataFrame,
    start_balance: float,
    *,
    trader_history_params: Mapping[str, Any] | None,
    use_trader_history: bool,
) -> pd.DataFrame:
    positions = positions.merge(
        trader_meta,
        on=["campaignId", "accountId"],
        how="left",
    )
    positions = positions.sort_values(
        ["campaignId", "accountId", "openDateTime", "positionId"],
        kind="mergesort",
    ).reset_index(drop=True)

    rows = []
    trader_histories: dict[str, TraderHistory] = {}
    history_config = dict(trader_history_params or {})

    for campaign_id, campaign_group in positions.groupby("campaignId", sort=True):
        campaign_rows: list[dict[str, Any]] = []
        for (_, _), account_group in campaign_group.groupby(["campaignId", "accountId"], sort=False):
            first = account_group.iloc[0]
            history_features = _history_features_for_campaign(
                first,
                current_campaign_id=int(campaign_id),
                trader_histories=trader_histories,
                history_config=history_config,
                use_trader_history=use_trader_history,
            )
            state = TraderState(
                {
                    "start_balance": start_balance,
                    "campaign_id": first["campaignId"],
                    "campaign_date": first["campaignDate"],
                    "trader_key": first["traderKey"],
                    "prior_campaigns": history_features["prior_campaigns"],
                    "shared_ip": bool(first["sharedIpFlag"]) if pd.notna(first["sharedIpFlag"]) else False,
                    "ip_cluster_size": first["ip_cluster_size"],
                    "challenge_type": first["challenge_type"],
                    "gold_vol_prev_day": first["gold_vol_prev_day"],
                    "breach_threshold_usd": BREACH_THRESHOLD_USD,
                    "target_threshold_usd": TARGET_THRESHOLD_USD,
                    "trader_prior_tilt": history_features["trader_prior_tilt"],
                    "trader_prior_sl_discipline": history_features["trader_prior_sl_discipline"],
                    "trader_prior_survival": history_features["trader_prior_survival"],
                    "is_cold_start": history_features["is_cold_start"],
                }
            )

            for position in account_group.to_dict("records"):
                features = state.compute_features(position)
                gross_loss_per_lot = (
                    -float(position["profit"]) / float(position["amount"])
                    if float(position["amount"]) != 0.0
                    else np.nan
                )
                row = {
                    "campaignId": position["campaignId"],
                    "accountId": position["accountId"],
                    "positionId": position["positionId"],
                    "openDateTime": position["openDateTime"],
                    "closeDateTime": position["closeDateTime"],
                    "campaignDate": position["campaignDate"],
                    "traderKey": position["traderKey"],
                    "ipClusterId": position["ipClusterId"],
                    "exit_type": position["exit_type"],
                    "gross_loss_per_lot": gross_loss_per_lot,
                    "reverse_profit_per_lot": reverse_profit_per_lot(gross_loss_per_lot)
                    if pd.notna(gross_loss_per_lot)
                    else np.nan,
                    "clears_hurdle": gross_loss_per_lot > HURDLE if pd.notna(gross_loss_per_lot) else np.nan,
                }
                row.update(features)
                rows.append(row)
                campaign_rows.append(row)
                state.update(position)

        if use_trader_history and campaign_rows:
            _update_trader_histories_for_campaign(
                pd.DataFrame(campaign_rows),
                trader_histories,
                history_config,
            )

    return pd.DataFrame(rows)


def _history_features_for_campaign(
    account_row: pd.Series,
    *,
    current_campaign_id: int,
    trader_histories: dict[str, TraderHistory],
    history_config: Mapping[str, Any],
    use_trader_history: bool,
) -> dict[str, Any]:
    if not use_trader_history:
        prior_campaigns = int(account_row["prior_campaigns"]) if pd.notna(account_row["prior_campaigns"]) else 0
        return {
            "prior_campaigns": prior_campaigns,
            "trader_prior_tilt": np.nan,
            "trader_prior_sl_discipline": np.nan,
            "trader_prior_survival": np.nan,
            "is_cold_start": prior_campaigns == 0,
        }

    trader_key = account_row["traderKey"]
    if pd.isna(trader_key):
        return TraderHistory(history_config).compute_features(current_campaign_id)

    trader_key = str(trader_key)
    if trader_key not in trader_histories:
        trader_histories[trader_key] = TraderHistory(history_config)
    return trader_histories[trader_key].compute_features(current_campaign_id)


def _update_trader_histories_for_campaign(
    campaign_rows: pd.DataFrame,
    trader_histories: dict[str, TraderHistory],
    history_config: Mapping[str, Any],
) -> None:
    for trader_key, trader_rows in campaign_rows.groupby("traderKey", dropna=True):
        trader_rows = trader_rows.sort_values(["openDateTime", "positionId"], kind="mergesort")
        tilt_rows = trader_rows.loc[trader_rows["loss_streak"] >= 2, "gross_loss_per_lot"]
        sl_rows = trader_rows["sl_distance_pct"].dropna()
        survival_span_hours = (
            trader_rows["closeDateTime"].max() - trader_rows["openDateTime"].min()
        ).total_seconds() / 3600.0
        summary = {
            "tilt_mean": tilt_rows.mean() if not tilt_rows.empty else np.nan,
            "tilt_n": int(tilt_rows.notna().sum()),
            "sl_sum": float(sl_rows.sum()) if not sl_rows.empty else np.nan,
            "sl_n": int(sl_rows.shape[0]),
            "survival_span_hours": survival_span_hours,
            "survival_n": int(len(trader_rows)),
        }
        trader_key = str(trader_key)
        if trader_key not in trader_histories:
            trader_histories[trader_key] = TraderHistory(history_config)
        trader_histories[trader_key].update_campaign(int(trader_rows["campaignId"].iloc[0]), summary)


def print_summary(features_df: pd.DataFrame) -> None:
    print(f"\nrow_count: {len(features_df)}")
    primary = features_df.loc[
        features_df["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)
    ]
    if "is_cold_start" in primary.columns:
        print(
            f"\nPrimary era C{PRIMARY_CAMPAIGN_MIN}-C{PRIMARY_CAMPAIGN_MAX} cold-start rate: "
            f"{primary['is_cold_start'].mean():.2%}"
        )
    else:
        print(
            f"\nPrimary era C{PRIMARY_CAMPAIGN_MIN}-C{PRIMARY_CAMPAIGN_MAX} cold-start rate: "
            "not printed (`is_cold_start` dropped from frozen v2.1 export)"
        )
    print(
        f"\nPrimary era C{PRIMARY_CAMPAIGN_MIN}-C{PRIMARY_CAMPAIGN_MAX} coverage per feature:"
    )
    non_nan_rates = primary[FEATURE_COLUMNS].notna().mean().sort_values(ascending=False)
    print(non_nan_rates.to_string(float_format=lambda value: f"{value:.2%}"))

    print("\n5-row feature sample (no identifiers):")
    print(features_df[FEATURE_COLUMNS].head(5).to_string(index=False))


def main() -> None:
    args = parse_args()
    positions = load_positions(args.datasets)
    trader_meta = load_trader_metadata(args.traders, positions)

    min_required_date = (
        pd.to_datetime(positions["campaignDate"]).dt.normalize().min() - pd.Timedelta(days=1)
    ).date()
    daily_ohlc = download_xauusd_daily_ohlc(args.cache, min_required_date=min_required_date)
    positions = attach_gold_vol_prev_day(positions, daily_ohlc)

    features_df = build_feature_rows(
        positions,
        trader_meta,
        start_balance=args.balance,
        trader_history_params={"shrinkage_k": args.trader_history_k},
    )
    ordered_columns = (
        IDENTIFIER_COLUMNS
        + ["exit_type"]
        + FEATURE_COLUMNS
        + COMPANION_BALANCE_COLUMNS
        + SUPPLEMENTAL_FEATURE_COLUMNS
        + TARGET_COLUMNS
    )
    features_df = features_df[ordered_columns]
    features_df.to_csv(args.out, index=False)

    print(f"\nWrote {args.out}")
    print_summary(features_df)


if __name__ == "__main__":
    main()
