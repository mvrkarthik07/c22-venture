# Repro Check

## Clean-Clone Run

The code checkout was cloned fresh on Saturday, July 25, 2026. Because the repo had uncommitted working-tree changes at audit time, the fresh clone was overlaid with the current source tree while explicitly excluding `datasets/`, generated CSVs, cached market data, and prior reports. Because `datasets/` is intentionally untracked, the single entry point was then run against an external datasets path instead of relying on repo-tracked data files.

Exact top-level commands executed:

| step | command |
| --- | --- |
| clean_clone | git clone --no-local /Users/karthik/catch22_venture /var/folders/p6/kpxd87rn5d7fmsjddrn7bjq00000gn/T/catch22_repro_clone_9w8i_sm9/repo |
| overlay_current_worktree | rsync -a --exclude .git/ --exclude datasets/ --exclude features.csv --exclude features_v2.csv --exclude traders_sanitized.csv --exclude reports/ --exclude cache/xauusd_daily_ohlc.csv --exclude __pycache__/ --exclude .pytest_cache/ /Users/karthik/catch22_venture/ /var/folders/p6/kpxd87rn5d7fmsjddrn7bjq00000gn/T/catch22_repro_clone_9w8i_sm9/repo/ |
| single_entry_point | /opt/anaconda3/bin/python reproduce_all.py --datasets /Users/karthik/catch22_venture/datasets --balance 10000.0 |

Commands executed by the single entry point:

| step | command |
| --- | --- |
| entrypoint_1 | /opt/anaconda3/bin/python pipeline.py /Users/karthik/catch22_venture/datasets --balance 10000.0 --era primary --out features.csv |
| entrypoint_2 | /opt/anaconda3/bin/python build_features.py --datasets /Users/karthik/catch22_venture/datasets --traders traders_sanitized.csv --out features_v2.csv --cache cache/xauusd_daily_ohlc.csv --balance 10000.0 --trader-history-k 5.0 |
| entrypoint_3 | /opt/anaconda3/bin/python validate_features.py --features features_v2.csv --out reports/stage2_validation.md --n-folds 4 |
| entrypoint_4 | /opt/anaconda3/bin/python prune_features_v21.py --datasets /Users/karthik/catch22_venture/datasets --traders traders_sanitized.csv --cache cache/xauusd_daily_ohlc.csv --balance 10000.0 --trader-history-k 5.0 --out-md reports/feature_prune_v21.md --out-png reports/feature_prune_v21_heatmap.png |
| entrypoint_5 | /opt/anaconda3/bin/python mechanism_decomposition.py --datasets /Users/karthik/catch22_venture/datasets --traders traders_sanitized.csv --cache cache/xauusd_daily_ohlc.csv --balance 10000.0 --trader-history-k 5.0 --out reports/mechanism_decomposition.md |
| entrypoint_6 | /opt/anaconda3/bin/python family_g_value.py --datasets /Users/karthik/catch22_venture/datasets --traders traders_sanitized.csv --cache cache/xauusd_daily_ohlc.csv --balance 10000.0 --trader-history-k 5.0 --out reports/family_g_value.md |
| entrypoint_7 | /opt/anaconda3/bin/python design_annex_stats.py --datasets /Users/karthik/catch22_venture/datasets --traders traders_sanitized.csv --cache cache/xauusd_daily_ohlc.csv --balance 10000.0 --trader-history-k 5.0 --out reports/design_annex_stats.md |
| entrypoint_8 | /opt/anaconda3/bin/python -m pytest -q tests/test_features.py tests/test_splits.py |

Clone/overlay command output summary:

```text
Cloning into '/var/folders/p6/kpxd87rn5d7fmsjddrn7bjq00000gn/T/catch22_repro_clone_9w8i_sm9/repo'...
```

Single-entry command stdout/stderr are omitted here for brevity; the exact subcommands are recorded above and in `reports/reproduce_all_commands.log` inside the clone.

## Regression Checks

| name | status | expected | actual | method |
| --- | --- | --- | --- | --- |
| reverseProfit identity | PASS | all campaigns except C41 satisfy reverseProfit = -profit - 7.00*amount; C41 uses 6.50 | max_abs_non_C41=4.54747350886464e-13; max_abs_C41=2.27373675443232e-13 | position-level exact identity on deduplicated positions |
| mean net -42.75 = gross -1.63 + commission -41.12 | PASS | -42.75 = -1.63 + -41.12 | full-corpus position means are net=-42.7474920983922, gross=-1.62620997663872, commission=-41.1212821217535 | full-corpus (34-campaign, 7277-position) audit with gross=profit and commission=netProfit-profit |
| median gross +1.84 | PASS | +1.84 | full-corpus median gross (profit)=1.84 | full-corpus (34-campaign, 7277-position) audit with gross=profit |
| loss_streak >= 2 | PASS | mean 40.54; trader CI [11.36, 70.21]; ip CI [10.79, 68.00] | mean=40.538441; trader CI=[11.36, 70.21]; ip CI=[10.79, 68.00] | primary-era trigger on clone-generated features.csv |
| loss_streak >= 2 AND small_size_flag | FAIL | mean 114.84; trader CI [32.47, 198.33]; ip CI [31.53, 193.50]; n=251; accounts=150 | mean=114.844335; trader CI=[35.89, 193.75]; ip CI=[33.74, 190.07]; n=251; accounts=150 | primary-era interaction on clone-generated features.csv; accounts counted as distinct (campaignId, accountId) |
| equal-weighted 12.44 vs size-weighted 4.00 | PASS | 12.44 vs 4.00 | 12.436357 vs 3.998612 | primary-era gross_loss_per_lot mean and -sum(profit)/sum(amount) |
| Spearman(size, loss/lot) ~ -0.004 | PASS | ~ -0.004 | -0.003596051628 | primary-era Spearman correlation on clone-generated features.csv |
| primary era counts | PASS | 6582 positions; 13 campaigns; 496 active accounts | 6582 positions; 13 campaigns; 496 active accounts | clone-generated features.csv with pipeline era_mask(primary) |
| corpus fills -> positions | PASS | 46520 fills -> 7277 positions | 46520 fills -> 7277 positions | raw trade loader and position dedupe on external datasets root |
| no tracked dataset artifacts | PASS | datasets/, features_v2.csv, traders_sanitized.csv are not tracked | none tracked | git ls-files on repo root |

## SL Usage Change at C53

| definition | prelude_rate | primary_rate | drop_pp |
| --- | --- | --- | --- |
| position_weighted | 0.985569985569986 | 0.761622607110301 | 22.3947378459685 |
| campaign_level_mean | 0.985549073766796 | 0.763070370300358 | 22.2478703466438 |
| account_campaign_mean | 0.986834230999401 | 0.761455469755911 | 22.537876124349 |

Canonical definition: **position-weighted SL-set rate by era on deduplicated positions**. That yields `98.5569985569986% -> 76.1622607110301%`, a drop of `22.3947378459685` percentage points. This is the canonical number because it matches the Stage 1 era chart and the prose in `docs/eda_memo.md`, both of which summarize position-level behavior rather than campaign means or account-level means.

## Artifact Check

- `features.csv` exists in clone: `True`.
- `features_v2.csv` exists in clone: `True`.
- `traders_sanitized.csv` exists in clone: `True`.
