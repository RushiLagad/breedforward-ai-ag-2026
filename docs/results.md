# Results, stage by stage

Every number here is in `results_summary/` and was reproduced on a second machine (Windows, miniforge,
Sep 19) with identical output. Scores are always against the real 2008 season, which no model saw.

## Reading the numbers: two evaluation sets

Two sets of 2008 lines appear below, and their numbers differ slightly. Do not mix them.

| Set | Lines | Used by | Genotype-only yield |
|---|---|---|---|
| All 2008 lines with a scorable yield | 15,959 | stage 2 | r 0.14, top-20% gain +1.9 of +12.7 bu/ac |
| Held-out half of every 2008 family | 8,014 | stages 3, 4, 5 | r 0.13, top-20% gain +1.7 of +12.6 bu/ac |

Stages 3 to 5 simulate "phenotypes of some related lines" by declaring a random half of each family known
and scoring only the other half, so their baseline is the same model scored on the smaller set. Stage 3's
50% split (one draw, seed 0) and stage 4's 50% point (mean of three draws) differ by 0.01 in r and
0.1 bu/ac for the same reason. Quote the stage 4 values for the curve and the stage 3 values for the scheme
comparison, and say which.

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
environment mean yield. Broad-acre prediction is therefore the target, and environment-specific
prediction would be fitting noise.

## Stage 2: genotype-only prediction, two validation years, six traits (src/predict_multitrait.py)

Ridge on 2,911 SNPs (GBLUP-equivalent), yield centred within environment by tester, shrinkage tuned on the
2007 hold-out and then fixed. Evaluated on all lines of the hold-out year.

| Hold-out year | r markers, yield | top-20% gain | ceiling r | families with both parents seen before |
|---|---|---|---|---|
| 2007 (train 2000 to 2006) | 0.07 | +0.5 of +12.5 bu/ac | 0.63 | 15% |
| 2008 (train 2000 to 2007) | 0.14 | +1.9 of +12.7 bu/ac | 0.68 | 29% |

Baselines on 2008 (src/predict2008.py): population mean from earlier years r ~ 0 (+0.04 bu/ac, most 2008
families are new), parent GCA r 0.11 (+1.30), markers plus parent GCA r 0.15 (+1.76).

Traits, 2008, markers only: TWT 0.23, MST 0.18, YLD 0.14, ERM 0.14, STLP 0.05, RTLP ~0. Lodging is not
predictable from markers here; it is carried as an observed family penalty in the index.

The ceiling is the reliability of the 2008 line means (0.46 at 4.8 plots per line, so r_max about 0.68).
Accuracy against true genetic value is roughly 0.14 / 0.68 = 0.2. Heavy shrinkage (h2 about 0.1) won the
tuning. This is the CV00 scheme (new lines, new year, 71% of families with no parent seen before); the
literature reports near zero for it, and the year-to-year difference tracks pedigree connectedness, not
the model.

## Stage 3: the plots you have beat the markers (src/predict_siblings.py, src/predict_two_stage.py)

Half of each 2008 family declared phenotyped, the other 8,014 lines predicted. Yield, top-20% advancement,
+12.6 bu/ac possible.

| What you know about a 2008 line | r | gain captured |
|---|---|---|
| genotype only (pure new year) | 0.13 | +1.7 |
| genotype, siblings pooled into training | 0.24 | +3.0 |
| mean of phenotyped siblings, no markers | **0.36** | **+4.7** |
| sibling mean + within-family marker model | 0.35 | +4.3 |

Markers add on top of the sibling mean for MST (0.58 to 0.62) and TWT (0.48 to 0.52), not for yield. The
within-family marker model (Mendelian sampling term) is fit per family on deviations from the sibling mean,
families with 30 or more known lines only.

Breeder's equation, top 20% advanced (i = 1.40), additive sd about 6.3 bu/ac: r 0.14 gives +1.2, r 0.35
gives +3.1, r 0.50 gives +4.4 bu/ac per cycle. 2008 as run was 77,353 plots; sampling half saves about
39,000 plots and keeps about 70% of the gain.

`results/advance2008.csv` (not committed): 8,014 lines, 1,602 flagged under the default index. Realised
2008 yield gain of the flagged set +2.6 bu/ac.

## Stage 4: the sampling curve (src/sampling_curve.py, figures/fig_sampling_curve.png)

Phenotype a random fraction of every 2008 family, predict the rest from the family mean, score against
real 2008 yield. Mean of three draws, top-20% advancement.

| share of each family phenotyped | plots | r (family mean) | gain bu/ac |
|---|---|---|---|
| 0% (genotype only) | 0 | 0.13 | +1.7 |
| 10% | 7.7k | 0.30 | +3.9 |
| 20% | 15k | 0.33 | +4.1 |
| 50% | 38k | 0.35 | +4.6 |
| 75% | 57k | 0.37 | +4.8 |
| perfect foresight | | | +12.7 |

The curve saturates almost immediately: 10% of each family recovers about 80% of what 75% recovers, at one
seventh of the plots. Markers on top of the family mean add r 0.37 to 0.40 only at high sampling.

## Stage 5: index-weight sensitivity (src/weight_sensitivity.py)

Index = 0.5 yield + 0.1 TWT - 0.15 MST - 0.05 ERM - 0.2 family lodging, on z-scores. Realised 2008
outcomes of the flagged top 20% of the 8,014 held-out lines.

| weighting | yield gain bu/ac | moisture (z) | family lodging (z) | overlap with default set |
|---|---|---|---|---|
| yield only | +2.96 | +0.24 (wetter) | -0.69 | 69% |
| default | +2.64 | -0.02 | -1.75 | 100% |
| yield-heavy | +3.02 | +0.14 | -1.17 | 80% |
| moisture-heavy (-0.35) | +1.81 | -0.24 | -1.50 | 78% |
| lodging-heavy (-0.40) | +2.92 | 0.00 | -2.21 | 88% |
| equal weights | -0.39 | -0.39 | -1.41 | 45% |

500 random weightings within plausible ranges: overlap with the default set median 85% (5th to 95th
percentile 68 to 94%), realised yield gain median +2.62 bu/ac (+1.47 to +3.20). The default trades about
0.3 bu/ac of yield for drier grain and much lower lodging risk. Equal weights are the one choice that
breaks it: maturity and moisture then weigh as much as yield and the index selects early, dry, low-yielding
lines. The weights are the breeder's lever and the demo exposes them.

## Limits

- One year of validation for the sibling schemes (2008), two for genotype-only (2007, 2008).
- Random half-splits within families; a breeder would choose which siblings to plant, and could do better.
- Ridge on markers treats all SNPs equally; no attempt at a trait-specific architecture.
- Lodging traits are near-unpredictable here and enter the index only as an observed family mean.
- The stress regimes are a coarse two-month weather index; a finer environmental typing could find G x E
  that this test cannot see. The claim is "no rank-changing G x E at this resolution", not "no G x E".
