from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_COMMAND_LOG = Path("reports/reproduce_all_commands.log")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full C22 pipeline end to end from one entry point.")
    parser.add_argument(
        "--datasets",
        default="datasets",
        help="Path to the trade datasets root. This may live outside the repo in a clean checkout.",
    )
    parser.add_argument("--balance", type=float, default=10000.0, help="Start balance per account")
    parser.add_argument("--cache", default="cache/xauusd_daily_ohlc.csv", help="Cached XAUUSD daily OHLC CSV path")
    parser.add_argument(
        "--trader-history-k",
        type=float,
        default=5.0,
        help="Empirical-Bayes shrinkage hyperparameter for cross-campaign trader history",
    )
    parser.add_argument(
        "--command-log",
        default=str(DEFAULT_COMMAND_LOG),
        help="Path to the command log emitted by this runner",
    )
    parser.add_argument(
        "--stage3",
        action="store_true",
        help="Also fit the frozen Stage 3 artifact and regenerate reports/stage3_backtest.md",
    )
    return parser.parse_args()


def command_list(args: argparse.Namespace) -> list[list[str]]:
    py = sys.executable
    commands = [
        [py, "pipeline.py", args.datasets, "--balance", str(args.balance), "--era", "primary", "--out", "features.csv"],
        [
            py,
            "build_features.py",
            "--datasets",
            args.datasets,
            "--traders",
            "traders_sanitized.csv",
            "--out",
            "features_v2.csv",
            "--cache",
            args.cache,
            "--balance",
            str(args.balance),
            "--trader-history-k",
            str(args.trader_history_k),
        ],
        [py, "validate_features.py", "--features", "features_v2.csv", "--out", "reports/stage2_validation.md", "--n-folds", "4"],
        [
            py,
            "prune_features_v21.py",
            "--datasets",
            args.datasets,
            "--traders",
            "traders_sanitized.csv",
            "--cache",
            args.cache,
            "--balance",
            str(args.balance),
            "--trader-history-k",
            str(args.trader_history_k),
            "--out-md",
            "reports/feature_prune_v21.md",
            "--out-png",
            "reports/feature_prune_v21_heatmap.png",
        ],
        [
            py,
            "mechanism_decomposition.py",
            "--datasets",
            args.datasets,
            "--traders",
            "traders_sanitized.csv",
            "--cache",
            args.cache,
            "--balance",
            str(args.balance),
            "--trader-history-k",
            str(args.trader_history_k),
            "--out",
            "reports/mechanism_decomposition.md",
        ],
        [
            py,
            "family_g_value.py",
            "--datasets",
            args.datasets,
            "--traders",
            "traders_sanitized.csv",
            "--cache",
            args.cache,
            "--balance",
            str(args.balance),
            "--trader-history-k",
            str(args.trader_history_k),
            "--out",
            "reports/family_g_value.md",
        ],
        [
            py,
            "design_annex_stats.py",
            "--datasets",
            args.datasets,
            "--traders",
            "traders_sanitized.csv",
            "--cache",
            args.cache,
            "--balance",
            str(args.balance),
            "--trader-history-k",
            str(args.trader_history_k),
            "--out",
            "reports/design_annex_stats.md",
        ],
        [py, "-m", "pytest", "-q", "tests/test_features.py", "tests/test_splits.py", "tests/test_ingest.py"],
    ]
    if args.stage3:
        stage3_commands = [
            [
                py,
                "stage3_model.py",
                "--fit-artifact",
                "--features",
                "features_v2.csv",
                "--artifact",
                "artifacts/stage3_v2.json",
            ],
            [
                py,
                "stage3_model.py",
                "--backtest",
                "--features",
                "features_v2.csv",
                "--artifact",
                "artifacts/stage3_v2.json",
                "--datasets",
                args.datasets,
                "--traders",
                "traders_sanitized.csv",
                "--cache",
                args.cache,
                "--out",
                "reports/stage3_backtest.md",
            ],
        ]
        commands[-1].append("tests/test_stage3_model.py")
        # Fit the artifact before the Stage 3 tests, so the documented command
        # also works when the artifact is being regenerated in a clean clone.
        commands[-1:-1] = stage3_commands
    return commands


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    log_path = Path(args.command_log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    commands = command_list(args)
    log_lines = []
    environment = os.environ.copy()
    environment["C22_DATASETS"] = str(Path(args.datasets).resolve())
    for command in commands:
        rendered = shlex.join(command)
        log_lines.append(rendered)
        print(f"$ {rendered}")
        subprocess.run(command, cwd=repo_root, check=True, env=environment)

    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path}")


if __name__ == "__main__":
    main()
