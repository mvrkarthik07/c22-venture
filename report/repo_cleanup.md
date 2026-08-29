# Repository cleanup audit

Audit date: 2026-08-28  
Repository: `/Users/karthik/catch22_venture`  
Branch: `stage3-submission`  
Frozen tag: `stage3-submission-2026-08-21`  
HEAD: `dd51d7a65b33820844dca22ccd43409fd74f1f5f`

## Stop condition

Cleanup stopped before any deletion or `.gitignore` change because the tracked
tree contains C22-supplied/proprietary-looking materials. The hard constraint
requires reporting this immediately and stopping if any C22-proprietary file
was ever committed.

Tracked files triggering the stop condition:

- `C22 - Kickoff Recap (10 Jul 2026).pdf` — 11,207 bytes
- `C22 veNTUre Programme Structure - July 2026.pdf` — 259,381 bytes
- `Trading Challenge Phase 1 Rules.png` — 220,305 bytes

These files were added in commit `06efdd5` (2026-08-21), and the first two
also appear in earlier project commits. No history rewrite was attempted.

## Part 1 — safety audit

- `artifacts/stage3_v2.json` remains unchanged at SHA-256:
  `7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b1`.
- Current tracked-path scan: no `datasets/`, raw trade export, CSV, parquet,
  credential, API-key, `.env`, or PII-data filename was found.
- All-ref added-path scan using
  `git log --all --diff-filter=A --name-only`: no dataset, raw export, CSV,
  parquet, credential, API-key, `.env`, or PII-data filename was found.
- Text scan found only schema/documentation references such as `email`,
  `ip_address`, and `telegram_username`; no raw values were emitted.
- Current working tree size: approximately 29 MB.
- Tracked file count: 52.
- Tracked files over 5 MB: none.
- Git LFS: not in use (`git lfs ls-files` empty; no `.gitattributes`).

### Largest tracked files

| Bytes | Path |
|---:|---|
| 857,160 | `EDA_memo.pdf` |
| 259,381 | `C22 veNTUre Programme Structure - July 2026.pdf` |
| 232,338 | `docs/figures/chart_4_sizing_paradox.png` |
| 226,867 | `docs/figures/chart_3_fade_triggers.png` |
| 225,834 | `docs/figures/chart_2_c53_shift.png` |
| 220,305 | `Trading Challenge Phase 1 Rules.png` |
| 130,621 | `docs/figures/chart_1_trade_economics.png` |
| 124,655 | `stage3_report.pdf` |
| 100,601 | `stage3_model.py` |
| 90,403 | `document_feature_set.pdf` |
| 75,577 | `reports/feature_checks_walkforward.md` |
| 58,923 | `reports/archive/balance_inference_max_drawdown_usd.png` |
| 54,119 | `reports/archive/balance_inference_max_profit_usd.png` |
| 38,835 | `reports/trials_log_and_power.md` |
| 33,624 | `pipeline.py` |
| 24,960 | `artifacts/stage3_v2.json` |
| 22,851 | `features.py` |
| 20,975 | `reports/stage3_backtest.md` |
| 18,692 | `build_features.py` |
| 18,568 | `reports/common_split_viability.md` |

### `.gitignore` coverage

Present: `datasets/`, `data/`, `*.csv`, `*.xlsx`, `*.xls`, `*.zip`,
`__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`,
`.ipynb_checkpoints/`, `.DS_Store`, editor junk, virtual environments, logs,
and `outputs/`.

Not present as a general pattern: `*.parquet` and `.env`/`.env.*`. The current
`.gitignore` also has a specific exception for `requirements.csv` and a
reference-document exception for a differently spelled filename;
`Glossory of User Trading Data.xlsx` is currently ignored by the broad
`*.xlsx` rule.

## Part 2 — inventory status

The complete read-only tracked inventory was collected before stopping. Main
groups are:

- Production/reproduction code: `stage3_model.py`, `features.py`, `pipeline.py`,
  `reproduce_all.py`, `build_features.py`, `splits.py`, `validate_features.py`.
- Tests: `tests/test_features.py`, `tests/test_ingest.py`,
  `tests/test_splits.py`, `tests/test_stage3_model.py`.
- Submission evidence: all tracked files under `reports/`, including
  `reports/archive/`, plus tracked analysis PDFs and `docs/` artifacts.
- Analysis/scratch candidates: `checks.py`, `balance_inference.py`,
  `balance_verification.py`, `ci_diagnosis.py`, `design_annex_stats.py`,
  `family_g_value.py`, `feature_checks_walkforward.py`,
  `mechanism_decomposition.py`, `prune_features_v21.py`, and `repro_check.py`.
- Documentation and references: `README.md`, `CLAUDE.md`, `CONTEXT.md`,
  `FEATURES.md`, `docs/eda_memo.md`, `reports/README.md`, and the tracked
  source/reference PDFs and image.
- Configuration/dependencies: `.gitignore`, `.claude/settings.local.json`,
  `requirements.txt`.
- Frozen artifact: `artifacts/stage3_v2.json`.

Import tracing performed before the stop showed that `stage3_model.py` imports
`features.py`; the Stage 3 tests import `stage3_model.py`; and
`reproduce_all.py` invokes the Stage 2 builders/validators and the Stage 3
entry point. The listed analysis scripts import shared pipeline/feature/split
modules but are standalone reporting entry points; no deletion decision was
made because the stop condition prohibits proceeding to cleanup.

Current untracked files are the transformed-column sidecar, seven `audit/*.md`
files, nine `report/*.md` files plus this report, and `requirements.lock`.
They were not deleted or staged. Current ignored files include Python caches,
`.pytest_cache`, `.DS_Store`, local datasets, generated CSVs, cached market
data, and ignored scratch/report outputs.

## Deletions performed

None. No file was moved, renamed, deleted, or modified by the cleanup audit.
No `.gitignore` change was made.

Observed safe-delete candidates, intentionally untouched because of the stop
condition:

- `.DS_Store`
- `.pytest_cache/`
- `__pycache__/`, `docs/__pycache__/`, and `tests/__pycache__/`
- all `*.pyc`
- ignored generated CSV/cache files (`features.csv`, `features_v2.csv`,
  `traders_sanitized.csv`, `cache/xauusd_daily_ohlc.csv`)

The generated CSV/cache files are not deleted here because the requested
operation has stopped and because some are inputs to tests or reproduction
workflows.

## PROPOSED — requires user decision

- Tracked C22 source materials listed under **Stop condition** — remove from
  the repository and address history exposure only after explicit direction.
- Standalone analysis scripts listed under **Part 2** — possible scratch code;
  retain unless import/reproduction guarantees are reviewed separately.
- Untracked `audit/*.md` and `report/*.md` files — retain as user-generated
  audit evidence unless explicitly approved for deletion.
- Untracked `artifacts/stage3_v2_transformed_columns.json` — referenced by
  `stage3_model.py`; do not delete without confirming hidden-data execution.
- Untracked `requirements.lock` — possible reproducibility dependency lock;
  retain unless intentionally superseded.
- Older tracked reports and archive reports — submission evidence; no deletion
  was attempted.

## Verification not run

The full test suite, deletion pass, `.gitignore` update, and clean-clone
reproduction verification were not run because the explicit sensitive-file
stop condition was triggered. The pre-cleanup status already contained
intentional/uncommitted changes:

`README.md`, `reports/stage3_backtest.md`, `reports/trials_log_and_power.md`,
`stage3_model.py`, `tests/test_stage3_model.py`, and the untracked files noted
above.
