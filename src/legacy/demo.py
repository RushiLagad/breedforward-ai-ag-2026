"""Synthetic results in the canonical schema, so every component runs before real data exists."""
from __future__ import annotations

import numpy as np
import pandas as pd

CONDITIONS = ["Dry", "Normal", "Wet"]


def demo_results(seed: int = 0, n_entities: int = 120) -> pd.DataFrame:
    """entity, condition, estimate, se, n — the same columns src/rank.py writes."""
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(n_entities):
        level, slope = rng.normal(0, 8), rng.normal(0, 6)
        for ci, c in enumerate(CONDITIONS):
            n = int(rng.integers(3, 15))
            rows.append({"entity": f"DEMO{e:03d}", "condition": c,
                         "estimate": level + slope * (ci - 1) + rng.normal(0, 2),
                         "se": 15 / np.sqrt(n), "n": n})
    return pd.DataFrame(rows)
