"""One visual system for the whole deck. Import this before any plot.

    from src.style import apply_theme, PALETTE, REGIME_COLORS, save
    apply_theme()

Rules baked in: large fonts for projection, no chartjunk, one categorical
palette used consistently, and a grayscale check before you ship.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Colorblind-safe categorical palette (Okabe-Ito). Same order everywhere.
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]

# Fixed meanings so a color never changes meaning between slides.
REGIME_COLORS = {"Dry": "#D55E00", "Normal": "#0072B2", "Wet": "#009E73"}

GRID = "#D9D9D9"
TEXT = "#1A1A1A"


def apply_theme(base: int = 14) -> None:
    """Projector-friendly defaults. Call once at the top of every script."""
    mpl.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "axes.edgecolor": TEXT,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.titlesize": base + 4,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": base + 1,
        "xtick.labelsize": base,
        "ytick.labelsize": base,
        "legend.fontsize": base,
        "legend.frameon": False,
        "font.size": base,
        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "scatter.edgecolors": "none",
    })


def save(fig, name: str, outdir: str | Path = "figures", grayscale_check: bool = True) -> Path:
    """Save a figure and, by default, also write a grayscale copy to check contrast."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{name}.png"
    fig.savefig(path)
    if grayscale_check:
        try:
            import numpy as np
            from matplotlib import image as mpimg
            rgb = mpimg.imread(path)[:, :, :3]
            gray = rgb @ [0.2126, 0.7152, 0.0722]
            plt.imsave(outdir / f"{name}_gray.png", gray, cmap="gray")
        except Exception:  # never let a check break a build at 2am
            pass
    return path


def title(ax, claim: str, subtitle: str | None = None) -> None:
    """Every figure title is a claim, not a label. Subtitle sits under it, never on it."""
    ax.set_title(claim, pad=30 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.015, subtitle, transform=ax.transAxes,
                fontsize=mpl.rcParams["font.size"] - 1, color="#555555", va="bottom")
