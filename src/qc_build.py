"""Confirm the clean-build row counts and the ID / join traps.

Run after `python src/build.py`:

    python src/qc_build.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path("data")
READY = Path("results/pheno_env_ready.pkl")
COLS = [
    "shorthand_x",
    "YEAR_x",
    "LOC",
    "LINE_UNIQUE_ID",
    "LINE",
    "GERMPLASM_ID_TESTER",
    "CLUSTER",
    "YLD_BE",
]


def load_pheno(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        usecols=COLS,
        low_memory=False,
        dtype={"LINE_UNIQUE_ID": str, "LINE": str, "GERMPLASM_ID_TESTER": str},
    )


def missing_tester(s: pd.Series) -> pd.Series:
    text = s.fillna("").astype(str).str.strip()
    return s.isna() | text.isin(["", "nan"])


def main() -> None:
    if not READY.exists():
        raise SystemExit("results/pheno_env_ready.pkl is missing. Run python src/build.py first.")

    c1 = load_pheno(DATA / "C1_Phenotype_Data_V2.csv")
    c2 = load_pheno(DATA / "C2_Phenotype_Data_V2.csv")
    env = pd.read_csv(DATA / "environmental_features.csv", encoding="utf-8-sig")
    ready = pd.read_pickle(READY)

    raw_n = len(c1) + len(c2)
    print("RAW")
    print(f"  C1 {len(c1):,}  C2 {len(c2):,}  both {raw_n:,}")
    print(f"  env year x loc {len(env):,}  duplicate keys {int(env.duplicated(['YEAR', 'LOC']).sum())}")

    print("\nTRAP 1  C2 IDs look like floats")
    print(f"  C1 LINE ends .0: {c1['LINE'].str.endswith('.0').mean():.1%}  example {c1['LINE'].iloc[0]!r} / {c1['LINE_UNIQUE_ID'].iloc[0]!r}")
    print(f"  C2 LINE ends .0: {c2['LINE'].str.endswith('.0').mean():.1%}  example {c2['LINE'].iloc[0]!r} / {c2['LINE_UNIQUE_ID'].iloc[0]!r}")
    ph = pd.concat([c1, c2], ignore_index=True)
    line_pops = ph.groupby("LINE")["shorthand_x"].nunique()
    print(f"  LINE is unique in {ph['LINE'].nunique():,} strings, reused across {int((line_pops > 1).sum()):,} populations")
    print(f"  LINE_UNIQUE_ID unique globally: {ph['LINE_UNIQUE_ID'].nunique():,}")

    print("\nTRAP 2  environment inner join drops C2 plots")
    env_keys = set(zip(pd.to_numeric(env["YEAR"]), env["LOC"].astype(str).str.strip()))
    for name, d in [("C1", c1), ("C2", c2)]:
        year = pd.to_numeric(d["YEAR_x"])
        keys = zip(year, d["LOC"].astype(str).str.strip())
        miss = sum(key not in env_keys for key in keys)
        print(f"  {name} plots with no env row: {miss:,} ({miss / len(d):.1%})")
    print(f"  build kept {len(ready):,} of {raw_n:,} ({len(ready) / raw_n:.1%})")
    print(f"  ready C1 {(ready.HG == 1).sum():,}  C2 {(ready.HG == 2).sum():,}")

    print("\nTRAP 3  missing tester IDs")
    both_na = missing_tester(ph["GERMPLASM_ID_TESTER"])
    print(f"  C1 {missing_tester(c1['GERMPLASM_ID_TESTER']).mean():.2%}")
    print(f"  C2 {missing_tester(c2['GERMPLASM_ID_TESTER']).mean():.2%}")
    print(f"  both {both_na.mean():.2%}")

    print("\nREADY TABLE")
    print(f"  rows {len(ready):,}  lines {ready.LINE_ID.nunique():,}  pops {ready.POP.nunique():,}  envs {ready.ENV.nunique():,}")
    years_per_line = ready.groupby("LINE_ID").YEAR.nunique()
    print(f"  years per line: {years_per_line.value_counts().to_dict()}")
    n_2008 = int((ready.YEAR == 2008).sum())
    lines_2008 = ready.loc[ready.YEAR == 2008, "LINE_ID"].nunique()
    print(f"  2008 already in the table: {n_2008:,} plots, {lines_2008:,} lines — hold this year out")

    y08 = ph[pd.to_numeric(ph["YEAR_x"]) == 2008].copy()
    y08["YLD"] = pd.to_numeric(y08["YLD_BE"], errors="coerce")
    y08["has_env"] = [
        (year, loc) in env_keys
        for year, loc in zip(pd.to_numeric(y08["YEAR_x"]), y08["LOC"].astype(str).str.strip())
    ]
    candidate = set(y08["LINE_UNIQUE_ID"])
    no_yield = set(y08.groupby("LINE_UNIQUE_ID")["YLD"].apply(lambda s: s.notna().sum()).loc[lambda s: s == 0].index)
    yield_rows = y08[y08["YLD"].notna()]
    env_on_yield = yield_rows.groupby("LINE_UNIQUE_ID")["has_env"].sum()
    weather_only = set(env_on_yield[env_on_yield == 0].index)
    evaluation = candidate - no_yield - weather_only
    print("\n2008 CANDIDATE vs EVALUATION")
    print(f"  candidate (every 2008 line, all get a prediction): {len(candidate):,}")
    print(f"  no recorded yield: {len(no_yield)}  {sorted(no_yield)}")
    print(f"  yield only at sites with no weather: {len(weather_only)}  {sorted(weather_only)}")
    print(f"  evaluation (can score against 2008 yield): {len(evaluation):,}")
    print("  predict all candidates; score only the evaluation set")


if __name__ == "__main__":
    main()
