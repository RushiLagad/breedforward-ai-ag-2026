"""The two figures that carry the deck. Run after src/rank.py has written results.

    python src/figures.py results/results.csv

Everything imports src/style.py so the whole deck looks like one system.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.rank import score  # noqa: E402
from src.style import REGIME_COLORS, apply_theme, save, title  # noqa: E402


def coverage_heatmap(res: pd.DataFrame, max_entities: int = 60):
    """Slide 3: what the data actually covers. Nobody else will show this."""
    wide = res.pivot_table(index="entity", columns="condition", values="n", fill_value=0)
    wide = wide.sort_values(list(wide.columns), ascending=False).head(max_entities)
    fig, ax = plt.subplots(figsize=(6, 8))
    im = ax.imshow(wide.values, aspect="auto", cmap="Blues", vmin=0)
    ax.set_xticks(range(wide.shape[1]), wide.columns)
    ax.set_yticks([])
    ax.set_ylabel(f"entities (top {len(wide)} by coverage)")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="observations per cell")
    title(ax, "Coverage decides what is answerable",
          f"{(wide.values < 5).mean():.0%} of cells have fewer than 5 observations")
    return fig


def reversal_slopegraph(res: pd.DataFrame, weights: dict, top: int = 10, penalty: float = 0.5):
    """Slide 5: the top list by the naive metric vs by the decision score."""
    s = score(res, weights, penalty=penalty)
    by_mean = s.sort_values("performance", ascending=False).head(top)
    by_score = s.head(top)
    keep = list(dict.fromkeys(list(by_mean.index) + list(by_score.index)))
    left = {e: i for i, e in enumerate(by_mean.index)}
    right = {e: i for i, e in enumerate(by_score.index)}

    fig, ax = plt.subplots(figsize=(8, 7))
    for e in keep:
        l, r = left.get(e), right.get(e)
        if l is not None and r is not None:
            col, lw = ("#0072B2", 2.0) if l == r else ("#E69F00", 2.4)
            ax.plot([0, 1], [l, r], color=col, lw=lw, zorder=2)
        elif l is not None:
            ax.plot([0, 0.45], [l, l], color="#CC0000", lw=2, ls=":", zorder=1)
            ax.text(0.47, l, "drops out", va="center", fontsize=11, color="#CC0000")
        else:
            ax.plot([0.55, 1], [r, r], color="#009E73", lw=2, ls=":", zorder=1)
            ax.text(0.53, r, "enters", va="center", ha="right", fontsize=11, color="#009E73")
        if l is not None:
            ax.text(-0.03, l, str(e), ha="right", va="center", fontsize=11)
        if r is not None:
            ax.text(1.03, r, str(e), ha="left", va="center", fontsize=11)

    ax.set_xlim(-0.35, 1.35)
    ax.invert_yaxis()
    ax.set_xticks([0, 1], ["ranked by\nmean performance", "ranked by\ndecision score"])
    ax.set_yticks([])
    ax.grid(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    changed = len(set(by_mean.index) ^ set(by_score.index)) // 2
    title(ax, f"{changed} of the top {top} change when stability counts",
          "orange = moved, dotted = enters or leaves the shortlist")
    return fig


def regime_profile(res: pd.DataFrame, entities: list[str]):
    """Slide 7 companion: how a handful of entities respond across conditions."""
    conds = sorted(res["condition"].unique())
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(conds))
    for e in entities:
        d = res[res["entity"] == e].set_index("condition").reindex(conds)
        ax.errorbar(x, d["estimate"], yerr=d["se"], marker="o", capsize=3, label=str(e))
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(x, conds)
    ax.set_ylabel("performance vs environment mean")
    ax.legend(ncol=2)
    for c, col in REGIME_COLORS.items():
        if c in conds:
            ax.get_xticklabels()[conds.index(c)].set_color(col)
    title(ax, "Different lines, different reaction norms")
    return fig


if __name__ == "__main__":
    apply_theme()
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src and Path(src).exists():
        res = pd.read_csv(src, dtype={"entity": str})
    else:
        from src.demo import demo_results
        res = demo_results()
        print("no results file given, using demo data")

    w = {c: 1 / res["condition"].nunique() for c in sorted(res["condition"].unique())}
    for fig, name in ((coverage_heatmap(res), "coverage"),
                      (reversal_slopegraph(res, w), "reversal"),
                      (regime_profile(res, res["entity"].unique()[:4].tolist()), "profiles")):
        print("wrote", save(fig, name))
        plt.close(fig)
