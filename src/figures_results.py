"""Deck figures from the real stage 2 and stage 3 results (no dataset needed, reads results_summary/).

    python src/figures_results.py

Deck v2 changes (Sep 19): the two family-based bars share one hue and the two genome-based bars share
another, with group labels under the axis; the sampling curve shows the family-mean curve only, labels the
genotype-only point, and carries the "first 7.8k plots vs the next 31k" message in the annotations.
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.style import apply_theme, save, title, PALETTE  # noqa: E402

apply_theme()
S2 = pd.read_csv("results_summary/stage2_results.csv")
S3 = pd.read_csv("results_summary/stage3_schemes.csv")
S3b = pd.read_csv("results_summary/stage3b_two_stage.csv")
S4 = pd.read_csv("results_summary/stage4_sampling_curve.csv")

# One meaning per hue, everywhere: warm = the genome, blue = the family.
GENOME, GENOME_PLUS = PALETTE[5], PALETTE[1]      # vermillion, orange
FAMILY, FAMILY_PLUS = PALETTE[0], PALETTE[4]      # blue, light blue
MUTED = "#555555"

# ---------- Figure 1: what you know about a line vs how well you can rank it (yield) ----------
yld = S3[S3.trait == "YLD"].iloc[0]
two = S3b[(S3b.trait == "YLD") & (S3b.scheme == "two_stage")].iloc[0]
n_pred = int(S4[(S4.trait == "YLD") & (S4.scheme == "sib") & (S4.frac == 0.5)].n_pred.iloc[0])
levels = ["genotype only", "genotype,\nsiblings in training", "sibling mean,\nno markers", "sibling mean +\nfamily markers"]
r = [yld.r_newyear, yld.r_sib_augmented, yld.r_sibmean, two.r]
gain = [yld.gain_newyear, yld.gain_sib_augmented, yld.gain_sibmean, two.gain]
gmax = yld.gain_max
fig, ax = plt.subplots(figsize=(10, 5.8))
cols = [GENOME, GENOME_PLUS, FAMILY, FAMILY_PLUS]
bars = ax.bar(levels, gain, color=cols, width=0.62)
ax.axhline(gmax, color=MUTED, lw=1, ls="--")
ax.text(3.4, gmax + 0.25, f"perfect foresight +{gmax:.1f}", ha="right", fontsize=11, color=MUTED)
for b, rr, g in zip(bars, r, gain):
    ax.text(b.get_x() + b.get_width() / 2, g + 0.2, f"+{g:.1f} bu/ac\nr = {rr:.2f}", ha="center", va="bottom", fontsize=11)
ax.set_ylabel("gain, top 20% advanced (bu/ac)"); ax.set_ylim(0, gmax + 2.5)
# group labels under the tick labels: the two ways of using the genome, the two ways of using the family
trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
for x0, x1, lab, c in ((-0.31, 1.31, "what the genome knows", GENOME), (1.69, 3.31, "what the family knows", FAMILY)):
    ax.plot([x0, x1], [-0.175, -0.175], transform=trans, color=c, lw=1.5, clip_on=False)
    ax.text((x0 + x1) / 2, -0.20, lab, transform=trans, ha="center", va="top", fontsize=11.5, color=c, fontweight="bold")
title(ax, "Half a family's plots beat 2,911 SNPs for ranking the other half",
      f"same {n_pred:,} untested 2008 lines; predicted from earlier years plus the phenotyped siblings")
fig.subplots_adjust(bottom=0.24)
save(fig, "fig_information_vs_gain"); plt.close(fig)

# ---------- Figure 2: accuracy by trait and scheme ----------
tr = ["YLD", "MST", "TWT"]
new = [S3[S3.trait == t].r_newyear.iloc[0] for t in tr]
sib = [S3b[(S3b.trait == t) & (S3b.scheme == "sib")].r.iloc[0] for t in tr]
twos = [S3b[(S3b.trait == t) & (S3b.scheme == "two_stage")].r.iloc[0] for t in tr]
x = np.arange(len(tr)); w = 0.26
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.bar(x - w, new, w, label="genotype only", color=GENOME)
ax.bar(x, sib, w, label="sibling mean", color=FAMILY)
ax.bar(x + w, twos, w, label="sibling mean + markers", color=FAMILY_PLUS)
for i, (a, b, c) in enumerate(zip(new, sib, twos)):
    for dx, v in ((-w, a), (0, b), (w, c)): ax.text(i + dx, v + 0.01, f"{v:.2f}", ha="center", fontsize=10)
ax.set_xticks(x, ["Yield", "Grain moisture", "Test weight"]); ax.set_ylabel("correlation with observed 2008 line mean"); ax.set_ylim(0, 0.75)
ax.legend(loc="upper left", ncol=3)
title(ax, "Markers add most for moisture and test weight, least for yield", "predicting the un-phenotyped half of each 2008 population")
save(fig, "fig_accuracy_by_trait"); plt.close(fig)

# ---------- Figure 3: breeder's equation, plots vs gain ----------
sd_true, i20 = 6.45, 1.40
plots_full = 77353
scen = [("markers only\n0 plots", 0.13, 0), ("sample 1/2 of each family\n~39k plots", 0.36, 0.5), ("full trial\n77k plots", 0.50, 1.0)]
fig, ax = plt.subplots(figsize=(8, 4.8))
xs = [s[2] * plots_full / 1000 for s in scen]; ys = [i20 * s[1] * sd_true for s in scen]
ax.plot(xs, ys, marker="o", ms=9, color=FAMILY, lw=2)
for (lab, rr, f), xx, yy in zip(scen, xs, ys):
    ax.annotate(f"{lab}\nr = {rr:.2f} → +{yy:.1f} bu/ac", (xx, yy), textcoords="offset points", xytext=(12, -40 if f == 1 else (14 if f == 0 else 10)), fontsize=10.5)
ax.set_xlabel("field plots used in 2008 (thousands)"); ax.set_ylabel("expected gain, top 20% advanced (bu/ac)")
ax.set_xlim(-4, 92); ax.set_ylim(0, 5.5)
title(ax, "Half the plots keep about 70% of the gain", "breeder's equation: gain = 1.40 × accuracy × 6.45 bu/ac genetic sd")
save(fig, "fig_plots_vs_gain"); plt.close(fig)

# ---------- Figure 4: year-to-year accuracy vs connectedness ----------
conn = {2007: 0.15, 2008: 0.29}
fig, ax = plt.subplots(figsize=(6.5, 4.5))
for yr, c in zip((2007, 2008), (GENOME_PLUS, FAMILY)):
    rr = S2[(S2.year == yr) & (S2.trait == "YLD")].r_markers.iloc[0]
    ax.scatter(conn[yr], rr, s=160, color=c, zorder=3); ax.annotate(f"predict {yr}", (conn[yr], rr), xytext=(10, -4), textcoords="offset points", fontsize=11)
ax.set_xlabel("share of new-year populations with both parents seen before"); ax.set_ylabel("marker accuracy, yield (r)")
ax.set_xlim(0, 0.4); ax.set_ylim(0, 0.2)
title(ax, "New-year accuracy tracks pedigree connection, not the model", "same ridge model, same tuning, two hold-out years")
save(fig, "fig_year_connectedness"); plt.close(fig)
print("wrote figures/fig_information_vs_gain.png, fig_accuracy_by_trait.png, fig_plots_vs_gain.png, fig_year_connectedness.png")

# ---------- Figure 5: the sampling curve (real, measured) ----------
yl = S4[S4.trait == "YLD"]
g0 = S3[S3.trait == "YLD"].iloc[0]
d = yl[yl.scheme == "sib"].sort_values("frac")
d10 = d[d.frac == 0.10].iloc[0]; d50 = d[d.frac == 0.50].iloc[0]
x10, x50 = d10.plots_used / 1000, d50.plots_used / 1000
ceiling = yl.gain_max.mean()
fig, ax = plt.subplots(figsize=(10, 5.6))
# the curve: family mean only. The marker term adds nothing for yield on this curve, so it stays off the slide.
ax.plot(d.plots_used / 1000, d.gain, marker="o", ms=7, lw=2.2, color=FAMILY, zorder=3)
ax.text(d.plots_used.iloc[-1] / 1000 + 1.2, d.gain.iloc[-1], "family mean of the\nphenotyped siblings", va="center", fontsize=10.5, color=FAMILY)
# the genotype-only point, no plots
ax.scatter([0], [g0.gain_newyear], s=130, color=GENOME, zorder=4)
ax.text(1.6, g0.gain_newyear - 0.95, f"genotype only, no plots: +{g0.gain_newyear:.1f}", fontsize=11, color=GENOME, va="center")
# the first 7.8k plots buy most of it
ax.annotate("", xy=(x10 - 0.5, d10.gain - 0.15), xytext=(0.4, g0.gain_newyear + 0.2),
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.1, connectionstyle="arc3,rad=-0.28"))
ax.text(0.6, 5.35, f"+{round(d10.gain, 1) - round(g0.gain_newyear, 1):.1f} bu/ac from the\nfirst {d10.plots_used/1000:.1f}k plots", fontsize=11, color="#1A1A1A", va="bottom")
# the next 31k plots buy the last 0.4
yb = 7.35
ax.plot([x10, x50], [yb, yb], color="#1A1A1A", lw=1.2)
ax.plot([x10, x10], [yb - 0.55, yb], color="#1A1A1A", lw=1.2); ax.plot([x50, x50], [yb - 0.55, yb], color="#1A1A1A", lw=1.2)
ax.text((x10 + x50) / 2, yb + 0.3, f"{x50 / x10:.0f}× the plots for the last +{round(d50.gain, 1) - round(d10.gain, 1):.1f} bu/ac",
        ha="center", va="bottom", fontsize=12.5, fontweight="bold", color="#1A1A1A")
# the two points the talk names
ax.annotate(f"10% of every family\n{int(d10.plots_used):,} plots → +{d10.gain:.1f}", (x10, d10.gain), xytext=(x10 + 1.6, 3.85),
            textcoords="data", fontsize=11, va="top", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate(f"50% of every family\n{int(d50.plots_used):,} plots → +{d50.gain:.1f}", (x50, d50.gain), xytext=(x50 + 1.6, 3.85),
            textcoords="data", fontsize=11, va="top", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
# ceiling and the full trial
ax.axhline(ceiling, color=MUTED, lw=1, ls="--")
ax.text(0.6, ceiling + 0.25, "perfect foresight: if you knew every 2008 result in advance", fontsize=11, color=MUTED)
ax.axvline(77.353, color="#999999", lw=1, ls=":"); ax.text(76.2, 0.45, "full 2008 trial\n77k plots", ha="right", fontsize=10, color=MUTED)
ax.set_xlabel("field plots spent on the 2008 candidates (thousands)"); ax.set_ylabel("realised 2008 gain, top 20% advanced (bu/ac)")
ax.set_xlim(-2, 80); ax.set_ylim(0, ceiling + 1.6)
title(ax, "Phenotyping 10% of each family captures most of the achievable gain",
      "2008 candidates, every family sampled (stratified), the rest predicted from the family mean; mean of 3 draws")
save(fig, "fig_sampling_curve"); plt.close(fig)
print("wrote figures/fig_sampling_curve.png")
