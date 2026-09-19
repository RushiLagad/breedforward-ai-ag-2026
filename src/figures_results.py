"""Deck figures from the real stage 2 and stage 3 results (no dataset needed, reads results_summary/).

    python src/figures_results.py
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.style import apply_theme, save, title, PALETTE  # noqa: E402

apply_theme()
S2 = pd.read_csv("results_summary/stage2_results.csv")
S3 = pd.read_csv("results_summary/stage3_schemes.csv")
S3b = pd.read_csv("results_summary/stage3b_two_stage.csv")

# ---------- Figure 1: what you know about a line vs how well you can rank it (yield) ----------
yld = S3[S3.trait == "YLD"].iloc[0]
two = S3b[(S3b.trait == "YLD") & (S3b.scheme == "two_stage")].iloc[0]
levels = ["genotype only", "genotype,\nsiblings in training", "sibling mean,\nno markers", "sibling mean +\nfamily markers"]
r = [yld.r_newyear, yld.r_sib_augmented, yld.r_sibmean, two.r]
gain = [yld.gain_newyear, yld.gain_sib_augmented, yld.gain_sibmean, two.gain]
gmax = yld.gain_max
fig, ax = plt.subplots(figsize=(10, 5.5))
cols = [PALETTE[5], PALETTE[1], PALETTE[0], PALETTE[2]]
bars = ax.bar(levels, gain, color=cols, width=0.62)
ax.axhline(gmax, color="#555555", lw=1, ls="--"); ax.text(3.4, gmax + 0.25, f"perfect foresight +{gmax:.1f}", ha="right", fontsize=11, color="#555555")
for b, rr, g in zip(bars, r, gain):
    ax.text(b.get_x() + b.get_width() / 2, g + 0.2, f"+{g:.1f} bu/ac\nr = {rr:.2f}", ha="center", va="bottom", fontsize=11)
ax.set_ylabel("gain, top 20% advanced (bu/ac)"); ax.set_ylim(0, gmax + 2.5)
title(ax, "Half a family's plots beat 2,911 SNPs for ranking the other half", "2008 lines, predicted from 2000-2007 plus the phenotyped siblings")
save(fig, "fig_information_vs_gain"); plt.close(fig)

# ---------- Figure 2: accuracy by trait and scheme ----------
tr = ["YLD", "MST", "TWT"]
new = [S3[S3.trait == t].r_newyear.iloc[0] for t in tr]
sib = [S3b[(S3b.trait == t) & (S3b.scheme == "sib")].r.iloc[0] for t in tr]
twos = [S3b[(S3b.trait == t) & (S3b.scheme == "two_stage")].r.iloc[0] for t in tr]
x = np.arange(len(tr)); w = 0.26
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.bar(x - w, new, w, label="genotype only", color=PALETTE[5])
ax.bar(x, sib, w, label="sibling mean", color=PALETTE[0])
ax.bar(x + w, twos, w, label="sibling mean + markers", color=PALETTE[2])
for i, (a, b, c) in enumerate(zip(new, sib, twos)):
    for dx, v in ((-w, a), (0, b), (w, c)): ax.text(i + dx, v + 0.01, f"{v:.2f}", ha="center", fontsize=10)
ax.set_xticks(x, ["Yield", "Grain moisture", "Test weight"]); ax.set_ylabel("correlation with observed 2008 line mean"); ax.set_ylim(0, 0.75)
ax.legend(loc="upper left", ncol=3)
title(ax, "Markers add most for moisture and test weight, least for yield", "predicting the un-phenotyped half of each 2008 population")
save(fig, "fig_accuracy_by_trait"); plt.close(fig)

# ---------- Figure 3: breeder's equation, plots vs gain ----------
sd_true, i20 = 6.29, 1.40
plots_full = 77353
scen = [("markers only\n0 plots", 0.13, 0), ("sample 1/2 of each family\n~39k plots", 0.35, 0.5), ("full trial\n77k plots", 0.50, 1.0)]
fig, ax = plt.subplots(figsize=(8, 4.8))
xs = [s[2] * plots_full / 1000 for s in scen]; ys = [i20 * s[1] * sd_true for s in scen]
ax.plot(xs, ys, marker="o", ms=9, color=PALETTE[0], lw=2)
for (lab, rr, f), xx, yy in zip(scen, xs, ys):
    ax.annotate(f"{lab}\nr = {rr:.2f} → +{yy:.1f} bu/ac", (xx, yy), textcoords="offset points", xytext=(12, -40 if f == 1 else (14 if f == 0 else 10)), fontsize=10.5)
ax.set_xlabel("field plots used in 2008 (thousands)"); ax.set_ylabel("expected gain, top 20% advanced (bu/ac)")
ax.set_xlim(-4, 92); ax.set_ylim(0, 5.5)
title(ax, "Half the plots keep about 70% of the gain", "breeder's equation: gain = 1.40 × accuracy × 6.3 bu/ac genetic sd")
save(fig, "fig_plots_vs_gain"); plt.close(fig)

# ---------- Figure 4: year-to-year accuracy vs connectedness ----------
conn = {2007: 0.15, 2008: 0.29}
fig, ax = plt.subplots(figsize=(6.5, 4.5))
for yr, c in zip((2007, 2008), (PALETTE[1], PALETTE[0])):
    rr = S2[(S2.year == yr) & (S2.trait == "YLD")].r_markers.iloc[0]
    ax.scatter(conn[yr], rr, s=160, color=c, zorder=3); ax.annotate(f"predict {yr}", (conn[yr], rr), xytext=(10, -4), textcoords="offset points", fontsize=11)
ax.set_xlabel("share of new-year populations with both parents seen before"); ax.set_ylabel("marker accuracy, yield (r)")
ax.set_xlim(0, 0.4); ax.set_ylim(0, 0.2)
title(ax, "New-year accuracy tracks pedigree connection, not the model", "same ridge model, same tuning, two hold-out years")
save(fig, "fig_year_connectedness"); plt.close(fig)
print("wrote figures/fig_information_vs_gain.png, fig_accuracy_by_trait.png, fig_plots_vs_gain.png, fig_year_connectedness.png")
