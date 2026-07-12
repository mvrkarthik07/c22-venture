from __future__ import annotations

import argparse
import gzip
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from features import TraderState
from pipeline import infer_exit_type, load_all_trades, to_positions

HURDLE = 7.0
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
    "shared_ip",
    "ip_cluster_size",
    "challenge_type",
    "gold_vol_prev_day",
]

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
    "clears_hurdle",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Stage 2 causal trader features.")
    parser.add_argument("--datasets", default="datasets", help="Path to the trade datasets root")
    parser.add_argument("--traders", default="traders_sanitized.csv", help="Path to traders_sanitized.csv")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Output CSV path")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument("--balance", type=float, default=10000.0, help="Start balance per account")
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


def build_feature_rows(positions: pd.DataFrame, trader_meta: pd.DataFrame, start_balance: float) -> pd.DataFrame:
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
    for (_, _), group in positions.groupby(["campaignId", "accountId"], sort=False):
        first = group.iloc[0]
        state = TraderState(
            {
                "start_balance": start_balance,
                "campaign_id": first["campaignId"],
                "campaign_date": first["campaignDate"],
                "trader_key": first["traderKey"],
                "prior_campaigns": int(first["prior_campaigns"]) if pd.notna(first["prior_campaigns"]) else 0,
                "shared_ip": bool(first["sharedIpFlag"]) if pd.notna(first["sharedIpFlag"]) else False,
                "ip_cluster_size": first["ip_cluster_size"],
                "challenge_type": first["challenge_type"],
                "gold_vol_prev_day": first["gold_vol_prev_day"],
            }
        )

        for position in group.to_dict("records"):
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
                "clears_hurdle": gross_loss_per_lot > HURDLE if pd.notna(gross_loss_per_lot) else np.nan,
            }
            row.update(features)
            rows.append(row)
            state.update(position)

    return pd.DataFrame(rows)


def print_summary(features_df: pd.DataFrame) -> None:
    print(f"\nrow_count: {len(features_df)}")
    print("\nNaN rate per feature:")
    nan_rates = features_df[FEATURE_COLUMNS].isna().mean().sort_values(ascending=False)
    print(nan_rates.to_string(float_format=lambda value: f"{value:.2%}"))

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

    features_df = build_feature_rows(positions, trader_meta, start_balance=args.balance)
    ordered_columns = IDENTIFIER_COLUMNS + ["exit_type"] + FEATURE_COLUMNS + TARGET_COLUMNS
    features_df = features_df[ordered_columns]
    features_df.to_csv(args.out, index=False)

    print(f"\nWrote {args.out}")
    print_summary(features_df)


if __name__ == "__main__":
    main()
