from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from splits import compare_track_reports, fold_attrition_report, get_folds


FEATURES_PATH = Path(__file__).resolve().parents[1] / "features_v2.csv"


def load_features() -> pd.DataFrame:
    return pd.read_csv(FEATURES_PATH)


def test_track_a_matches_current_reported_output():
    features = load_features()
    report = fold_attrition_report(features, track="A")

    assert report["train_rows"].tolist() == [2037, 2986, 4019, 4992]
    assert report["raw_val_rows"].tolist() == [949, 1033, 973, 1590]
    assert report["purged_val_rows"].tolist() == [371, 454, 464, 901]
    assert report["rows_removed"].tolist() == [578, 579, 509, 689]

    expected_attrition = [0.6090621707060064, 0.5605033881897387, 0.5231243576567317, 0.43333333333333335]
    assert report["attrition_pct"].tolist() == pytest.approx(expected_attrition)


def test_track_b_has_no_campaign_overlap_and_zero_attrition():
    features = load_features()
    folds = get_folds(features, track="B")
    primary = features.loc[features["campaignId"].between(53, 65)].copy()
    comparison = compare_track_reports(features)

    for train_idx, val_idx in folds:
        train_campaigns = set(primary.loc[train_idx, "campaignId"].tolist())
        val_campaigns = set(primary.loc[val_idx, "campaignId"].tolist())
        assert train_campaigns
        assert val_campaigns
        assert train_campaigns.isdisjoint(val_campaigns)
        assert max(train_campaigns) < min(val_campaigns)

    track_b = comparison.loc[comparison["track"] == "B"].reset_index(drop=True)
    assert track_b["train_rows"].tolist() == [2037, 2986, 4019, 4992]
    assert track_b["val_rows"].tolist() == [949, 1033, 973, 1590]
    assert track_b["attrition_pct"].tolist() == [0.0, 0.0, 0.0, 0.0]
