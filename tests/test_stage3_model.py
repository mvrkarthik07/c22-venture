from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stage3_model


def _synthetic_stream(n: int = 260) -> pd.DataFrame:
    base = datetime(2026, 1, 1, 9, 0, 0)
    rows = []
    for i in range(n):
        open_time = base + timedelta(minutes=3 * i)
        rows.append(
            {
                "campaignId": 53,
                "accountId": "acct-1" if i % 2 else "acct-2",
                "positionId": i,
                "openDateTime": open_time,
                "closeDateTime": open_time + timedelta(minutes=1),
                "campaignDate": open_time.date(),
                "traderKey": "unseen-trader",
                "ipClusterId": 7,
                "sharedIpFlag": False,
                "ip_cluster_size": 1,
                "challenge_type": "11" if i % 2 else "unknown",
                "gold_vol_prev_day": 0.02,
                "amount": 0.2 + (i % 5) * 0.1,
                "openPrice": 2000.0,
                "side": "BUY" if i % 2 else "SELL",
                "netProfit": -3.0 if i % 4 == 0 else 2.0,
                "slPrice": np.nan,
                "tpPrice": np.nan,
                "exit_type": "manual",
            }
        )
    return pd.DataFrame(rows)


def test_stage3_module_exposes_exactly_one_public_function():
    public_functions = [
        name
        for name, value in inspect.getmembers(stage3_model, inspect.isfunction)
        if not name.startswith("_")
    ]
    assert public_functions == ["predict"]


def test_frozen_artifact_and_unseen_trader_are_deterministic():
    artifact_path = Path("artifacts/stage3_v2.json")
    assert artifact_path.exists()
    artifact = stage3_model._load_artifact(artifact_path)
    assert artifact["selected_threshold"] <= artifact["effective_threshold"]
    assert artifact["effective_threshold"] == pytest.approx(0.0)
    assert artifact["training_threshold_n"] >= 30
    assert not set(stage3_model.V2_FEATURES) & stage3_model._FORBIDDEN_CLOSE_COLUMNS

    trades = _synthetic_stream(8).drop(columns=["slPrice", "tpPrice"])
    first = stage3_model.predict(trades)
    second = stage3_model.predict(trades.copy())
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == len(trades)
    assert set(first["decision"]).issubset({"FADE", "ABSTAIN"})


def test_predict_smoke_arbitrary_campaign_unseen_trader_and_nan_features():
    trades = _synthetic_stream(5).copy()
    trades["campaignId"] = [101, 101, 102, 102, 103]
    trades["traderKey"] = ["hidden-trader-a", "hidden-trader-b", "hidden-trader-c", "hidden-trader-d", "hidden-trader-e"]
    trades["ip_cluster_size"] = np.nan
    trades["gold_vol_prev_day"] = np.nan
    output = stage3_model.predict(trades)
    assert len(output) == len(trades)
    assert output["position_key"].notna().all()
    assert output["decision"].isin(["FADE", "ABSTAIN"]).all()


def test_close_only_column_is_rejected_if_added_to_feature_contract(monkeypatch):
    monkeypatch.setattr(stage3_model, "V2_FEATURES", stage3_model.V2_FEATURES + ["profit"])
    with pytest.raises(AssertionError, match="profit"):
        stage3_model._assert_no_feature_leakage()


def test_feature_matrix_build_rejects_banned_column_in_read_values():
    with pytest.raises(AssertionError, match="profit"):
        stage3_model._feature_frame([{"profit": 1.0}])


def test_recompute_after_truncation_is_byte_identical_for_200_positions():
    trades = _synthetic_stream()
    artifact = stage3_model._load_artifact()
    rng = np.random.default_rng(7)
    sampled_positions = rng.choice(np.arange(200), size=200, replace=False)

    for position in sampled_positions:
        k = int(rng.integers(1, min(6, len(trades) - position)))
        prefix = stage3_model._stream_features(trades.iloc[: position + 1], artifact)[0]
        extended = stage3_model._stream_features(trades.iloc[: position + k + 1], artifact)[0]
        left = prefix.iloc[[-1]].reset_index(drop=True)
        right = extended.iloc[[position]].reset_index(drop=True)
        assert pd.util.hash_pandas_object(left, index=False).values.tobytes() == pd.util.hash_pandas_object(
            right, index=False
        ).values.tobytes(), f"future row changed features at position {position}"


def test_forbidden_input_columns_do_not_reach_entry_features():
    trades = _synthetic_stream(4)
    artifact = stage3_model._load_artifact()
    with_close = trades.copy()
    with_close["profit"] = 10_000_000.0
    with_close["commission"] = -10_000_000.0
    without_close = trades.copy()

    left = stage3_model._stream_features(with_close, artifact)[0]
    right = stage3_model._stream_features(without_close, artifact)[0]
    pd.testing.assert_frame_equal(left, right)


def test_transformed_column_sidecar_matches_artifact_position_by_position():
    artifact = stage3_model._load_artifact()
    sidecar = stage3_model._load_transformed_column_contract()
    assert len(sidecar) == 21
    assert artifact["preprocessing"]["transformed_feature_names"] == sidecar
    assert len(artifact["coefficients"]) == len(sidecar)


def test_unseen_challenge_type_raises_at_predict_time():
    trades = _synthetic_stream(4)
    trades.loc[0, "challenge_type"] = "unseen-level"
    with pytest.raises(ValueError, match="Unseen categorical level"):
        stage3_model.predict(trades)


def test_missing_expected_challenge_type_level_raises_at_matrix_contract():
    artifact = stage3_model._load_artifact()
    params = dict(artifact["preprocessing"])
    params["categorical_categories"] = dict(params["categorical_categories"])
    params["categorical_categories"]["challenge_type"] = ["11"]
    with pytest.raises(AssertionError, match="missing=.*unknown"):
        stage3_model._assert_categorical_contract(
            params,
            stage3_model._load_transformed_column_contract(),
            context="test",
        )


def test_predict_missing_expected_challenge_type_level_raises():
    trades = _synthetic_stream(4)
    trades["challenge_type"] = "11"
    with pytest.raises(ValueError, match="Missing expected categorical level"):
        stage3_model.predict(trades)


def test_permuting_input_columns_does_not_change_output():
    trades = _synthetic_stream(12).drop(columns=["slPrice", "tpPrice"])
    expected = stage3_model.predict(trades)
    permuted = trades.loc[:, list(reversed(trades.columns))]
    actual = stage3_model.predict(permuted)
    pd.testing.assert_frame_equal(expected, actual)


def test_shuffling_input_rows_preserves_per_trade_predictions():
    trades = _synthetic_stream(18).drop(columns=["slPrice", "tpPrice"])
    expected = stage3_model.predict(trades).set_index("position_key").sort_index()
    shuffled = trades.sample(frac=1.0, random_state=123).reset_index(drop=True)
    actual = stage3_model.predict(shuffled).set_index("position_key").sort_index()
    pd.testing.assert_frame_equal(expected, actual)


def test_seeded_causal_rebuild_is_bit_identical_for_sampled_state():
    artifact = stage3_model._load_artifact()
    result = stage3_model._assert_causal_rebuild(
        _synthetic_stream(80).drop(columns=["slPrice", "tpPrice"]),
        artifact,
        sample_size=16,
        seed=7,
    )
    assert result == {"sample_size": 16, "seed": 7, "state_rows": 80, "mismatches": 0}
