# Results, stage by stage

Every number here is in `results_summary/` and was reproduced on a second machine (Windows, miniforge,
Sep 19) to within rounding; where a value differs in the third decimal between machines the Windows
value is the committed one. Scores are always against the real 2008 season, which no model saw.
Input files are identified by SHA-256 in `results_summary/input_checksums.csv`.

## The timeline, stated precisely

The scenario has two decisions, not one, and they happen at different times.

| When | Decision | What is known | Stage |
|---|---|---|---|
| January 2008 | How to spend the cut plot budget | 2001 to 2007 phenotypes, all genotypes, pedigrees | 2 (genotype-only), 4 (the sampling curve is the answer) |
| After the sampled plots are harvested | Which untested siblings advance | the above, plus the phenotypes of the siblings that were planted | 3, 5 |

The genotype-only stage is a January decision. The sibling stages are not: they assume a share of every
family was planted and harvested, and they rank the siblings that were never planted. The only thing the
models never see is the real 2008 yield of those untested lines, which exists in the data because in
reality every line was grown; it is used purely to score the decision.

## Reading the numbers: two evaluation sets

| Set | Lines | Used by | Genotype-only yield |
|---|---|---|---|
| All 2008 lines with a scorable yield | 15,959 | stage 2 | r 0.14, top-20% gain +1.9 of +12.7 bu/ac |
| Untested half of every 2008 family (stratified split) | 7,972 | stages 3, 5 | r 0.13, top-20% gain +1.9 of +12.9 bu/ac |

The split is stratified by family: every family with two or more lines contributes at least one
phenotyped and at least one untested line (`src/common.py`). Cell means for the environment × tester
centering are computed from training plots only (all pre-2008 plots plus the phenotyped 2008 lines) and
applied to every plot, so untested outcomes cannot leak into the target definition. Ties in every ranking
break on LINE_ID.

## Stage 1: the data, and the traps in it

- 1,019,864 plots, 154,551 lines, 998 families, 1,185 environments after the merge. 52k C2 rows have no
  environment row and drop.
- Every line is tested in exactly one year. LINE is unique only within a family; key on LINE_UNIQUE_ID.
- The C2 phenotype file stores LINE as `12.0` and LINE_UNIQUE_ID as `C2.1.12.0`; strip the `.0` before
  matching genotypes, then the leading zeros. Missing this silently drops every C2 genotype.
- 3.9% of plots have no tester ID.
- 15,968 lines in the raw 2008 files, 15,967 after the environment join, 15,959 with a scorable 2008 yield.
- Line-mean heritability of yield is 0.48 at about 7 plots per line. Plot-level h2 about 0.10.
- The data guide's column names do not match the files (YEAR_x, X04_PRCP, clay_0_5cm, no TMAX/TMIN).
  `src/build.py` uses the real names.

## G x E, tested rather than assumed (src/gxe_test.py)

Stress regimes from flowering-window weather: z(July + August precipitation) minus z(July + August cooling
degree days), tertiles over unique environments. Yield centred within environment by family.

| Level | Between HotDry and CoolWet | Split-half within one regime |
|---|---|---|
| Lines | r 0.23 | 0.18 to 0.25 |
| Parents with 30 or more environments | r 0.50 | 0.45 to 0.64 |

If lines re-ranked across regimes, between would sit well below within. It does not. Regime explains 1% of
environment mean yield. Broad-acre prediction is therefore the target at this resolution.

## Stage 2: genotype-only prediction, two validation years, six traits (src/predict_multitrait.py)

Ridge on 2,911 SNPs (GBLUP-equivalent), yield centred within environment by tester, shrinkage tuned on the
2007 hold-out and then fixed. Evaluated on all lines of the hold-out year. This is the January decision.

| Hold-out year | r markers, yield | top-20% gain | ceiling r | families with both parents seen before |
|---|---|---|---|---|
| 2007 (train 2000 to 2006) | 0.07 | +0.5 of +12.5 bu/ac | 0.63 | 15% |
| 2008 (train 2000 to 2007) | 0.14 | +1.9 of +12.7 bu/ac | 0.68 | 29% |

Baselines on 2008 (src/predict2008.py): population mean from earlier years r ~ 0 (+0.04 bu/ac), parent
GCA r 0.11 (+1.30), markers plus parent GCA r 0.15 (+1.76). Traits, 2008, markers only: TWT 0.23, MST
0.18, YLD 0.14, ERM 0.14, STLP 0.05, RTLP ~0. The ceiling is the reliability of the 2008 line means (0.46
at 4.8 plots per line, so r_max about 0.68). Heavy shrinkage (h2 about 0.1) won the tuning. This is the
CV00 scheme (new lines, new year, 71% of families with no parent seen before), and the year-to-year
difference tracks pedigree connectedness, not the model.

## Stage 3: the plots you have beat the markers (src/predict_siblings.py)

Half of every family planted (7,987 lines, 38,713 of the season's 77,353 plots); the other 7,972 lines
predicted. Yield, top-20% advancement, +12.9 bu/ac possible.

| What you know about an untested 2008 line | r | gain captured |
|---|---|---|
| A. genotype only (pure new year) | 0.13 | +1.9 |
| B. genotype, phenotyped siblings pooled into training | 0.24 | +3.3 |
| C. mean of the phenotyped siblings, no markers | **0.36** | **+4.9** |
| D. sibling mean + within-family marker model | 0.36 | +4.5 |

By trait, sibling mean to two-stage: MST 0.59 to 0.64, TWT 0.50 to 0.54, ERM 0.38 to 0.50, YLD 0.364 to
0.360. The within-family marker model (Mendelian sampling term) is fit per family on deviations from the
sibling mean, families with 30 or more phenotyped lines only; the global marker model is the fallback for a
family with no phenotyped sibling (none in this split).

Breeder's equation, top 20% advanced (i = 1.40), additive sd about 6.45 bu/ac: r 0.14 gives +1.3, r 0.35
gives +3.2, r 0.50 gives +4.5 bu/ac per cycle.

### The advancement list and the one trade-off in it

`results/advance2008.csv` (not committed): 7,972 untested lines, 1,594 flagged under the default index
(0.5 yield + 0.1 TWT − 0.15 MST − 0.05 ERM − 0.2 observed family lodging, on z-scores). Moisture, test
weight and maturity use the two-stage predictor, where markers demonstrably add. For yield the plain sibling
mean is the empirical winner on its own (0.364 vs 0.360, +4.9 vs +4.5), so both were scored on the full
index (`results_summary/stage3_index_choice.csv`):

| yield predictor in the index | realised gain of flagged set | families in flagged set |
|---|---|---|
| sibling mean | +4.15 bu/ac | 52 |
| two-stage (sibling mean + within-family markers) | +4.13 bu/ac | 115 |

The two are tied within 0.02 bu/ac. The sibling mean gives every sibling the same yield prediction, so the
index can only rank families and the flagged set collapses onto 52 of them. Two-stage ranks within families
and keeps 115. Rule applied: two-stage when the index gains are within 0.1 bu/ac, otherwise the higher.
That is a judgment (family coverage and within-family choice over 0.02 bu/ac), and it is written down here
rather than hidden.

## Stage 4: the sampling curve (src/sampling_curve.py, figures/fig_sampling_curve.png)

Phenotype a share of EVERY 2008 family (stratified, at least one line per family), predict the rest from the
family mean, score against real 2008 yield. Plots are the actual plots of the sampled lines. Mean of three
draws, top-20% advancement.

| share of each family phenotyped | plots | r (family mean) | gain bu/ac |
|---|---|---|---|
| 0% (genotype only) | 0 | 0.13 | +1.9 |
| 10% | 7,774 | 0.33 | +4.5 |
| 20% | 15,512 | 0.35 | +4.8 |
| 50% | 38,726 | 0.38 | +4.9 |
| 75% | 58,010 | 0.37 | +4.8 |
| perfect foresight | | | +12.8 |

The curve is flat from 10% on: 7,774 plots realise 92% of what 38,726 plots realise. The earlier version
of this stage sampled lines independently, left small families with no plots and predicted them as zero,
which understated the low end (+3.9 at 10%). The within-family marker term adds r 0.37 to 0.39 only at 75%,
where there are enough phenotyped siblings to fit it. This is the answer to the January question.

## Stage 5: index-weight sensitivity (src/weight_sensitivity.py)

Realised 2008 outcomes of the flagged top 20% of the 7,972 untested lines. Moisture, test weight and
lodging columns are differences of means in z units (divided by the candidate sd).

| weighting | yield gain bu/ac | moisture (z) | family lodging (z) | families | overlap with default set |
|---|---|---|---|---|---|
| yield only | +4.46 | +0.29 (wetter) | −0.35 | 117 | 75% |
| default | +4.13 | −0.18 | −0.53 | 115 | 100% |
| yield-heavy (0.7, others halved) | +4.47 | +0.12 | −0.42 | 120 | 84% |
| moisture-heavy (−0.35) | +3.35 | −0.59 | −0.45 | 110 | 84% |
| lodging-heavy (−0.40) | +3.97 | −0.13 | −0.66 | 110 | 92% |
| no lodging term | +3.84 | −0.25 | −0.21 | 122 | 89% |
| equal weights (0.2 each, signs kept) | +1.56 | −0.78 | −0.49 | 108 | 61% |

500 random weightings within plausible ranges (`results_summary/stage5_random_sweep.csv`): overlap with the
default set median 87% (5th to 95th percentile 76 to 95%), realised gain median +3.91 bu/ac (+2.86 to
+4.47). The default trades about 0.3 bu/ac against yield-only for drier grain and lower lodging exposure.
Equal weights are the one choice that breaks it: maturity and moisture then weigh as much as yield, the
index favours the earliest and driest lines, and 62% of the gain is gone.

## Limits

- One year of validation for the sibling schemes (2008), two for genotype-only (2007, 2008).
- Random stratified splits within families; a breeder would choose which siblings to plant and could do better.
- Ridge treats every SNP the same. No trait-specific architecture, no dominance, no pedigree beyond what the markers carry.
- Lodging traits are near-unpredictable here and enter only as an observed family mean.
- The stress regimes are a two-month weather index in tertiles. "No rank-changing G x E at this resolution" is the claim; "no G x E" is not.
- The realised gains are top-20% comparisons on line means with reliability 0.46; conservative relative to true genetic gain.
- The index weights are a judgment, and so is the two-stage choice for yield; both are recorded with the alternative's outcome.
