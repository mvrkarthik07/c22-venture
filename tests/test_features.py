from __future__ import annotations

import math
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from features import TraderState


def make_trade(
    *,
    open_time: datetime,
    close_time: datetime,
    amount: float,
    net_profit: float,
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
            sl_price=99.0,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=20),
            close_time=base + timedelta(minutes=30),
            amount=0.5,
            net_profit=-20.0,
            sl_price=None,
            tp_price=101.5,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=40),
            close_time=base + timedelta(minutes=50),
            amount=1.0,
            net_profit=-30.0,
            sl_price=98.0,
            tp_price=None,
            exit_type="sl_hit",
        ),
        make_trade(
            open_time=base + timedelta(minutes=60),
            close_time=base + timedelta(minutes=65),
            amount=0.2,
            net_profit=2.0,
            sl_price=None,
            tp_price=None,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=80),
            close_time=base + timedelta(minutes=90),
            amount=0.5,
            net_profit=5.0,
            sl_price=99.5,
            tp_price=101.0,
            exit_type="manual",
        ),
        make_trade(
            open_time=base + timedelta(minutes=100),
            close_time=base + timedelta(minutes=110),
            amount=2.0,
            net_profit=-10.0,
            sl_price=None,
            tp_price=102.0,
            exit_type="manual",
        ),
    ]


def make_config():
    return {
        "start_balance": 1000.0,
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
        left = actual[key]
        right = expected[key]
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
    assert trade_4["trade_index"] == 4
    assert trade_4["log_dt_close"] == pytest.approx(math.log1p(10 * 60))
    assert trade_4["trades_per_hour"] == pytest.approx(4.0)
    assert trade_4["prior_campaigns"] == 2
    assert trade_4["shared_ip"] is True
    assert trade_4["ip_cluster_size"] == 3.0
    assert trade_4["challenge_type"] == "standard"
    assert trade_4["gold_vol_prev_day"] == pytest.approx(0.015)
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


def test_truncated_and_full_sequence_features_are_identical_per_prefix():
    positions = make_sequence()
    full_features = run_sequence(positions)

    for prefix_len in range(1, len(positions) + 1):
        truncated_features = run_sequence(positions[:prefix_len])
        assert_feature_dicts_equal(
            truncated_features[-1],
            full_features[prefix_len - 1],
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
