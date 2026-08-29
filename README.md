# C22 veNTUre Stage 3 submission

## Reproduce the submission

After installing the locked environment and placing the permitted
`traders_sanitized.csv` at the repository root, run this one regeneration
command (the raw dataset may remain outside the clone):

Install once:
```bash
python -m pip install --require-hashes -r requirements.lock
```

Regenerate everything covered by the runner:
```bash
python reproduce_all.py --stage3 --datasets /path/to/datasets --cache /path/to/cache/xauusd_daily_ohlc.csv
```

`--datasets` and `--cache` are local paths and are not hardcoded. On the
submitted tag, this command took 119.46 s wall time on macOS arm64 with
CPython 3.13.9 and passed 20 tests. It writes/rebuilds:
`features.csv`, `features_v2.csv`, `reports/stage2_validation.md`,
`reports/feature_prune_v21.md`, `reports/feature_prune_v21_heatmap.png`,
`reports/mechanism_decomposition.md`, `reports/family_g_value.md`,
`reports/design_annex_stats.md`, `artifacts/stage3_v2.json`,
`reports/stage3_backtest.md`, and the ignored command log
`reports/reproduce_all_commands.log`. The CSVs and raw/trader input files are
intentionally not tracked.

The lock resolves Python 3.13 dependencies with exact versions and hashes;
see [requirements.lock](requirements.lock). The reproduction seed used by the
production bootstrap and Stage 3 backtest is `7`.

## Stage 4 usage

```python
import pandas as pd
from stage3_model import predict
trades = pd.read_csv("new_trades.csv")
decisions = predict(trades)
print(decisions[["position_key", "decision", "score"]])
```

Pass trades in arrival order. `predict()` loads the frozen artifact, computes only
entry-time features, handles unseen traders and missing features, and returns one
decision per input row.

## File manifest

- `stage3_model.py` — frozen causal V2 Ridge runtime and backtest; exposes `predict()`.
- `artifacts/stage3_v2.json` — versioned coefficients, preprocessing, alpha, and threshold.
- `features.py`, `pipeline.py`, `splits.py`, `build_features.py` — causal features, repaired fill-to-position ingestion, and validation splits.
- `reproduce_all.py` — one-command clean-clone reproduction with `--datasets`.
- `reports/stage3_backtest.md` — Stage 3 performance, economics, C66 audit, and power analysis.
- `reports/trials_log_and_power.md` — trials log, multiple-testing correction, and power work.
- `reports/common_split_viability.md` — mandated split and feature viability.
- `reports/sl_leak_audit_v2.md` — refreshed stop-loss leakage audit.
- `reports/feature_checks_walkforward.md` — walk-forward feature checks.
- `reports/repro_check.md` — reproduction verification.
- `stage3_report.pdf` — Current Stage 3 submission brief PDF.
- `FEATURES.md`, `CLAUDE.md` — feature contract and project methodology.
- `tests/` — the submitted tag contains 20 ingestion, feature, split, leakage,
  determinism, and hidden-data smoke tests; the current compliance worktree
  contains 28 after eight additional checks.

Raw `datasets/`, CSV exports, and trader metadata are intentionally excluded.

## Environment

Python 3.13; install exact dependencies with:

```bash
python -m pip install -r requirements.txt
```

Run the full suite with:

```bash
pytest -q tests
```
