# Deterministic reproduction check

Date: 2026-08-26  
Repository: `stage3-submission`  
Submitted tag: `stage3-submission-2026-08-21` (`dd51d7a65b33820844dca22ccd43409fd74f1f5f`)

## Result at a glance

The frozen tag reproduces the fitted artifact byte-for-byte. The clean-tag run
took **119.46 s wall time** and passed **20 tests**. The current worktree, which
contains the eight uncommitted Stage-3 compliance tests, took **98.37 s wall
time** and passed **28 tests** in an isolated overlay. These are reported
separately because the eight tests are not present in the frozen tag.

Two compliance gaps remain factual and are not hidden by the reproduction
result:

1. Production randomness is fully seeded with value `7`, but the repository
   does not yet have one shared module-level seed constant: it has equivalent
   aliases/literals in `pipeline.py`, `stage3_model.py`, and test/diagnostic
   code.
2. `reproduce_all.py` regenerates the computational outputs listed below, but
   several submitted audit reports are frozen reports with no generator in the
   repository. Therefore the literal requirement that one command regenerate
   every number in every submitted report is not met by the existing runner.

No estimator, hyperparameter, feature definition, artifact value, hurdle, or
abstain rule was changed for this check.

## Environment and dependency lock

Observed execution environment:

| item | value |
|---|---|
| Python | CPython 3.13.9 (`/opt/anaconda3/bin/python`) |
| pip | 25.3 |
| OS | macOS Darwin 25.5.0, arm64 |
| platform string | `macOS-26.5.2-arm64-arm-64bit-Mach-O` |
| assumptions | Python 3.13 on macOS arm64; C22 datasets and the permitted `traders_sanitized.csv` supplied out-of-tree |

`requirements.txt` already had seven exact direct pins. The new
`requirements.lock` resolves **30 packages**: seven direct packages and 23
transitive packages. Every package line is `name==exact_version` and every
package block has one or more SHA-256 hashes. A `pip install --dry-run
--ignore-installed --require-hashes -r requirements.lock` validation completed
with exit code 0.

Direct pins:

| package | version |
|---|---:|
| numpy | 2.3.5 |
| pandas | 2.3.3 |
| scikit-learn | 1.7.2 |
| requests | 2.32.5 |
| openpyxl | 3.1.5 |
| matplotlib | 3.10.6 |
| pytest | 8.4.2 |

The transitive pins are `certifi==2026.7.22`, `charset-normalizer==3.5.1`,
`colorama==0.4.6` (Windows marker), `contourpy==1.3.3`, `cycler==0.12.1`,
`et-xmlfile==2.0.0`, `fonttools==4.63.0`, `idna==3.19`,
`iniconfig==2.3.0`, `joblib==1.5.3`, `kiwisolver==1.5.0`,
`packaging==26.3`, `pillow==12.3.0`, `pluggy==1.6.0`,
`pygments==2.21.0`, `pyparsing==3.3.2`, `python-dateutil==2.9.0.post0`,
`pytz==2026.3.post1`, `scipy==1.18.1`, `six==1.17.0`,
`threadpoolctl==3.6.0`, `tzdata==2026.3`, and `urllib3==2.7.0`.

The lockfile SHA-256 is:

```text
f4f160120e3de3c88aa62aac70604ee2fc076a68da1567c520dc32cc9ab5db3a  requirements.lock
```

## Randomness audit

The production reproduction path has no unseeded random generator and uses
seed value **7** everywhere it resamples or samples:

| source | operation | seed source | scope |
|---|---|---|---|
| `pipeline.py` | clustered bootstrap: `np.random.default_rng()` and account/trader-cluster `rng.choice()` | `BOOT_SEED = 7` | Stage 1 pipeline and downstream feature-check helpers |
| `stage3_model.py` | backtest account-cluster bootstrap: `default_rng()` and `rng.integers()` | `_BOOT_SEED = 7` | Stage 3 report CIs and MDE calculations |
| current worktree `stage3_model.py` | seeded causal-rebuild samples: `default_rng()` and `rng.choice()` | `_CAUSAL_SEED = 7` | eight uncommitted compliance tests; absent from submitted tag |
| sklearn Ridge | fitting | no RNG / no `random_state` parameter | deterministic estimator path |
| CV/splits in the reproduction command | campaign-ordered splits; no shuffle | no RNG | deterministic split order |

The repository-wide audit also found these deterministic but separate sources:

- `tests/test_stage3_model.py` uses seed `7` for the causal sample and
  `random_state=123` for a row-order permutation test. Both are test-only and
  do not feed fitted values.
- `checks.py` has default seed `7` and a top-level seed literal `7`; it is not
  called by `reproduce_all.py`.
- `ci_diagnosis.py` intentionally sweeps seeds `0..19` for a seed-sensitivity
  diagnostic; it is not a submission regeneration step.

Thus the production path is fixed at `7`, but the strict “single documented
constant for every source in the repository” wording is not yet literally true.
No source uses an unseeded NumPy generator, sklearn random state, sampling, or
shuffling in the one-command path.

## One-command contract

The first screen of `README.md` now documents the single regeneration command:

```bash
python reproduce_all.py --stage3 --datasets /path/to/datasets --cache /path/to/cache/xauusd_daily_ohlc.csv
```

The permitted `traders_sanitized.csv` must be present at the repository root;
raw datasets, PII, CSV feature exports, and cached market data remain outside
the clone or ignored. On the frozen tag the command executed these subcommands:

1. `pipeline.py` -> ignored `features.csv`;
2. `build_features.py` -> ignored `features_v2.csv`;
3. `validate_features.py` -> `reports/stage2_validation.md`;
4. `prune_features_v21.py` -> `reports/feature_prune_v21.md` and its heatmap;
5. `mechanism_decomposition.py`;
6. `family_g_value.py`;
7. `design_annex_stats.py`;
8. `stage3_model.py --fit-artifact`;
9. `stage3_model.py --backtest`;
10. the 20-test suite.

The command log is ignored by design. The submitted audit reports
`trials_log_and_power.md`, `common_split_viability.md`, `submission_manifest.md`,
`sl_leak_audit_v2.md`, `feature_checks_walkforward.md`, `balance_verification.md`,
and other historical/audit files do not have corresponding invocations in
`reproduce_all.py`; their numbers are not regenerated by this command.

## Clean-clone verification

The tag was cloned into a temporary directory. The allowed sanitized trader
metadata and cached OHLC file were copied into that temporary clone; no raw PII
or dataset file was copied into the repository or added to Git. The command was
run with the external dataset path shown above. `README.md` and
`requirements.lock` are current worktree additions and are not part of the
frozen tag clone, so this run used the already-installed environment above; the
new lock was validated separately with pip's hash-enforced dry run.

### Frozen-tag runtime

```text
real 119.46
user 133.51
sys   6.25
20 passed in 4.74s
```

### Generated-output comparison

Hashes below are SHA-256 hashes of the generated file and the committed blob
from the tag. `BYTE_IDENTICAL` is a byte-level comparison, not a semantic
comparison.

| output | result | generated SHA-256 | committed SHA-256 |
|---|---|---|---|
| `reports/stage2_validation.md` | BYTE_IDENTICAL | `29b61da3c1a91ba6414638a3e43327013b5c923299ae8b75d5d431b20591ce02` | same |
| `reports/family_g_value.md` | DIFF | `16201904fd8ef2edc1ce544b3d22cd56d002b29dd700e2d968d0fc9ea6e839a5` | `bbbea8eefbce378715d35cf32abbc584abe3e733879c6a0830af7f18031002f3` |
| `reports/design_annex_stats.md` | BYTE_IDENTICAL | `efec2ec20740f2bf89a85b94d7823e106edebbfcf9d230b0b43b883085cd4c59` | same |
| `artifacts/stage3_v2.json` | BYTE_IDENTICAL | `7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b1` | same |
| `reports/stage3_backtest.md` | BYTE_IDENTICAL | `4c51eb66b8f223fc3e0091cdde50e1f5e8d36f30da8abb95dd24d5ef6d22a89` | same |
| `reports/feature_prune_v21.md` | no committed baseline | `e25b2dcb759aae7e8f394ffc9ba16393050c78450f30727a4f279da8fdb78dc5` | not tracked at tag |
| `reports/feature_prune_v21_heatmap.png` | no committed baseline | `806f3d5d1ee8700eb93e995579b95b9263e04b5c97a0be98a66e29a7387ecad7` | not tracked at tag |
| `reports/mechanism_decomposition.md` | no committed baseline | `95c28b29058dcc3946164eadd36973d51fda60a5d0f96deb40d021c87046ed49` | not tracked at tag |

The only committed-file difference was the known `family_g_value.md` inner-CV
tie. Exact changed rows:

- Fold 2, M1: selected alpha `0.03162` -> `0.003162`; the reported values are
  otherwise unchanged to the displayed precision.
- Pooled, M1: the displayed value `332.8822` -> `332.8823`.

The ignored CSV outputs and command log have no committed counterparts and were
not retained in this report.

### Eight-test worktree timing

An isolated overlay of the current dirty worktree (not the tag) ran the same
entry point in **98.37 s wall time**:

```text
28 passed in 4.64s
```

Its artifact remained byte-identical to the worktree artifact. Its
`reports/stage3_backtest.md` necessarily differed from the frozen report because
the pre-existing uncommitted compliance code changes CI clustering from
`traderKey` to `accountId` and changes interval values; the point estimates and
artifact bytes remained unchanged. This is not counted as a clean-tag result.

## Artifact tracking and digest

`git ls-files --error-unmatch artifacts/stage3_v2.json` confirms the artifact is
tracked. The direct shell command and an independent Python `hashlib` read both
returned the full 64-character digest:

```text
$ shasum -a 256 artifacts/stage3_v2.json
7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b1  artifacts/stage3_v2.json

$ python -c 'import hashlib; print(hashlib.sha256(open("artifacts/stage3_v2.json","rb").read()).hexdigest())'
7d77eb8af7cde7bdef856f0d5a47d28a5881795da0a4cde4ed8421623bc359b1
```

This is 64 hexadecimal characters. It is the same digest before and after the
clean-tag reproduction. No dataset, PII, or C22-proprietary file was added.
