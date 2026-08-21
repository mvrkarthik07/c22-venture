from __future__ import annotations

import os
from pathlib import Path
import re
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import load_all_trades, reverse_profit_per_lot, to_positions, validate_trade_schema


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS = Path(os.environ.get("C22_DATASETS", str(REPO_ROOT / "datasets")))


def test_full_corpus_fills_collapse_to_positions():
    trades = load_all_trades(str(DATASETS))
    positions = to_positions(trades)
    assert len(trades) == 46520
    assert len(positions) == 7277


def test_primary_era_counts():
    positions = to_positions(load_all_trades(str(DATASETS)))
    primary = positions.loc[positions["campaignId"].between(53, 65)]
    assert len(primary) == 6582
    assert primary["accountId"].nunique() == 496
    assert primary["campaignId"].nunique() == 13


def test_collapse_key_is_non_null_after_ingestion():
    trades = load_all_trades(str(DATASETS))
    assert trades[["campaignId", "positionId"]].notna().all().all()


def test_each_trade_file_has_exact_mapped_identifier_columns():
    paths = sorted(
        p
        for p in (DATASETS / "user_trades").iterdir()
        if p.suffix.lower() in {".csv", ".xlsx", ".xls"}
    )
    assert len(paths) == 34
    for path in paths:
        reader = pd.read_excel if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv
        frame = reader(path, nrows=1)
        validate_trade_schema(frame, str(path))
        assert "positionId" in frame.columns


def test_position_pnl_identity_subtracts_seven_once():
    positions = to_positions(load_all_trades(str(DATASETS)))
    positions = positions.loc[positions["amount"].ne(0)].copy()
    gross_loss_per_lot = -positions["profit"] / positions["amount"]
    calculated_reverse = reverse_profit_per_lot(gross_loss_per_lot)
    field_reverse = positions["reverseProfit"] / positions["amount"]

    assert (calculated_reverse - (gross_loss_per_lot - 7.0)).abs().max() == 0.0
    assert (gross_loss_per_lot - (-positions["profit"] / positions["amount"])).abs().max() == 0.0
    assert (calculated_reverse - field_reverse).abs().max() < 1e-9
