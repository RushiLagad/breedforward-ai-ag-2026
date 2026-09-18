# BreedForward 2026

AI in AG Hackathon, University of Arkansas. Team: Sambhavi Patel, Rushikesh Lagad,
Renuka Khanal, Ajaydeep Bedi.

> Grounded in data. Breeding for the future.

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
unzip the dataset into data/   (folder name: "Simplified Hackathon Dataset V3", genotype zips unzipped beside it)
python src/build.py            # ~2 min, writes results/pheno_env_ready.pkl and results/env_ready.csv
python src/gxe_test.py         # ~3 min
python src/gp_within_pop.py    # ~20 min for 50 populations
python src/figures.py results/results.csv
streamlit run dashboard/app.py
```

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
