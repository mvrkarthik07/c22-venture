from __future__ import annotations

import math

import numpy as np
import pandas as pd

PRIMARY_CAMPAIGN_MIN = 53
PRIMARY_CAMPAIGN_MAX = 65
DEFAULT_N_FOLDS = 4
MIN_TRAIN_CAMPAIGNS = 4
FLAGGED_SYNCHRONOUS_PAIRS = {
    (1, 63),
    (8, 63),
    (21, 54),
    (31, 57),
    (31, 59),
    (42, 59),
    (42, 60),
}
VALID_TRACKS = {"A", "B"}


def _primary_era(features_df: pd.DataFrame) -> pd.DataFrame:
    mask = features_df["campaignId"].between(PRIMARY_CAMPAIGN_MIN, PRIMARY_CAMPAIGN_MAX)
    return features_df.loc[mask].copy()


def _validation_block_sizes(n_campaigns: int, n_folds: int) -> list[int]:
    if n_campaigns < MIN_TRAIN_CAMPAIGNS + n_folds:
        raise ValueError(
            f"Need at least {MIN_TRAIN_CAMPAIGNS + n_folds} campaigns for "
            f"{n_folds} folds; got {n_campaigns}"
        )

    remaining = n_campaigns - MIN_TRAIN_CAMPAIGNS
    base = remaining // n_folds
    remainder = remaining % n_folds
    sizes = [base] * n_folds
    for idx in range(remainder):
        sizes[-(idx + 1)] += 1
    if any(size <= 0 for size in sizes):
        raise ValueError(f"Invalid fold sizing derived from {n_campaigns=} and {n_folds=}")
    return sizes


def _campaign_windows(campaigns: list[int], n_folds: int) -> list[tuple[list[int], list[int]]]:
    val_sizes = _validation_block_sizes(len(campaigns), n_folds)
    windows: list[tuple[list[int], list[int]]] = []
    train_end = MIN_TRAIN_CAMPAIGNS
    for val_size in val_sizes:
        train_campaigns = campaigns[:train_end]
        val_campaigns = campaigns[train_end:train_end + val_size]
        windows.append((train_campaigns, val_campaigns))
        train_end += val_size
    return windows


def _flagged_sync_mask(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        [(pd.notna(ip_cluster_id) and (ip_cluster_id, campaign_id) in FLAGGED_SYNCHRONOUS_PAIRS)
         for ip_cluster_id, campaign_id in zip(df["ipClusterId"], df["campaignId"])],
        index=df.index,
    )


def _validate_track(track: str) -> str:
    track = track.upper()
    if track not in VALID_TRACKS:
        raise ValueError(f"track must be one of {sorted(VALID_TRACKS)}; got {track!r}")
    return track


def compute_fold_metadata(
    features_df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
    *,
    track: str = "A",
) -> tuple[list[tuple[np.ndarray, np.ndarray]], pd.DataFrame]:
    track = _validate_track(track)
    primary = _primary_era(features_df)
    campaigns = sorted(primary["campaignId"].dropna().unique().tolist())
    windows = _campaign_windows(campaigns, n_folds)

    folds: list[tuple[np.ndarray, np.ndarray]] = []
    report_rows: list[dict] = []

    for fold_idx, (train_campaigns, val_campaigns) in enumerate(windows, start=1):
        train_mask = primary["campaignId"].isin(train_campaigns)
        raw_val_mask = primary["campaignId"].isin(val_campaigns)

        train_df = primary.loc[train_mask]
        raw_val_df = primary.loc[raw_val_mask]

        if track == "A":
            train_trader_keys = set(train_df["traderKey"].dropna().astype(str))
            train_ip_clusters = set(train_df["ipClusterId"].dropna().tolist())

            trader_overlap = raw_val_df["traderKey"].astype(str).isin(train_trader_keys)
            trader_overlap = trader_overlap & raw_val_df["traderKey"].notna()

            ip_overlap = raw_val_df["ipClusterId"].isin(train_ip_clusters)
            ip_overlap = ip_overlap & raw_val_df["ipClusterId"].notna()
            flagged_sync = _flagged_sync_mask(raw_val_df)
            targeted_ip_overlap = ip_overlap & flagged_sync

            broad_purge = trader_overlap | ip_overlap
            targeted_purge = trader_overlap | targeted_ip_overlap
            purged_val_df = raw_val_df.loc[~targeted_purge]
        else:
            trader_overlap = pd.Series(False, index=raw_val_df.index)
            ip_overlap = pd.Series(False, index=raw_val_df.index)
            targeted_ip_overlap = pd.Series(False, index=raw_val_df.index)
            broad_purge = pd.Series(False, index=raw_val_df.index)
            purged_val_df = raw_val_df

        train_idx = train_df.index.to_numpy()
        val_idx = purged_val_df.index.to_numpy()
        folds.append((train_idx, val_idx))

        raw_val_rows = len(raw_val_df)
        purged_val_rows = len(purged_val_df)
        rows_removed = raw_val_rows - purged_val_rows
        attrition_pct = rows_removed / raw_val_rows if raw_val_rows else math.nan

        trader_only_rows = int((trader_overlap & ~ip_overlap).sum())
        ip_only_rows = int((ip_overlap & ~trader_overlap).sum())
        both_rows = int((trader_overlap & ip_overlap).sum())
        broad_rows_removed = int(broad_purge.sum())
        broad_attrition_pct = broad_rows_removed / raw_val_rows if raw_val_rows else math.nan
        targeted_ip_only_rows = int((targeted_ip_overlap & ~trader_overlap).sum())
        targeted_both_rows = int((targeted_ip_overlap & trader_overlap).sum())

        raw_val_accounts = raw_val_df["accountId"].nunique()
        purged_val_accounts = purged_val_df["accountId"].nunique()
        accounts_removed = raw_val_accounts - purged_val_accounts
        account_attrition_pct = accounts_removed / raw_val_accounts if raw_val_accounts else math.nan

        report_rows.append(
            {
                "fold": fold_idx,
                "track": track,
                "train_campaigns": train_campaigns,
                "val_campaigns": val_campaigns,
                "train_rows": len(train_df),
                "raw_val_rows": raw_val_rows,
                "purged_val_rows": purged_val_rows,
                "rows_removed": rows_removed,
                "attrition_pct": attrition_pct,
                "trader_only_rows": trader_only_rows,
                "ip_only_rows": ip_only_rows,
                "both_rows": both_rows,
                "broad_rows_removed": broad_rows_removed,
                "broad_attrition_pct": broad_attrition_pct,
                "targeted_ip_only_rows": targeted_ip_only_rows,
                "targeted_both_rows": targeted_both_rows,
                "train_accounts": train_df["accountId"].nunique(),
                "raw_val_accounts": raw_val_accounts,
                "purged_val_accounts": purged_val_accounts,
                "accounts_removed": accounts_removed,
                "account_attrition_pct": account_attrition_pct,
            }
        )

    return folds, pd.DataFrame(report_rows)


def fold_attrition_report(
    features_df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
    *,
    track: str = "A",
) -> pd.DataFrame:
    _, report = compute_fold_metadata(features_df, n_folds=n_folds, track=track)
    return report


def get_folds(
    features_df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
    *,
    track: str = "A",
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return walk-forward campaign-blocked folds for the requested evaluation track.

    Track A is the conservative unseen-trader benchmark: it keeps the current
    traderKey purge plus targeted ipClusterId purge for the 7 known synchrony
    pairs. Track B uses the same expanding campaign windows but applies no
    identity purge at all. This does not introduce lookahead because train
    campaigns still strictly precede validation campaigns; it only permits
    identity overlap. That makes Track B the production analogue for Stage 4,
    where returning traders are expected, while Track A remains the floor for
    generalization to unseen traders.
    """
    folds, _ = compute_fold_metadata(features_df, n_folds=n_folds, track=track)
    return folds


def compare_track_reports(
    features_df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
) -> pd.DataFrame:
    report_a = fold_attrition_report(features_df, n_folds=n_folds, track="A")
    report_b = fold_attrition_report(features_df, n_folds=n_folds, track="B")
    comparison = pd.concat(
        [
            report_a.assign(val_rows=report_a["purged_val_rows"])[
                ["track", "fold", "train_rows", "val_rows", "attrition_pct"]
            ],
            report_b.assign(val_rows=report_b["purged_val_rows"])[
                ["track", "fold", "train_rows", "val_rows", "attrition_pct"]
            ],
        ],
        ignore_index=True,
    )
    return comparison.sort_values(["fold", "track"]).reset_index(drop=True)


def print_track_comparison(
    features_df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
) -> pd.DataFrame:
    comparison = compare_track_reports(features_df, n_folds=n_folds)
    print("track comparison:")
    print(
        comparison.to_string(
            index=False,
            float_format=lambda value: f"{value:.1%}" if 0 <= value <= 1 else f"{value:.0f}",
        )
    )
    return comparison


def make_folds(features_df: pd.DataFrame, n_folds: int = DEFAULT_N_FOLDS) -> list[tuple[np.ndarray, np.ndarray]]:
    folds, report = compute_fold_metadata(features_df, n_folds=n_folds, track="A")
    print("purge decomposition (broad traderKey OR ipClusterId rule):")
    print(
        report[
            [
                "fold",
                "train_campaigns",
                "val_campaigns",
                "trader_only_rows",
                "ip_only_rows",
                "both_rows",
                "broad_rows_removed",
                "broad_attrition_pct",
            ]
        ].to_string(index=False, float_format=lambda value: f"{value:.1%}" if 0 <= value <= 1 else f"{value:.0f}")
    )
    print()
    for row in report.itertuples(index=False):
        print(
            f"fold {row.fold}: train {row.train_campaigns} -> val {row.val_campaigns} | "
            f"val rows {row.raw_val_rows} -> {row.purged_val_rows} "
            f"({row.attrition_pct:.1%} attrition; targeted ip-only removals={row.targeted_ip_only_rows}), "
            f"accounts {row.raw_val_accounts} -> {row.purged_val_accounts} "
            f"({row.account_attrition_pct:.1%} attrition)"
        )
    return folds
