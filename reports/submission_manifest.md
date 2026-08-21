# Stage 3 submission manifest

Branch: `stage3-submission`  
Submission commit: generated on 2026-08-21  
Raw campaign data and derived CSV exports are excluded by `.gitignore`.

| File | Size (bytes) | C22 requirement |
|---|---:|---|
| `.gitignore` | 999 | Excludes raw datasets, PII, and derived exports |
| `README.md` | 2110 | Submission entry point and reproduction instructions |
| `requirements.txt` | 113 | Exact pinned environment |
| `reproduce_all.py` | 5673 | One-command reproduction with supplied dataset path |
| `stage3_model.py` | 69105 | Frozen causal V2 model and `predict()` entry point |
| `artifacts/stage3_v2.json` | 24960 | Required frozen coefficients and preprocessing |
| `features.py` | 22851 | Streaming causal feature state |
| `pipeline.py` | 33624 | Fill-to-position collapse and target construction |
| `build_features.py` | 18692 | Feature build pipeline |
| `splits.py` | 9992 | Walk-forward validation splits |
| `validate_features.py` | 8191 | Feature validation generation |
| `prune_features_v21.py` | 11837 | Frozen feature-pruning reproduction dependency |
| `mechanism_decomposition.py` | 16946 | Reproduction dependency for Stage 2 diagnostics |
| `family_g_value.py` | 17163 | Reproduction dependency for Stage 2 diagnostics |
| `design_annex_stats.py` | 18186 | Reproduction dependency for design and power statistics |
| `checks.py` | 16818 | Existing project integrity checks |
| `CLAUDE.md` | 3907 | Project methodology and data-handling constraints |
| `FEATURES.md` | 14682 | Feature definitions and admissibility contract |
| `CONTEXT.md` | 7516 | Project context |
| `stage3_brief.tex` | 2916 | Stage 3 brief source |
| `stage3_report.pdf` | 124655 | Stage 3 brief PDF supplied for submission |
| `reports/stage3_backtest.md` | 20322 | Stage 3 backtest, economics, C66 audit, and power |
| `reports/trials_log_and_power.md` | 37714 | Trials log, FDR correction, and power analysis |
| `reports/common_split_viability.md` | 18568 | Mandated split viability |
| `reports/sl_leak_audit_v2.md` | 14895 | Refreshed stop-loss leakage audit |
| `reports/feature_checks_walkforward.md` | 75577 | Walk-forward feature checks |
| `reports/repro_check.md` | 6433 | Reproduction verification |
| `reports/design_annex_stats.md` | 5779 | Design statistics referenced by Stage 3 |
| `reports/family_g_value.md` | 4434 | Family G validation report |
| `reports/stage2_validation.md` | 14325 | Stage 2 validation report |
| `tests/test_stage3_model.py` | 4643 | Frozen artifact, leakage, determinism, and hidden-data smoke tests |
| `tests/test_features.py` | 18555 | Causal feature and lookahead tests |
| `tests/test_ingest.py` | 2128 | Ingestion and collapse assertions |
| `tests/test_splits.py` | 1911 | Split and purge assertions |
| `C22 - Kickoff Recap (10 Jul 2026).pdf` | 11207 | C22 reference material |
| `C22 veNTUre Programme Structure - July 2026.pdf` | 259381 | C22 reference material |
| `EDA_memo.pdf` | 857160 | Prior analysis reference |
| `document_feature_set.pdf` | 90403 | Feature reference |
| `Trading Challenge Phase 1 Rules.png` | 220305 | Challenge-rule reference |
| `docs/eda_memo.md` | 6753 | Prior analysis source |
| `docs/generate_eda_charts.py` | 7912 | Prior analysis reproduction utility |
| `docs/figures/chart_1_trade_economics.png` | 130621 | Prior analysis figure |
| `docs/figures/chart_2_c53_shift.png` | 225834 | Prior analysis figure |
| `docs/figures/chart_3_fade_triggers.png` | 226867 | Prior analysis figure |
| `docs/figures/chart_4_sizing_paradox.png` | 232338 | Prior analysis figure |
| `.claude/settings.local.json` | 133 | Existing repository configuration |
| `reports/submission_manifest.md` | 3963 | This manifest |

Validation: `pytest -q tests` passes all 20 tests. No tracked file contains an
email-address pattern or raw IPv4 pattern. The word `telegram` appears only in
sanitization, schema, or submission-documentation text; no raw Telegram values
are present.
