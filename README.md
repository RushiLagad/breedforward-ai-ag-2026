# BreedForward 2026

AI in AG Hackathon, University of Arkansas. Team: Sambhavi Patel, Rushikesh Lagad,
Renuka Khanal, Ajaydeep Bedi.

> Grounded in data. Breeding for the future.

![BreedForward workflow](deck/workflow.png)

*Bayer scenario: January 2008, plots cut. Predict which of the 15,968 lines about to be planted should advance (15,959 have a scorable 2008 yield), from genotypes and 2001 to 2007 testcross data. Validate on the real 2008 season. Data Friday, model Saturday, decision and demo Sunday.*

**Nothing from the hackathon dataset gets committed.** `data/` is gitignored and so are
`*.csv`, `*.parquet` and `*.xlsx`. The organizers marked last year's materials confidential.

## Setup

```bash
git clone https://github.com/RushiLagad/breedforward-ai-ag-2026.git
cd breedforward-ai-ag-2026
pip install -r requirements.txt
```

Then copy the dataset files into `data/` and unzip `ImputedC1Populations.zip` and `ImputedC2Populations.zip`
there (so `data/ImputedPopulationsC1/` and `data/ImputedPopulationsC2/` exist). Nothing under `data/` or
`results/` is ever committed.

## Working rule

Everyone pushes to `main`, small commits, no long-lived branches. If two people must touch one file, say so
in the channel first. Any number that goes in the deck is reproduced by a second person from this repo.
Reproduced on a second machine (Windows, miniforge) on Sep 19: every stage, every number identical.

## Layout

```
src/audit.py          structure audit for an unknown dataset   <- run this first
src/build.py          clean build of both groups + environment -> results/pheno_env_ready.pkl
src/gxe_test.py       between-regime vs split-half correlation (the honest G x E test)
src/predict2008.py    first pass at the scenario: train 2000-2007, predict 2008 (superseded by predict_multitrait)
src/predict_multitrait.py  tuned ridge, 2007 + 2008 hold-outs, six traits -> results_summary/stage2_results.csv
src/predict_siblings.py    half of each 2008 pop phenotyped, predict the rest; breeder's equation; advancement list
src/predict_two_stage.py   sibling mean + within-population marker model (Mendelian sampling term)
deck/workflow.png     the team schematic (deck/workflow.dot is the source)
src/weight_sensitivity.py  how the advancement list moves with index weights -> results_summary/stage5_weight_sensitivity.csv
src/figures_results.py     the five deck figures, from results_summary/ only  -> figures/fig_*.png
src/style.py               one visual system for every plot
src/legacy/                pre-scenario scripts (generic ranking, demo data, last year's build); not used
dashboard/app.py           Streamlit demo, reads results/advance2008.csv, never fits a model
deck/OUTLINE.md            the 10 slides and who owns each
deck/workflow.html         hypotheses, Mermaid pipeline, demo spec
docs/                      challenge brief, decision log, pitch outline
data/, results/            gitignored (dataset and derived tables)
```

## Pipeline

```
copy the dataset files into data/ and unzip ImputedC1Populations.zip and ImputedC2Populations.zip there
python src/build.py            # ~2 min, writes results/pheno_env_ready.pkl and results/env_ready.csv
python src/gxe_test.py         # ~3 min
python src/predict_multitrait.py   # ~9 min first run (builds the genotype cache), ~2 min after
python src/predict_siblings.py     # ~1 min, writes results/advance2008.csv
python src/predict_two_stage.py    # seconds
python src/sampling_curve.py       # ~1 min
python src/weight_sensitivity.py   # seconds
python src/figures_results.py      # the five deck figures
streamlit run dashboard/app.py
```

## The scenario (from "Hackathon Scenario And Help.docx")

January 2008, plots cut. Predict 2008 performance of known, genotyped lines (crossed to testers,
about to be planted at known locations) from 2001-2007 data, and decide which lines advance.
Choose broad-acre (average across environments) or environment-specific prediction and justify it.
Focus on GCA; SCA is out of scope by the organizers' own statement.

## 2008 hold-out result (Sep 18, src/predict2008.py)

Train 2000-2007 (138k lines), predict all 15,959 lines tested in 2008, score against their real 2008 yields.

| Predictor | r with 2008 line means | Gain if top 20% advance |
|---|---|---|
| Population mean from earlier years | ~0 (most 2008 pops are new) | +0.04 bu/ac |
| Parent GCA from earlier years | 0.11 | +1.30 bu/ac |
| Markers, ridge on 2,911 SNPs | 0.14 | +1.48 bu/ac |
| Markers + parent GCA | **0.15** | **+1.76 bu/ac** |
| Perfect foresight | | +12.69 bu/ac |

2008 line means have reliability 0.46 (4.8 plots/line), so the ceiling is r ~ 0.68 and accuracy vs
true genetic value is ~0.22. This is CV00 (new lines, new year, 71% of populations with no parent
seen before); literature reports near zero for this scheme. Broad-acre is the right target because
lines do not re-rank across environments (see G x E test below).

Two traps found here: the C2 phenotype file stores LINE as `12.0` and LINE_UNIQUE_ID as `C2.1.12.0`,
so strip the `.0` before matching genotypes; and 3.9% of rows have no tester ID.

## Stage 2: tuned model, two validation years, six traits (src/predict_multitrait.py)

| Hold-out year | r markers, yield | top-20% gain | ceiling r | pops with both parents seen before |
|---|---|---|---|---|
| 2007 (train 2000-2006) | 0.07 | +0.5 of +12.5 bu/ac | 0.63 | 15% |
| 2008 (train 2000-2007) | 0.14 | +1.9 of +12.7 bu/ac | 0.68 | 29% |

Accuracy for a new year is set by how connected the new populations are to the past, not by the model.
Traits (2008, markers): TWT 0.23, MST 0.18, YLD 0.14, ERM 0.14, STLP 0.05, RTLP ~0. Lodging is not
predictable here; carry it as an observed penalty, not a prediction. Heavy shrinkage (h2 ~ 0.1) won tuning.

## Stage 3: the plots you have beat the markers (src/predict_siblings.py, src/predict_two_stage.py)

Scenario says "phenotypes of some related lines" are available. Simulated: half of each 2008 population
phenotyped, predict the other half. Yield, top-20% advancement, gain possible +12.6 bu/ac:

| What you know about a 2008 line | r | gain captured |
|---|---|---|
| genotype only (pure new year) | 0.13 | +1.7 |
| genotype, siblings pooled into training | 0.24 | +3.0 |
| mean of phenotyped siblings, no markers | **0.36** | **+4.7** |
| sibling mean + within-pop marker model | 0.35 | +4.3 |

Markers add on top of the sibling mean for MST (0.58 -> 0.62) and TWT (0.48 -> 0.52), not for yield.
Decision: in a plot-cut year, sample every population rather than grow every line; predict the rest
from family mean plus markers; markers alone only for populations with zero plots.

Breeder's equation, top 20% advanced, true genetic sd ~6.3 bu/ac: r=0.14 -> +1.2, r=0.35 -> +3.1,
r=0.50 -> +4.4 bu/ac. 2008 as run = 77,353 plots; sampling half saves ~39,000 plots and keeps ~70% of gain.

`results/advance2008.csv` (not committed): 8,014 lines, 1,602 flagged, index = 0.5 yield + 0.1 TWT
- 0.15 MST - 0.05 ERM - 0.2 observed family lodging. Realised 2008 yield gain of the flagged set +2.6 bu/ac.

## Stage 4: the sampling curve (src/sampling_curve.py, figures/fig_sampling_curve.png)

Phenotype a random fraction f of every 2008 family, predict the rest from the family mean (with or
without within-family markers), score against real 2008 yield. Mean of 3 draws, top-20% advancement:

| share of each family phenotyped | plots | r (family mean) | gain bu/ac |
|---|---|---|---|
| 0% (genotype only) | 0 | 0.13 | +1.7 |
| 10% | 7.7k | 0.30 | +3.9 |
| 20% | 15k | 0.33 | +4.1 |
| 50% | 38k | 0.35 | +4.6 |
| 75% | 57k | 0.37 | +4.8 |
| perfect foresight | | | +12.7 |

The curve saturates almost immediately: 10% of each family recovers about 80% of what 75% recovers,
at one seventh of the plots. Markers on top of the family mean add r 0.37 -> 0.40 only at high sampling.
This is the answer to the scenario's resource question: with a plot cut, sample every family thinly,
never drop families, and use markers for the moisture and test-weight calls.

## Stage 5: index-weight sensitivity (src/weight_sensitivity.py)

The advancement index is 0.5 yield + 0.1 TWT - 0.15 MST - 0.05 ERM - 0.2 family lodging (z-scores).
Realised 2008 outcomes of the flagged top 20% under different weightings:

| weighting | yield gain bu/ac | moisture (z) | family lodging (z) | overlap with default set |
|---|---|---|---|---|
| yield only | +2.96 | +0.24 (wetter) | -0.69 | 69% |
| default | +2.64 | -0.02 | -1.75 | 100% |
| yield-heavy | +3.02 | +0.14 | -1.17 | 80% |
| moisture-heavy (-0.35) | +1.81 | -0.24 | -1.50 | 78% |
| lodging-heavy (-0.40) | +2.92 | 0.00 | -2.21 | 88% |
| equal weights | -0.39 | -0.39 | -1.41 | 45% |

500 random weightings within plausible ranges: overlap with the default set median 85% (5th-95th 68-94%),
realised yield gain median +2.62 bu/ac (5th-95th +1.47 to +3.20). Reading: the default trades ~0.3 bu/ac of
yield for drier grain and much lower lodging risk; the flagged set is stable to any sensible weighting;
equal weights are the one choice that breaks it. The weights are the breeder's lever and the demo exposes them.

## What we already know (Sep 18 runs)

- 1,019,864 plots, 154,551 lines, 998 populations, 1,185 environments after the merge. 52k C2 rows have no environment row and drop.
- Every line is tested in exactly one year. LINE is unique only within a population; use LINE_UNIQUE_ID.
- Line-mean heritability of yield is 0.48 at ~7 plots. GCA ranking is meaningful.
- Lines do NOT re-rank across stress regimes: between-regime r 0.23 vs within-regime split-half 0.18-0.25. Same at parent level. Regime explains 1% of environment mean yield. This is the honest-test slide.
- Within-population genomic prediction, ridge, CV1: r 0.21 yield, 0.35-0.39 moisture on 24 populations. Literature gets 0.4-0.6 with GBLUP.
- Samuel's CORN_BREEDING_DATA_GUIDE.md column names do not match the files (YEAR_x, X04_PRCP, clay_0_5cm, no TMAX/TMIN). src/build.py uses the real names.

## Lanes

| Person | Lane |
|---|---|
| Sambhavi Patel | Data: build, QC, traps, reproduction |
| Rushikesh Lagad | Modeling: prediction, validation, sampling curve, index |
| Renuka Khanal | Visualization: figures, dashboard, demo |
| Ajaydeep Bedi | Story: deck, narrative, rehearsal clock |

Any result that goes in the deck is read by a second person first.

## How we talk about it

The framing is ours, the mathematics is established, and we chose established mathematics
because a weekend is not long enough to validate a new estimator. Benchmark any score we
define against Finlay-Wilkinson slopes and WAASBY (`metan` in R) and say where they agree.
