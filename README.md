# BreedForward 2026

AI in AG Hackathon, University of Arkansas. Team: Sambhavi Patel, Rushikesh Lagad,
Renuka Khanal, Ajaydeep Bedi.

> Grounded in data. Breeding for the future.

![BreedForward workflow](deck/workflow.png)

*Bayer scenario: January 2008, plots cut. Predict which of the 15,959 lines about to be planted should advance, from genotypes and 2001 to 2007 testcross data. Validate on the real 2008 season. Data Friday, model Saturday, decision and demo Sunday.*

**Nothing from the hackathon dataset gets committed.** `data/` is gitignored and so are
`*.csv`, `*.parquet` and `*.xlsx`. The organizers marked last year's materials confidential.

## Setup (do this before Saturday, not on Saturday)

```bash
git clone git@github.com:<org>/breedforward-2026.git
cd breedforward-2026
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/rank.py            # smoke test on synthetic data
python src/figures.py         # writes figures/*.png from demo data
streamlit run dashboard/app.py
```

Everyone pushes one test commit before the event so nobody debugs SSH keys at 9am.

## Working rule

Push to `main` often, small commits, no long-lived branches. Branch discipline costs more
than it saves in a 28-hour sprint. If two people must touch one file, say so out loud first.

## Layout

```
src/audit.py          structure audit for an unknown dataset   <- run this first
src/build.py          clean build of both groups + environment -> results/pheno_env_ready.pkl
src/gxe_test.py       between-regime vs split-half correlation (the honest G x E test)
src/gp_within_pop.py  within-population genomic prediction, CV1  -> results/gp_within_pop.csv
src/predict2008.py    THE SCENARIO: train 2000-2007, predict 2008  -> results/pred2008.csv
src/predict_multitrait.py  tuned ridge, 2007 + 2008 hold-outs, six traits -> results_summary/stage2_results.csv
src/predict_siblings.py    half of each 2008 pop phenotyped, predict the rest; breeder's equation; advancement list
src/predict_two_stage.py   sibling mean + within-population marker model (Mendelian sampling term)
deck/workflow.png     the team schematic (deck/workflow.dot is the source)
src/rank.py           shrunken estimates + decision score      -> results/results.csv
src/figures.py        the deck figures                         -> figures/*.png
src/style.py          one visual system for every plot
src/demo.py           synthetic results so everything runs before real data
dashboard/app.py      Streamlit shell, reads results.csv, never fits a model
deck/OUTLINE.md       the 10 slides and who owns each
deck/workflow.html    hypotheses, Mermaid pipeline, demo spec
data/                 gitignored
```

`src/example_2025_corn_build.py` is last year's clean-build script, kept as a worked example
of the merge and QC pattern.

## Pipeline

```
copy the dataset files into data/ and unzip ImputedC1Populations.zip and ImputedC2Populations.zip there
python src/build.py            # ~2 min, writes results/pheno_env_ready.pkl and results/env_ready.csv
python src/gxe_test.py         # ~3 min
python src/gp_within_pop.py    # ~20 min for 50 populations
python src/predict2008.py      # ~7 min, needs ~4 GB RAM; the scenario result
python src/figures.py results/results.csv
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

## What we already know (Sep 18 runs)

- 1,019,864 plots, 154,551 lines, 998 populations, 1,185 environments after the merge. 52k C2 rows have no environment row and drop.
- Every line is tested in exactly one year. LINE is unique only within a population; use LINE_UNIQUE_ID.
- Line-mean heritability of yield is 0.48 at ~7 plots. GCA ranking is meaningful.
- Lines do NOT re-rank across stress regimes: between-regime r 0.23 vs within-regime split-half 0.18-0.25. Same at parent level. Regime explains 1% of environment mean yield. This is the honest-test slide.
- Within-population genomic prediction, ridge, CV1: r 0.21 yield, 0.35-0.39 moisture on 24 populations. Literature gets 0.4-0.6 with GBLUP.
- Samuel's CORN_BREEDING_DATA_GUIDE.md column names do not match the files (YEAR_x, X04_PRCP, clay_0_5cm, no TMAX/TMIN). src/build.py uses the real names.

## Day one: hours 0 to 3

- [ ] Write the organizers' question on the whiteboard, in their words.
- [ ] Write our hypothesis so that it could be proven wrong.
- [ ] `python src/audit.py data/<file>.csv --id <ID> --group <GROUP> --condition <COND> --outcome <Y>`
- [ ] Read every ID as a string. Float coercion invents entities ("1" vs "1.0").
- [ ] Check IDs are globally unique, not just unique within a group.
- [ ] Map nesting. A factor fully nested in another kills the comparison that depends on it.
- [ ] Build the coverage matrix. Cells with n < 5 are noise.
- [ ] List variables measured at or after the outcome. They are banned from the features.
- [ ] Cut class thresholds on unique environments, not on plot rows.
- [ ] Validate every merge with row counts before and after.
- [ ] Write the traps onto deck slide 3 while they are fresh.

## Validation rules, no exceptions

1. The split matches the claim. New season means leave-one-year-out. New entity means a
   group split on entity.
2. Every metric names its split in the same sentence.
3. A baseline sits next to every model: grand mean, condition mean, one classical method.

Last year's lesson, measured on the 2025 corn data: R-squared 0.73 on a random split,
mean -0.27 under leave-one-year-out. Same model, same features.

## Gates

| Clock | Gate |
|---|---|
| Sat 10:00 | Hypothesis everyone can recite |
| Sat 13:00 | Clean table plus written traps list |
| Sat 16:00 | One number that supports or kills the hypothesis. Keep, adjust, or switch |
| Sat 23:00 | Scope freeze. Dashboard runs end to end. No new analysis after this |
| Sun 11:00 | Full deck, no placeholders |
| Sun 12:50 | Submitted |

Standing check-ins at 13:00, 16:00, 23:00, 09:00. Five minutes, standing, what exists and
what is blocked.

## Lanes

| Person | Lane | Never |
|---|---|---|
| | Data engineer: clean build, IDs, QC | slides |
| Rishi | Modeler: baselines, model, validation | chart styling |
| | Visualization: dashboard and every figure, from hour 0 | model tuning |
| | Story: hypothesis wording, deck, rehearsal clock | debugging after hour 12 |

Any result that goes in the deck is read by a second person first.

## How we talk about it

The framing is ours, the mathematics is established, and we chose established mathematics
because a weekend is not long enough to validate a new estimator. Benchmark any score we
define against Finlay-Wilkinson slopes and WAASBY (`metan` in R) and say where they agree.
