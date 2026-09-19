<p align="center">
  <img src="assets/breedforward-logo-white.png" alt="BreedForward" width="340">
</p>

<p align="center">
  AI in AG Hackathon with Bayer, University of Arkansas, September 18 to 20, 2026<br>
  Sambhavi Patel, Rushikesh Lagad, Renuka Khanal, Ajaydeep Bedi
</p>

---

## The problem

January 2008 at a maize breeding program. The field budget has been cut and there are not enough plots to
grow every candidate. 15,968 new inbred lines from 998 biparental families are genotyped and ready to be
crossed to testers and planted. Behind them sit seven years of testcross data (2001 to 2007, about a million
plots across 1,185 year by location environments) and one shared 2,911-SNP panel.

Before a single 2008 plot goes in the ground, the breeder must decide which lines advance. Bayer's question
to us: with fewer plots, how should the program spend the ones it has, and how should it rank the lines it
cannot afford to test?

## Our hypothesis

Stated so that it could be wrong:

> In a new year with mostly new families, the genotype alone says little about a line's yield. Most of what
> can be known about a line lives in its family. A program facing a plot cut should therefore phenotype a
> small sample of every family instead of every line of a few families, predict the untested siblings from
> the family mean, and use markers only where they add on top of that.

If markers had predicted new-year yield well, or if lines had re-ranked across environments, this plan would
have been wrong. We tested both.

## What we found

Everything is scored against the real 2008 season, which no model saw. Full tables, baselines, ceilings
and the limits are in [docs/results.md](docs/results.md).

| Claim | Evidence |
|---|---|
| Genotype alone predicts a new year weakly | Ridge on 2,911 SNPs trained on 2000 to 2007: r 0.14 with 2008 line means, +1.9 bu/ac if the top 20% advance, against +12.7 with perfect foresight. The same scheme on 2007 gives r 0.07. Accuracy tracks how many new families have a parent seen before (29% in 2008, 15% in 2007), not the model. |
| The plots you have beat the markers | Phenotype half of every 2008 family and predict the rest from the family mean: r 0.36, +4.7 bu/ac. Markers on top add nothing for yield, but lift moisture (0.58 to 0.62) and test weight (0.48 to 0.52). |
| The sampling curve saturates almost at once | 10% of each family phenotyped, 7.7k plots: r 0.30, +3.9 bu/ac. 75%, 57k plots: r 0.37, +4.8. One seventh of the plots buys about 80% of the gain. |
| Broad-acre is the right target | Lines do not re-rank across stress regimes: between-regime r 0.23 against within-regime split-half 0.18 to 0.25, same pattern at parent level. Regime explains 1% of environment mean yield. |
| The advancement index is stable | 500 random weightings of a five-trait index keep a median 87% overlap with the default advancement set, which realises +3.9 bu/ac. Equal weights are the one choice that breaks it: two thirds of the gain is gone. |

<p align="center">
  <img src="figures/fig_sampling_curve.png" alt="Share of each family phenotyped against realised 2008 gain" width="720">
</p>

**Recommendation.** In a plot-cut year: sample every family thinly and never drop a family; predict the
untested siblings from the family mean plus markers; use markers alone only for families with zero plots;
predict broad-acre, not environment-specific; advance on a yield-led index that also carries moisture, test
weight, maturity and observed family lodging.

## Architecture

<p align="center">
  <img src="deck/workflow.png" alt="BreedForward workflow" width="860">
</p>

| Stage | Script | What it does |
|---|---|---|
| Build | `src/build.py` | Both heterotic groups plus environment covariates into one plot table; stress regimes from flowering-window weather |
| G x E test | `src/gxe_test.py` | Between-regime against split-half correlation, at line and parent level |
| Genotype-only prediction | `src/predict_multitrait.py` | Ridge on markers (GBLUP-equivalent), 2007 and 2008 hold-outs, six traits, tuned on 2007 only |
| Sibling-informed prediction | `src/predict_siblings.py`, `src/predict_two_stage.py` | Half of each 2008 family known: family mean, markers plus siblings, within-family marker model, breeder's equation; the advancement list is built on family mean plus within-family markers |
| Sampling curve | `src/sampling_curve.py` | Fraction of each family phenotyped against realised gain |
| Index sensitivity | `src/weight_sensitivity.py` | Named and 500 random weightings of the advancement index |
| Figures | `src/figures_results.py` | The five deck figures, from `results_summary/` only |
| Demo | `dashboard/app.py`, `dashboard/build_demo_html.py` | Move the index weights and the plot budget, see the advancement list and its realised 2008 gain. Streamlit for development; the single-file HTML build (`results/breedforward_demo.html`, not committed) is what runs in the room: no server, no network, opens in any browser |

Why these choices: yield is centred within environment by tester, so the models predict general combining
ability and tester-specific effects never enter (SCA is out of scope by the organizers' statement). Shrinkage
is tuned on 2007 and fixed before 2008 is touched. Every accuracy carries two baselines (population mean,
parent GCA) and a ceiling (the reliability of the 2008 line means, about 0.68). The mathematics is
established on purpose: a weekend is long enough to ask a sharp question of a large dataset, not to validate
a new estimator.

## Reproduce it

```bash
git clone https://github.com/RushiLagad/breedforward-ai-ag-2026.git
cd breedforward-ai-ag-2026
pip install -r requirements.txt
```

Copy the dataset files into `data/` and unzip `ImputedC1Populations.zip` and `ImputedC2Populations.zip`
there, so `data/ImputedPopulationsC1/` and `data/ImputedPopulationsC2/` exist. Then, in order:

```
python src/build.py                # ~2 min
python src/gxe_test.py             # ~3 min
python src/predict_multitrait.py   # ~9 min first run (builds the genotype cache), ~2 min after
python src/predict_siblings.py     # ~1 min, writes results/advance2008.csv
python src/predict_two_stage.py    # seconds
python src/sampling_curve.py       # ~1 min
python src/weight_sensitivity.py   # seconds
python src/figures_results.py      # the five deck figures
python dashboard/build_demo_html.py  # results/breedforward_demo.html, the offline demo
streamlit run dashboard/app.py       # or the Streamlit view
```

Reproduced end to end on a second machine (Windows, miniforge) on Sep 19 with identical numbers at every stage.

**Nothing from the dataset is committed.** `data/` and `results/` are gitignored, and so are `*.csv`,
`*.parquet` and `*.xlsx`. Only the small summary tables in `results_summary/` and the figures are versioned.

## Layout

```
src/                 the pipeline, one script per stage (src/legacy/ holds pre-scenario scripts, unused)
dashboard/           Streamlit app and the single-file HTML demo builder; both read results/advance2008.csv, neither fits a model
deck/                workflow schematic (png + dot source), slide outline
docs/                results.md, challenge brief, decision log, pitch outline, branding
figures/             the five deck figures
results_summary/     the small tables behind every number above
assets/              team logo
data/, results/      gitignored
```

## Team

| Person | Lane |
|---|---|
| Sambhavi Patel | Data: build, QC, traps, reproduction |
| Rushikesh Lagad | Modeling: prediction, validation, sampling curve, index |
| Renuka Khanal | Visualization: figures, dashboard, demo |
| Ajaydeep Bedi | Story: deck, narrative, rehearsal clock |

Everyone pushes to `main`, small commits, no long-lived branches. Any number that goes in the deck is
reproduced by a second person from this repo. Decisions and their reasons are in `docs/decision-log.md`.

## Data and acknowledgements

The dataset is Bayer Crop Science's legacy maize testcross data (Lian, Jacobson, Zhong and Bernardo, 2014,
*Crop Science* 54:1514), provided in simplified form by the AI in AG Hackathon organizers at the University
of Arkansas (Samuel B. Fernandes) for this event. The organizers marked the materials confidential; this
repository contains code, summary statistics and figures only. Thanks to Bayer and the organizing team for
the data and the scenario.
