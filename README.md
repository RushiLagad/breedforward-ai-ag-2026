<p align="center">
  <img src="assets/breedforward-logo-white.png" alt="BreedForward" width="340">
</p>

<p align="center">
  AI in AG Hackathon with Bayer, University of Arkansas, September 18 to 20, 2026<br>
  Sambhavi Patel, Rushikesh Lagad, Renuka Khanal
</p>

---

## The problem

January 2008 at a maize breeding program. The field budget has been cut and there are not enough plots to
grow every candidate. 15,968 new inbred lines from 157 biparental families are genotyped and ready to be
crossed to testers and planted. Behind them sit seven years of testcross data (2001 to 2007, about a million
plots across 1,185 year by location environments) and one shared 2,911-SNP panel.

Two decisions follow, at two different times. In January, before planting: how should the program spend the
plots it still has? After the sampled plots are harvested: which of the lines it never planted should
advance? Bayer's question to us covered both.

## Our hypothesis

Stated so that it could be wrong:

> In a new year with mostly new families, the genotype alone says little about a line's yield. Most of what
> can be known about a line lives in its family. A program facing a plot cut should therefore phenotype a
> small sample of every family instead of every line of a few families, predict the untested siblings from
> the family mean, and use markers only where they add on top of that.

If markers had predicted new-year yield well, or if lines had re-ranked across environments, this plan would
have been wrong. We tested both.

## What we found

Everything is scored against the real 2008 yields of lines the models never saw. The sibling stages assume
half of every family was planted and harvested, then rank the untested half; only the untested lines'
outcomes are hidden. Full tables, baselines, ceilings, the timeline and the limits are in
[docs/results.md](docs/results.md).

| Claim | Evidence |
|---|---|
| Genotype alone predicts a new year weakly | Ridge on 2,911 SNPs trained on 2000 to 2007: r 0.14 with 2008 line means, +1.9 bu/ac if the top 20% advance, against +12.7 with perfect foresight. The same scheme on 2007 gives r 0.07. Accuracy tracks how many new families have a parent seen before (29% in 2008, 15% in 2007), not the model. |
| The plots you have beat the markers | Plant half of every 2008 family and predict the untested half from the family mean: r 0.36, +4.9 bu/ac against +3.3 for a marker model given the same siblings. Markers on top add nothing for yield, but lift moisture (0.59 to 0.64) and test weight (0.50 to 0.54). |
| The sampling curve is flat from 10% on | 10% of every family phenotyped, 7,774 plots: r 0.33, +4.5 bu/ac. 50%, 38,726 plots: +4.9. A fifth of the plots buys 92% of the gain. Every family sampled, none dropped. |
| Broad-acre is the right target | Lines do not re-rank across stress regimes: between-regime r 0.23 against within-regime split-half 0.18 to 0.25, same pattern at parent level. Regime explains 1% of environment mean yield. |
| The advancement index is stable | 500 random weightings of a five-trait index keep a median 87% overlap with the default advancement set, which realises +4.1 bu/ac. Equal weights are the one choice that breaks it: 62% of the gain is gone. |

<p align="center">
  <img src="figures/fig_sampling_curve.png" alt="Share of each family phenotyped against realised 2008 gain" width="720">
</p>

**Recommendation.** In January: sample every family thinly and never drop a family. After harvest: predict
the untested siblings from the family mean, with within-family markers for moisture, test weight and
within-family ranking; use markers alone only for families with zero plots; predict broad-acre, not
environment-specific; advance on a yield-led index that also carries moisture, test weight, maturity and
observed family lodging.

## Architecture

<p align="center">
  <img src="deck/workflow.png" alt="BreedForward workflow" width="860">
</p>

| Stage | Script | What it does |
|---|---|---|
| Build | `src/build.py` | Both heterotic groups plus environment covariates into one plot table; stress regimes from flowering-window weather |
| G x E test | `src/gxe_test.py` | Between-regime against split-half correlation, at line and parent level |
| Genotype-only prediction | `src/predict_multitrait.py` | Ridge on markers (GBLUP-equivalent), 2007 and 2008 hold-outs, six traits, tuned on 2007 only |
| Sibling-informed prediction | `src/predict_siblings.py` (+ `src/common.py`) | Stratified half of every 2008 family known, training-only centering: family mean, markers plus siblings, within-family marker model, breeder's equation; the advancement list, with both yield predictors scored and the choice recorded |
| Sampling curve | `src/sampling_curve.py` | Share of every family phenotyped (stratified) against realised gain, actual plots counted |
| Index sensitivity | `src/weight_sensitivity.py` | Named and 500 random weightings of the advancement index |
| Figures | `src/figures_results.py` | The five deck figures, from `results_summary/` only |
| Demo | `dashboard/app.py`, `dashboard/build_demo_html.py` | Move the index weights and the plot budget, see the advancement list and its realised 2008 gain. Streamlit for development; the single-file HTML build (`results/breedforward_demo.html`, not committed) is what runs in the room: no server, no network, opens in any browser |

Why these choices: yield is centred within environment by tester, using training plots only, so the models
predict general combining ability, tester-specific effects never enter (SCA is out of scope by the
organizers' statement), and untested outcomes cannot leak into the target. Shrinkage is tuned on 2007 and
fixed before 2008 is touched. Every accuracy carries two baselines (population mean,
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
python src/predict_siblings.py     # ~2 min, writes results/advance2008.csv
python src/sampling_curve.py       # ~1.5 min
python src/weight_sensitivity.py   # seconds
python src/figures_results.py      # the five deck figures
python dashboard/build_demo_html.py  # results/breedforward_demo.html, the offline demo
streamlit run dashboard/app.py       # or the Streamlit view
```

Reproduced end to end on a second machine (Windows, miniforge) on Sep 19 to within rounding (one stage 5 cell
differed in the third decimal). `requirements-lock.txt` pins the reference versions, `python src/checksums.py`
records the input files' SHA-256 so two runs can prove they saw the same data, every ranking breaks ties on
LINE_ID, and `pytest` plus GitHub Actions check the committed summaries on every push.

**Nothing from the dataset is committed.** `data/` and `results/` are gitignored, and so are `*.csv`,
`*.parquet` and `*.xlsx`. Only the small summary tables in `results_summary/` and the figures are versioned.

## Layout

```
src/                 the pipeline, one script per stage; common.py holds the split and centering rules
tests/, .github/     sanity tests on the summaries, run in CI
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
