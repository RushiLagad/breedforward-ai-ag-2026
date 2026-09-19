# Slide 3 — What this data actually is (and two traps in it)

Owner: data/QC. Numbers from `python src/build.py` then `python src/qc_build.py` on 18 Sep.

**Claim title:** `LINE` is not a line, and 52k C2 plots disappear if you join the way the guide says.

## What the data is

Bayer 115-RM inbred screen, 2000–2008. Two heterotic groups (C1, C2). One row is a testcross plot.

After the clean build (`results/pheno_env_ready.pkl`):

| | Count |
| --- | ---: |
| Raw plots | 1,072,276 |
| Plots with weather/soil | 1,019,864 |
| Lines | 154,551 |
| Populations | 998 |
| Year × location environments | 1,185 |
| 2008 candidate set | **15,968** |
| 2008 evaluation set | **15,959** |

Every line is tested in **exactly one year**. 2008 is not a future we invent; it is already here. Train on 2000–2007.

**2008 split (put this on the slide):** the scenario asks which of the lines about to be planted should advance. Markers exist for all of them, so we **predict all 15,968** and **score the 15,959** we can observe.

- Drop 6 lines with no recorded yield: `C1.379.46`, `C1.396.183`, `C1.430.58`, `C2.386.43.0`, `C2.399.26.0`, `C2.408.52.0`
- Drop 3 lines whose only yields are at sites with no weather: `C2.421.11.0` (KSGC), `C2.422.13.0` (KSGC, KSJO), `C2.425.17.0` (INWS)

## Trap 1 — C2 IDs look like Excel floats

C1 IDs are `C1.1.191`. C2 IDs were written as `C2.1.1.0` and `LINE = "1.0"`. **99.6%** of C2 rows end in `.0`.

`LINE` is only unique inside a population (1,903 LINE strings are reused across pops). The join key is `LINE_UNIQUE_ID`. If you match genotypes on the raw C2 line number, the SNP file never attaches.

Fix already in `src/build.py` / `src/predict2008.py`: read IDs as strings, strip the trailing `.0`.

## Trap 2 — the environment file does not cover C2

C1: every plot has a year × location in `environmental_features.csv`.
C2: **52,412 plots (9.8%)** have no env row. An inner join drops them. That is the 1,072,276 → 1,019,864 cut.

Also: **3.84%** of raw plots have no tester ID (C1 5.83%, C2 1.84%). Do not treat tester as complete.

## One-sentence version for the slide

We have 1.02 million testcross plots and 155 thousand lines, but C2 line IDs are stored as `12.0` and one in ten C2 plots has no weather — both will silently break a genotype or environment merge.

## Do not put on this slide

Model *r* values, G×E correlations, or the top-20% gain. Those are slides 4–6.
