# In-sample versus out-of-sample gap

Date: 2026-08-25

The frozen V2 model was run through the public `predict()` entry point on the
collapsed position stream. The V3 results use the public `predict()` entry
point and the clean-feature artifact on branch `stage3-tp-remediation`:
`artifacts/stage3_v3_clean.json`. Public `predict()` and the backtest decision
path agreed on all 7,277 rows for each artifact.

The IS window is campaigns C33-C52, `n=694`. Under the corrected convention,
the OOS window is C53-C65, `n=6,582`; C66 is excluded from coverage and per-lot
metrics as well as dollar totals. There is no C66 row in IS, so the IS dollar
totals exclude no training row.

The superseded full-predict OOS path acted on 178 V2 rows and 6 V3 rows,
including the same C66 row. After excluding C66, V2 acts on 177 rows and V3 on
5 rows. The C66 dollar contribution is `-$4,019.40`; it remains excluded from
the dollar totals and is also excluded from the corrected coverage, EW/lot, and
SW/lot calculations.

EW/lot is the arithmetic mean of `reverseProfit / amount`. SW/lot is total
`reverseProfit` divided by total lots. Each interval is a 95% bootstrap with
2,000 replicates, seed 7, resampling `accountId` clusters with all selected
trades per sampled account.

## V2 panel

| window | rows | acted n | coverage | EW/lot (accountId 95% CI) | SW/lot (accountId 95% CI) | dollar total |
|---|---:|---:|---:|---|---|---:|
| IS, C33-C52 | 694 | 4 | 0.5764% | 50.8966 [-37.2130, 142.1230] | -6.1469 [-15.4355, 119.6575] | -$1,251.21 |
| OOS, C53-C65 | 6,582 | 177 | 2.6892% | 10.4327 [-46.117, 66.826] | -33.8486 [-70.260, 2.964] | -$3,556.81 |

### V2 IS/OOS gaps

Gaps are OOS minus IS. Coverage gaps are percentage points.

| metric | IS | OOS | gap |
|---|---:|---:|---:|
| coverage | 0.5764% | 2.6892% | +2.1128 pp |
| acted n | 4 | 177 | +173 |
| EW/lot | 50.8966 | 10.4327 | -40.4639 |
| SW/lot | -6.1469 | -33.8486 | -27.7017 |
| dollar total | -$1,251.21 | -$3,556.81 | -$2,305.60 |

## V3 clean-feature panel

V3 retains the 9 clean features, including `challenge_type`, and uses the
branch artifact without refitting in this report.

| window | rows | acted n | coverage | EW/lot (accountId 95% CI) | SW/lot (accountId 95% CI) | dollar total |
|---|---:|---:|---:|---|---|---:|
| IS, C33-C52 | 694 | 2 | 0.2882% | -37.2130 [-62.9240, -11.5020] | -12.7973 [-62.9240, -11.5020] | -$2,474.11 |
| OOS, C53-C65 | 6,582 | 5 | 0.0760% | 243.0120 [-78.775, 572.100] | 228.1797 [-133.868, 655.217] | +$292.07 |

### V3 IS/OOS gaps

Gaps are OOS minus IS. Coverage gaps are percentage points.

| metric | IS | OOS | gap |
|---|---:|---:|---:|
| coverage | 0.2882% | 0.0760% | -0.2122 pp |
| acted n | 2 | 5 | +3 |
| EW/lot | -37.2130 | 243.0120 | +280.2250 |
| SW/lot | -12.7973 | 228.1797 | +240.9770 |
| dollar total | -$2,474.11 | +$292.07 | +$2,766.18 |

### V3 IS interval check

The premise that one of the two V3 IS intervals is incorrect is not borne out
by the frozen accountId bootstrap. Both acted trades are singleton accountId
clusters (`n=2`, two clusters), so the 2,000-resample percentile endpoints are
the two observed EW endpoints and are also the two observed SW endpoints:
EW `-37.2130/lot`, 95% CI `[-62.9240, -11.5020]`; SW `-12.7973/lot`, 95% CI
`[-62.9240, -11.5020]`. Neither interval should be changed.

## Training per-campaign breakdown

The coverage percentage in this table is within the campaign. A dash means no
trade was acted on in that campaign, so no per-campaign EW/SW interval exists.
The C41 one-position test campaign is part of the mandated IS window.

| campaign | all n | V2 acted (coverage) | V2 EW/lot [95% CI] | V2 SW/lot [95% CI] | V2 dollars | V3 acted (coverage) | V3 EW/lot [95% CI] | V3 SW/lot [95% CI] | V3 dollars |
|---|---:|---:|---|---|---:|---:|---|---|---:|
| C33 | 33 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C34 | 41 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C35 | 33 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C36 | 41 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C37 | 32 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C38 | 39 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C39 | 35 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C40 | 43 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C41 | 1 | 1 (100.00%) | -11.502 [-11.502, -11.502] | -11.502 [-11.502, -11.502] | $-2,167.67 | 1 (100.00%) | -11.502 [-11.502, -11.502] | -11.502 [-11.502, -11.502] | $-2,167.67 |
| C42 | 39 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C43 | 27 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C44 | 31 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C45 | 35 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C46 | 30 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C47 | 38 | 1 (2.63%) | 84.681 [84.681, 84.681] | 84.681 [84.681, 84.681] | $586.84 | 0 | — | — | $0.00 |
| C48 | 43 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C49 | 35 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |
| C50 | 40 | 1 (2.50%) | 193.331 [193.331, 193.331] | 193.331 [193.331, 193.331] | $636.06 | 0 | — | — | $0.00 |
| C51 | 39 | 1 (2.56%) | -62.924 [-62.924, -62.924] | -62.924 [-62.924, -62.924] | $-306.44 | 1 (2.56%) | -62.924 [-62.924, -62.924] | -62.924 [-62.924, -62.924] | $-306.44 |
| C52 | 39 | 0 | — | — | $0.00 | 0 | — | — | $0.00 |

## Interpretation

Training is where model selection occurred. The IS numbers are therefore
optimistically biased by construction; they are not an independent estimate
of deployable performance. No correction for that bias is applied here.
