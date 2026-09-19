"""Shrunken per-condition estimates and the decision score.

Produces the canonical `results.csv` the dashboard and every figure read:

    entity, condition, estimate, n, se, raw_mean

Then ranks entities with a weighted score across conditions, minus a penalty
for instability. Weights are a project decision, not a biological law, so the
sensitivity helper is part of the deliverable, not an extra.

Replace `shrunken_estimates` with BLUPs from a mixed model when time allows.
The columns stay the same, so nothing downstream changes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def shrunken_estimates(df: pd.DataFrame, entity: str, condition: str, outcome: str,
                       env: str | None = None, min_n: int = 1) -> pd.DataFrame:
    """Condition-centered means, shrunk toward zero by cell size.

    env: the finest unit to center within (a trial, site-year, batch). Centering
    removes the condition effect so entities are compared on equal footing.
    """
    d = df.dropna(subset=[outcome]).copy()
    center_on = env if env and env in d else condition
    d["_c"] = d[outcome] - d.groupby(center_on, observed=True)[outcome].transform("mean")

    g = d.groupby([entity, condition], observed=True)["_c"]
    out = g.agg(raw_mean="mean", n="size", sd="std").reset_index()
    out = out[out["n"] >= min_n]

    # k = within-entity noise variance / between-entity variance, estimated crudely
    within = np.nanmean(out["sd"].pow(2)) if out["sd"].notna().any() else d["_c"].var()
    between = max(out["raw_mean"].var() - within / max(out["n"].mean(), 1), 1e-9)
    k = float(np.clip(within / between, 1, 200))

    out["estimate"] = out["raw_mean"] * out["n"] / (out["n"] + k)
    out["se"] = np.sqrt(within / out["n"].clip(lower=1))
    out.attrs["k"] = k
    return out.rename(columns={entity: "entity", condition: "condition"})[
        ["entity", "condition", "estimate", "se", "n", "raw_mean"]]


def score(results: pd.DataFrame, weights: dict[str, float], penalty: float = 0.5,
          min_n: int = 5) -> pd.DataFrame:
    """Weighted mean across conditions minus `penalty` x spread across conditions."""
    r = results[results["n"] >= min_n]
    wide = r.pivot_table(index="entity", columns="condition", values="estimate")
    wide = wide.dropna(subset=list(weights))
    w = pd.Series(weights, dtype=float)
    w = w / w.sum()
    perf = (wide[w.index] * w).sum(axis=1)
    spread = wide[w.index].std(axis=1)
    counts = r.pivot_table(index="entity", columns="condition", values="n").reindex(wide.index)
    out = wide.copy()
    out["performance"] = perf
    out["instability"] = spread
    out["score"] = perf - penalty * spread
    out["min_n"] = counts.min(axis=1)
    return out.sort_values("score", ascending=False)


def weight_sensitivity(results: pd.DataFrame, grids: list[dict[str, float]], top: int = 10,
                       penalty: float = 0.5) -> pd.DataFrame:
    """How much does the shortlist move when the weights move? Report this."""
    rows = []
    base = set(score(results, grids[0], penalty).head(top).index)
    for g in grids:
        s = score(results, g, penalty).head(top)
        rows.append({"weights": ", ".join(f"{k}={v:g}" for k, v in g.items()),
                     "overlap_with_first": len(base & set(s.index)),
                     "top_entity": s.index[0]})
    return pd.DataFrame(rows)


def rank_reversal(results: pd.DataFrame, weights: dict[str, float], top: int = 10,
                  penalty: float = 0.5) -> pd.DataFrame:
    """Slide 5: who makes the top list on the naive metric vs the decision score."""
    s = score(results, weights, penalty)
    naive = s["performance"].rank(ascending=False)
    smart = s["score"].rank(ascending=False)
    out = pd.DataFrame({"rank_mean": naive, "rank_score": smart,
                        "moved": naive - smart}).sort_values("rank_score")
    out["in_top_by_mean"] = out["rank_mean"] <= top
    out["in_top_by_score"] = out["rank_score"] <= top
    return out


if __name__ == "__main__":  # smoke test on synthetic data
    rng = np.random.default_rng(0)
    n_ent, conds = 200, ["Dry", "Normal", "Wet"]
    rows = []
    for e in range(n_ent):
        g = rng.normal(0, 8)
        slope = rng.normal(0, 6)
        for ci, c in enumerate(conds):
            for _ in range(rng.integers(1, 12)):
                rows.append({"LINE": f"L{e:03d}", "REGIME": c, "ENV": f"{c}{rng.integers(0, 5)}",
                             "Y": 180 + 20 * ci + g + slope * (ci - 1) + rng.normal(0, 15)})
    df = pd.DataFrame(rows)
    res = shrunken_estimates(df, "LINE", "REGIME", "Y", env="ENV")
    print(res.head(), "\nshrinkage k =", round(res.attrs["k"], 1))
    s = score(res, {"Dry": 0.4, "Normal": 0.3, "Wet": 0.3})
    print("\ntop 5 by score:\n", s[["performance", "instability", "score", "min_n"]].head())
    print("\nsensitivity:\n", weight_sensitivity(res, [
        {"Dry": 0.4, "Normal": 0.3, "Wet": 0.3},
        {"Dry": 0.6, "Normal": 0.2, "Wet": 0.2},
        {"Dry": 1 / 3, "Normal": 1 / 3, "Wet": 1 / 3}]))
