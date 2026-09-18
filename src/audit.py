#!/usr/bin/env python3
"""Structure audit for an unknown tabular dataset.

Run this BEFORE plotting anything. It answers the questions that decide
whether an analysis plan is even possible, and catches the failure modes
that cost us the 2025 hackathon:

  - IDs read as floats, creating phantom entities ("1" vs "1.0")
  - IDs unique only within a group, silently pooling unrelated entities
  - a factor fully nested in another, making a planned comparison impossible
  - rankings built on cells with n = 1
  - predictors measured at or after the outcome (leakage)

Usage
-----
    python src/audit.py data/pheno.csv
    python src/audit.py data/pheno.csv --id LINE --group POP --condition REGIME --outcome YLD
    python src/audit.py data/pheno.csv --sample 200000        # big file, sample rows
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

RULE = "=" * 72
ID_HINTS = ("id", "line", "entity", "sample", "plot", "name", "code", "key")


def h(title: str) -> None:
    print(f"\n{RULE}\n{title}\n{RULE}")


def load(path: str, sample: int | None) -> pd.DataFrame:
    """Read everything as string first so no ID is silently coerced to float."""
    raw = pd.read_csv(path, dtype=str, low_memory=False)
    if sample and len(raw) > sample:
        raw = raw.sample(sample, random_state=0)
        print(f"NOTE: sampled {sample:,} of the file's rows")
    out = raw.copy()
    for c in raw.columns:
        num = pd.to_numeric(raw[c], errors="coerce")
        # treat as numeric only if nearly everything parsed
        if num.notna().sum() >= 0.95 * raw[c].notna().sum() and raw[c].notna().any():
            out[c] = num
    return out, raw


def overview(df: pd.DataFrame, raw: pd.DataFrame) -> None:
    h("1. SHAPE AND TYPES")
    print(f"rows {len(df):,}   columns {len(df.columns)}")
    info = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
        "missing_%": (df.isna().mean() * 100).round(1),
        "example": [raw[c].dropna().iloc[0] if raw[c].notna().any() else "" for c in df.columns],
    })
    print(info.to_string())


def id_formats(raw: pd.DataFrame, cols: list[str]) -> None:
    h("2. ID FORMAT CONSISTENCY  (mixed formats mean mixed source files)")
    for c in cols:
        s = raw[c].dropna().astype(str).str.strip()
        if s.empty:
            continue
        shapes = s.str.replace(r"\d", "9", regex=True).value_counts()
        print(f"\n{c}: {s.nunique():,} raw values, {len(shapes)} format(s)")
        print(shapes.head(6).to_string())
        norm = s.str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")
        if norm.nunique() < s.nunique():
            print(f"  WARNING: {s.nunique() - norm.nunique():,} values collapse after "
                  f"stripping '.0' and leading zeros.")
            print("  Decide deliberately: same entity written two ways, or different "
                  "entities from different files? Check the data dictionary.")


def uniqueness(df: pd.DataFrame, cols: list[str], group: str | None) -> None:
    h("3. ID UNIQUENESS AND NESTING")
    factors = [c for c in df.columns if df[c].nunique() <= max(50, len(df) // 20)]
    for c in cols:
        print(f"\n{c}: {df[c].nunique():,} distinct values")
        if group and group in df.columns:
            combo = df.groupby(group, observed=True)[c].nunique().sum()
            print(f"  distinct {group}+{c} pairs: {combo:,}")
            if combo > df[c].nunique() * 1.05:
                print(f"  WARNING: {c} is NOT globally unique. It repeats across {group}.")
                print(f"  Use {group} + {c} as the key, or a provided unique-ID column.")
        for f in factors:
            if f == c:
                continue
            counts = df.groupby(c, observed=True)[f].nunique()
            if len(counts) and counts.max() == 1:
                print(f"  NESTED: every {c} has exactly one {f}. "
                      f"Comparisons of {c} across {f} are impossible.")


def coverage(df: pd.DataFrame, id_col: str, cond: str, outcome: str | None) -> None:
    h("4. COVERAGE MATRIX  (a ranking on n=1 cells is noise, not a result)")
    sub = df.dropna(subset=[outcome]) if outcome and outcome in df else df
    cell = sub.groupby([id_col, cond], observed=True).size().unstack(fill_value=0)
    n_cond = cell.shape[1]
    print(f"{cell.shape[0]:,} entities x {n_cond} conditions")
    print("\nplots per entity-condition cell:")
    print(pd.Series(cell.values.ravel()).describe().round(2).to_string())
    flat = cell.values.ravel()
    print(f"\ncells with n = 0: {(flat == 0).mean():.0%}"
          f"   n = 1: {(flat == 1).mean():.0%}   n < 5: {(flat < 5).mean():.0%}")
    for k in (2, 5, 10):
        ok = ((cell >= k).sum(axis=1) == n_cond).sum()
        print(f"entities with n >= {k} in ALL conditions: {ok:,}")
    print("\nUse the n>=5 set for any ranking. Shrink or model the rest.")


def leakage(df: pd.DataFrame, outcome: str) -> None:
    h("5. LEAKAGE WATCHLIST")
    print("Any variable measured at or after the outcome must stay out of the features.")
    print("Typical offenders: moisture or quality measured at harvest, post-hoc grades,")
    print("anything derived from the outcome, any row-order or index column.\n")
    num = df.select_dtypes("number")
    if outcome in num:
        corr = num.corr(numeric_only=True)[outcome].drop(outcome).abs().sort_values(ascending=False)
        print(f"strongest absolute correlations with {outcome} (inspect the top ones by hand):")
        print(corr.head(10).round(3).to_string())
    idx_like = [c for c in df.columns if c.lower().startswith("unnamed") or c.lower() in ("index", "id")]
    if idx_like:
        print(f"\nindex-like columns to drop before modeling: {idx_like}")


def variance(df: pd.DataFrame, outcome: str, cond: str | None, group: str | None, id_col: str | None) -> None:
    h("6. WHERE THE VARIANCE LIVES  (rough group means, an upper bound per layer)")
    y = df.dropna(subset=[outcome]).copy()
    if y.empty:
        print("no rows with the outcome")
        return
    total = y[outcome].var()
    print(f"total variance of {outcome}: {total:,.2f}")
    for name, col in (("condition", cond), ("group", group), ("entity", id_col)):
        if not col or col not in y:
            continue
        centered = y[outcome] - y.groupby(col, observed=True)[outcome].transform("mean")
        share = 1 - centered.var() / total
        print(f"  {name:9s} ({col}): explains about {share:6.1%} on its own")
    print("\nIf one layer dominates, center within it before comparing entities.")


def main() -> int:
    p = argparse.ArgumentParser(description="Structure audit for an unknown dataset")
    p.add_argument("path")
    p.add_argument("--id", dest="id_col", help="entity ID column (line, plot, field, animal)")
    p.add_argument("--group", help="grouping factor IDs may be nested in (population, site, project)")
    p.add_argument("--condition", help="condition / regime / environment column")
    p.add_argument("--outcome", help="outcome column (yield, score)")
    p.add_argument("--sample", type=int, help="sample N rows for speed")
    a = p.parse_args()

    df, raw = load(a.path, a.sample)
    overview(df, raw)

    id_cols = [c for c in df.columns if any(k in c.lower() for k in ID_HINTS)]
    if a.id_col and a.id_col not in id_cols:
        id_cols.insert(0, a.id_col)
    id_cols = id_cols[:8]
    if id_cols:
        id_formats(raw, id_cols)
        uniqueness(df, id_cols, a.group)
    else:
        print("\nNo ID-like columns found by name. Pass --id explicitly.")

    if a.id_col and a.condition:
        coverage(df, a.id_col, a.condition, a.outcome)
    if a.outcome:
        leakage(df, a.outcome)
        variance(df, a.outcome, a.condition, a.group, a.id_col)

    h("NEXT")
    print("Write the traps you found into deck/OUTLINE.md slide 3 while they are fresh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
