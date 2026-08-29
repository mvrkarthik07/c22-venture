from __future__ import annotations

import math
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_features import build_feature_rows
from features import TraderState

FAMILY_F_FEATURES = [
    "sl_widening_delta",
    "entry_gap_sec",
    "same_direction_reentry",
    "size_delta_ratio",
]
BALANCE_STATE_FEATURES = [
    "pnl_pct",
    "dd_from_peak_pct",
    "cum_pnl_usd",
    "dd_from_peak_usd",
    "breach_proximity_usd",
    "target_proximity_usd",
]


def make_trade(
    *,
    open_time: datetime,
    close_time: datetime,
    amount: float,
    net_profit: float,
    side: str,
    sl_price,
    tp_price,
    exit_type: str,
    open_price: float = 100.0,
    campaign_id: int = 53,
):
    return {
        "campaignId": campaign_id,
        "openDateTime": open_time,
        "closeDateTime": close_time,
        "amount": amount,
        "side": side,
        "netProfit": net_profit,
        "profit": net_profit,
        "openPrice": open_price,
        "slPrice": sl_price,
        "tpPrice": tp_price,
        "exit_type": exit_type,
    }


def make_sequence():
    base = datetime(2026, 5, 19, 9, 0, 0)
    return [
        make_trade(
            open_time=base,
            close_time=base + timedelta(minutes=10),
            amount=0.5,
            net_profit=10.0,
            side="BUY",
            sl_price=99.0,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=20),
            close_time=base + timedelta(minutes=30),
            amount=0.5,
            net_profit=-20.0,
            side="SELL",
            sl_price=None,
            tp_price=101.5,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=40),
            close_time=base + timedelta(minutes=50),
            amount=1.0,
            net_profit=-30.0,
            side="BUY",
            sl_price=98.0,
            tp_price=None,
            exit_type="sl_hit",
        ),
        make_trade(
            open_time=base + timedelta(minutes=60),
            close_time=base + timedelta(minutes=65),
            amount=0.2,
            net_profit=2.0,
            side="BUY",
            sl_price=None,
            tp_price=None,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=80),
            close_time=base + timedelta(minutes=90),
            amount=0.5,
            net_profit=5.0,
            side="SELL",
            sl_price=99.5,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=100),
            close_time=base + timedelta(minutes=110),
            amount=2.0,
            net_profit=-10.0,
            side="SELL",
            sl_price=None,
            tp_price=102.0,
            exit_type="manual",
        ),
    ]


def make_sl_widening_sequence():
    base = datetime(2026, 5, 20, 9, 0, 0)
    return [
        make_trade(
            open_time=base,
            close_time=base + timedelta(minutes=5),
            amount=0.5,
            net_profit=5.0,
            side="BUY",
            sl_price=99.0,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=10),
            close_time=base + timedelta(minutes=15),
            amount=0.5,
            net_profit=-3.0,
            side="BUY",
            sl_price=98.5,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=20),
            close_time=base + timedelta(minutes=25),
            amount=0.5,
            net_profit=4.0,
            side="SELL",
            sl_price=98.0,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=30),
            close_time=base + timedelta(minutes=35),
            amount=0.5,
            net_profit=2.0,
            side="SELL",
            sl_price=97.5,
            tp_price=101.0,
            exit_type="manual",
        ),
    ]


def make_config():
    return {
        "start_balance": 1000.0,
        "breach_threshold_usd": 40.0,
        "target_threshold_usd": 80.0,
        "campaign_id": 53,
        "trader_key": "trader-1",
        "prior_campaign_ids": [49, 52, 53],
        "shared_ip": True,
        "ip_cluster_size": 3,
        "challenge_type": "standard",
        "gold_vol_prev_day": 0.015,
    }


def run_sequence(positions, config=None):
    state = TraderState(config or make_config())
    features = []
    for position in positions:
        features.append(state.compute_features(position))
        state.update(position)
    return features


def assert_feature_dicts_equal(actual: dict, expected: dict):
    assert actual.keys() == expected.keys()
    for key in actual:
        assert_feature_value_equal(actual[key], expected[key], key)


def assert_feature_value_equal(left, right, key: str):
    if isinstance(left, float) and math.isnan(left):
        assert isinstance(right, float) and math.isnan(right), key
    elif isinstance(right, float) and math.isnan(right):
        assert isinstance(left, float) and math.isnan(left), key
    elif isinstance(left, float) or isinstance(right, float):
        assert left == pytest.approx(right), key
    else:
        assert left == right, key


def test_trade_4_matches_hand_computed_values():
    features = run_sequence(make_sequence())
    trade_4 = features[3]

    assert trade_4["loss_streak"] == 2
    assert trade_4["win_streak"] == 0
    assert trade_4["pnl_ewm"] == pytest.approx(-11.73)
    assert trade_4["size_after_loss_delta"] == pytest.approx(0.2 - 0.5)
    assert trade_4["sl_usage_rate_5"] == pytest.approx(2 / 3)
    assert trade_4["manual_exit_rate_5"] == pytest.approx(2 / 3)
    assert trade_4["pnl_pct"] == pytest.approx(-0.04)
    assert trade_4["dd_from_peak_pct"] == pytest.approx(0.05)
    assert trade_4["cum_pnl_usd"] == pytest.approx(-40.0)
    assert trade_4["dd_from_peak_usd"] == pytest.approx(50.0)
    assert trade_4["breach_proximity_usd"] == pytest.approx(-10.0)
    assert trade_4["target_proximity_usd"] == pytest.approx(120.0)
    assert trade_4["trade_index"] == 4
    assert trade_4["log_dt_close"] == pytest.approx(math.log1p(10 * 60))
    assert trade_4["trades_per_hour"] == pytest.approx(4.0)
    assert trade_4["prior_campaigns"] == 2
    assert trade_4["shared_ip"] is True
    assert trade_4["ip_cluster_size"] == 3.0
    assert trade_4["challenge_type"] == "standard"
    assert trade_4["gold_vol_prev_day"] == pytest.approx(0.015)
    assert math.isnan(trade_4["sl_widening_delta"])
    assert trade_4["entry_gap_sec"] == pytest.approx(10 * 60)
    assert trade_4["same_direction_reentry"] == 1
    assert trade_4["size_delta_ratio"] == pytest.approx(0.2 / 1.0)
    for removed_feature in [
        "streak_age_s",
        "lot_ratio_vs_avg",
        "size_pctile",
        "dist_to_target",
        "dist_to_dd_limit",
        "gap_compression",
        "is_repeat",
    ]:
        assert removed_feature not in trade_4


def test_usd_balance_features_do_not_require_start_balance():
    features = run_sequence(make_sequence(), config={**make_config(), "start_balance": np.nan})
    assert math.isnan(features[0]["pnl_pct"])
    assert math.isnan(features[0]["dd_from_peak_pct"])
    assert features[0]["cum_pnl_usd"] == pytest.approx(0.0)
    assert features[0]["dd_from_peak_usd"] == pytest.approx(0.0)
    assert features[0]["breach_proximity_usd"] == pytest.approx(40.0)
    assert features[0]["target_proximity_usd"] == pytest.approx(80.0)
    assert features[3]["cum_pnl_usd"] == pytest.approx(-40.0)
    assert features[3]["dd_from_peak_usd"] == pytest.approx(50.0)
    assert features[3]["breach_proximity_usd"] == pytest.approx(-10.0)
    assert features[3]["target_proximity_usd"] == pytest.approx(120.0)


def test_truncated_and_full_sequence_features_are_identical_per_prefix():
    positions = make_sequence()
    full_features = run_sequence(positions)
    assert set(FAMILY_F_FEATURES + BALANCE_STATE_FEATURES).issubset(full_features[0].keys())

    for prefix_len in range(1, len(positions) + 1):
        truncated_features = run_sequence(positions[:prefix_len])
        assert_feature_dicts_equal(
            truncated_features[-1],
            full_features[prefix_len - 1],
        )
        for feature_name in FAMILY_F_FEATURES + BALANCE_STATE_FEATURES:
            assert_feature_value_equal(
                truncated_features[-1][feature_name],
                full_features[prefix_len - 1][feature_name],
                feature_name,
            )


def test_future_modifications_do_not_change_past_features():
    original = make_sequence()
    modified = deepcopy(original)
    modified[4]["amount"] = 50.0
    modified[4]["netProfit"] = 5000.0
    modified[4]["profit"] = 5000.0
    modified[5]["amount"] = 75.0
    modified[5]["netProfit"] = -9000.0
    modified[5]["profit"] = -9000.0
    modified[5]["slPrice"] = 10.0
    modified[5]["exit_type"] = "sl_hit"

    original_features = run_sequence(original)
    modified_features = run_sequence(modified)

    for idx in range(4):
        assert_feature_dicts_equal(original_features[idx], modified_features[idx])
        for feature_name in FAMILY_F_FEATURES + BALANCE_STATE_FEATURES:
            assert_feature_value_equal(
                original_features[idx][feature_name],
                modified_features[idx][feature_name],
                feature_name,
            )


def test_sl_widening_delta_uses_prior_sl_median_only():
    features = run_sequence(make_sl_widening_sequence())

    assert math.isnan(features[0]["sl_widening_delta"])
    assert math.isnan(features[1]["sl_widening_delta"])
    assert math.isnan(features[2]["sl_widening_delta"])
    assert features[3]["sl_widening_delta"] == pytest.approx(0.025 - 0.015)


def test_entry_gap_sec_uses_optional_clip_parameter():
    config = make_config()
    config["entry_gap_sec_clip"] = 300.0
    features = run_sequence(make_sequence(), config=config)

    assert math.isnan(features[0]["entry_gap_sec"])
    assert features[1]["entry_gap_sec"] == pytest.approx(300.0)


def make_cross_campaign_positions():
    return pd.DataFrame(
        [
            {
                "campaignId": 53,
                "accountId": "acct-53",
                "positionId": 5301,
                "openDateTime": datetime(2026, 5, 1, 9, 0, 0),
                "closeDateTime": datetime(2026, 5, 1, 9, 30, 0),
                "campaignDate": datetime(2026, 5, 1),
                "gold_vol_prev_day": 0.02,
                "amount": 1.0,
                "side": "BUY",
                "netProfit": -10.0,
                "profit": -10.0,
                "openPrice": 100.0,
                "slPrice": 99.0,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
            {
                "campaignId": 53,
                "accountId": "acct-53",
                "positionId": 5302,
                "openDateTime": datetime(2026, 5, 1, 10, 0, 0),
                "closeDateTime": datetime(2026, 5, 1, 10, 30, 0),
                "campaignDate": datetime(2026, 5, 1),
                "gold_vol_prev_day": 0.02,
                "amount": 1.0,
                "side": "BUY",
                "netProfit": -20.0,
                "profit": -20.0,
                "openPrice": 100.0,
                "slPrice": 98.0,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
            {
                "campaignId": 53,
                "accountId": "acct-53",
                "positionId": 5303,
                "openDateTime": datetime(2026, 5, 1, 10, 40, 0),
                "closeDateTime": datetime(2026, 5, 1, 11, 0, 0),
                "campaignDate": datetime(2026, 5, 1),
                "gold_vol_prev_day": 0.02,
                "amount": 1.0,
                "side": "SELL",
                "netProfit": -30.0,
                "profit": -30.0,
                "openPrice": 100.0,
                "slPrice": None,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
            {
                "campaignId": 54,
                "accountId": "acct-54",
                "positionId": 5401,
                "openDateTime": datetime(2026, 5, 8, 9, 0, 0),
                "closeDateTime": datetime(2026, 5, 8, 9, 20, 0),
                "campaignDate": datetime(2026, 5, 8),
                "gold_vol_prev_day": 0.02,
                "amount": 1.0,
                "side": "BUY",
                "netProfit": -5.0,
                "profit": -5.0,
                "openPrice": 100.0,
                "slPrice": 99.5,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
            {
                "campaignId": 54,
                "accountId": "acct-54",
                "positionId": 5402,
                "openDateTime": datetime(2026, 5, 8, 9, 40, 0),
                "closeDateTime": datetime(2026, 5, 8, 10, 0, 0),
                "campaignDate": datetime(2026, 5, 8),
                "gold_vol_prev_day": 0.02,
                "amount": 1.5,
                "side": "SELL",
                "netProfit": 12.0,
                "profit": 12.0,
                "openPrice": 100.0,
                "slPrice": None,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
            {
                "campaignId": 55,
                "accountId": "acct-55",
                "positionId": 5501,
                "openDateTime": datetime(2026, 5, 15, 9, 0, 0),
                "closeDateTime": datetime(2026, 5, 15, 9, 45, 0),
                "campaignDate": datetime(2026, 5, 15),
                "gold_vol_prev_day": 0.02,
                "amount": 2.0,
                "side": "BUY",
                "netProfit": 50.0,
                "profit": 50.0,
                "openPrice": 100.0,
                "slPrice": 95.0,
                "tpPrice": 101.0,
                "exit_type": "manual",
            },
        ]
    )


def make_cross_campaign_trader_meta():
    return pd.DataFrame(
        [
            {
                "campaignId": 53,
                "accountId": "acct-53",
                "traderKey": "trader-repeat",
                "sharedIpFlag": False,
                "ipClusterId": 11,
                "ip_cluster_size": 1.0,
                "prior_campaigns": 0,
                "challenge_type": "standard",
            },
            {
                "campaignId": 54,
                "accountId": "acct-54",
                "traderKey": "trader-repeat",
                "sharedIpFlag": False,
                "ipClusterId": 11,
                "ip_cluster_size": 1.0,
                "prior_campaigns": 1,
                "challenge_type": "standard",
            },
            {
                "campaignId": 55,
                "accountId": "acct-55",
                "traderKey": "trader-repeat",
                "sharedIpFlag": False,
                "ipClusterId": 11,
                "ip_cluster_size": 1.0,
                "prior_campaigns": 2,
                "challenge_type": "standard",
            },
        ]
    )


def test_trader_history_uses_only_strictly_prior_campaigns():
    positions = make_cross_campaign_positions()
    trader_meta = make_cross_campaign_trader_meta()
    history_params = {
        "shrinkage_k": 5.0,
        "population_trader_prior_tilt": 0.0,
        "population_trader_prior_sl_discipline": 0.0,
        "population_trader_prior_survival": 0.0,
    }

    full = build_feature_rows(
        positions,
        trader_meta,
        start_balance=1000.0,
        trader_history_params=history_params,
    )

    campaign_54 = full.loc[full["campaignId"] == 54].reset_index(drop=True)
    expected_tilt = (1.0 / 6.0) * 30.0
    expected_sl = (2.0 / 7.0) * 0.015
    expected_survival = (3.0 / 8.0) * (2.0 / 1.99)

    assert (campaign_54["prior_campaigns"] == 1).all()
    assert campaign_54["trader_prior_tilt"].tolist() == pytest.approx([expected_tilt, expected_tilt])
    assert campaign_54["trader_prior_sl_discipline"].tolist() == pytest.approx([expected_sl, expected_sl])
    assert campaign_54["trader_prior_survival"].tolist() == pytest.approx([expected_survival, expected_survival])
    assert campaign_54["is_cold_start"].tolist() == [False, False]

    same_campaign_modified = positions.copy(deep=True)
    same_campaign_modified.loc[same_campaign_modified["positionId"] == 5401, "netProfit"] = 999.0
    same_campaign_modified.loc[same_campaign_modified["positionId"] == 5401, "profit"] = 999.0
    same_campaign_modified.loc[same_campaign_modified["positionId"] == 5401, "slPrice"] = 50.0

    future_campaign_modified = positions.copy(deep=True)
    future_campaign_modified.loc[future_campaign_modified["campaignId"] == 55, "netProfit"] = -999.0
    future_campaign_modified.loc[future_campaign_modified["campaignId"] == 55, "profit"] = -999.0
    future_campaign_modified.loc[future_campaign_modified["campaignId"] == 55, "slPrice"] = 50.0

    same_campaign_features = build_feature_rows(
        same_campaign_modified,
        trader_meta,
        start_balance=1000.0,
        trader_history_params=history_params,
    )
    future_campaign_features = build_feature_rows(
        future_campaign_modified,
        trader_meta,
        start_balance=1000.0,
        trader_history_params=history_params,
    )

    campaign_54_same = same_campaign_features.loc[same_campaign_features["campaignId"] == 54].reset_index(drop=True)
    campaign_54_future = future_campaign_features.loc[future_campaign_features["campaignId"] == 54].reset_index(drop=True)

    for feature_name in [
        "prior_campaigns",
        "trader_prior_tilt",
        "trader_prior_sl_discipline",
        "trader_prior_survival",
        "is_cold_start",
    ]:
        assert_feature_value_equal(
            campaign_54_same.loc[1, feature_name],
            campaign_54.loc[1, feature_name],
            feature_name,
        )
        assert_feature_value_equal(
            campaign_54_future.loc[0, feature_name],
            campaign_54.loc[0, feature_name],
            feature_name,
        )
