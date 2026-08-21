# C22 veNTUre Stage 3 submission

Reproduce the frozen V2 model, repaired ingestion, backtest, reports, and tests with:

```bash
python reproduce_all.py --stage3 --datasets ./datasets
```

`--datasets` is the path to C22's supplied campaign-data directory; it may be any
local path and is not hardcoded.

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
- `tests/` — the 20 ingestion, feature, split, leakage, determinism, and hidden-data smoke tests.

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
