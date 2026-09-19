"""Shared pieces for the 2008 sibling stages (3, 3b, 4, 5).

Two rules live here so every stage applies them the same way:

1. Stratified family split. A share f of every family is declared phenotyped, at least one line per
   family (and at least one held out), so "sample every family" is enforced rather than hoped for.
2. Training-only centering. Environment x tester cell means are computed from training plots only
   (every pre-2008 plot plus the phenotyped 2008 lines), never from held-out lines, and then applied
   to all plots. Held-out outcomes therefore cannot leak into the target definition.
"""
import numpy as np
import pandas as pd

TRAITS = ["YLD", "MST", "TWT", "ERM", "RTLP", "STLP"]


def load_plots():
    y = pd.read_pickle("results/pheno_env_parents.pkl")
    y["TESTER"] = y["TESTER"].fillna("NA")
    return y


def genotype_index():
    G = np.load("results/G.npy", mmap_mode="r")
    gidx = pd.Index(pd.read_csv("results/G_ids.csv", header=None)[0])
    return G, gidx


def line_keys(line):
    """Genotype row index for each line: POP|LINE with the C2 '.0' and leading zeros stripped."""
    key = [s[:-2] if s.endswith(".0") else s for s in line["LINE"]]
    return [s.lstrip("0") or "0" for s in key]


def lines_2008(y, gidx):
    """The 2008 candidate lines with a genotype (uncentered; used only to define the split)."""
    te = y[y.YEAR == 2008][["LINE_ID", "POP", "LINE"]].drop_duplicates("LINE_ID").copy()
    te["key"] = line_keys(te)
    te["gi"] = gidx.get_indexer(te["POP"] + "|" + te["key"])
    te = te[te.gi >= 0].drop_duplicates("gi").sort_values("LINE_ID").reset_index(drop=True)
    return te


def split_families(te, frac, rng):
    """Stratified split: per family, n_known = clip(round(frac*n), 1, n-1). Single-line families are
    held out (nothing to sample from). Returns a boolean Series 'known' aligned to te."""
    known = pd.Series(False, index=te.index)
    for pop, d in te.groupby("POP"):
        n = len(d)
        if n < 2:
            continue
        k = int(min(n - 1, max(1, round(frac * n))))
        pick = rng.choice(d.index.values, size=k, replace=False)
        known.loc[pick] = True
    return known


def centered_lines(y, heldout_ids, traits, extra_keys=("YEAR", "HG", "P1", "P2")):
    """Centre every plot within ENV x TESTER using means from training plots only, then aggregate to
    line means. heldout_ids: LINE_IDs whose plots must not contribute to any cell mean."""
    tr = ~y["LINE_ID"].isin(heldout_ids)
    out = y[["LINE_ID", "POP", "LINE", *extra_keys, "ENV", "TESTER", *traits]].copy()
    for t in traits:
        cell = y.loc[tr].groupby(["ENV", "TESTER"])[t].mean().rename("cell")
        env = y.loc[tr].groupby("ENV")[t].mean().rename("envm")
        m = out[["ENV", "TESTER"]].merge(cell, left_on=["ENV", "TESTER"], right_index=True, how="left") \
                                 .merge(env, left_on="ENV", right_index=True, how="left")
        mu = m["cell"].fillna(m["envm"]).values   # a cell with no training plot falls back to its environment mean
        out[t + "_c"] = out[t].values - mu
    agg = {t + "_c": (t + "_c", "mean") for t in traits}
    agg["n"] = ("LINE_ID", "size")
    keys = ["LINE_ID", "POP", "LINE", *extra_keys]
    line = out.groupby(keys, dropna=False).agg(**agg).reset_index()
    return line


def attach_genotypes(line, gidx):
    line = line.copy()
    line["key"] = line_keys(line)
    line["gi"] = gidx.get_indexer(line["POP"] + "|" + line["key"])
    return line[line.gi >= 0].drop_duplicates("gi").copy()


def rank_desc(df, col):
    """Deterministic ranking: by value descending, ties by LINE_ID ascending."""
    return df.sort_values([col, "LINE_ID"], ascending=[False, True], kind="mergesort")


def top_k_gain(df, pred_col, obs_col, frac=0.2):
    """Realised outcome of advancing the top frac by pred_col, scored on obs_col; and the oracle."""
    d = df[df[obs_col].notna()]
    k = int(frac * len(d))
    top = rank_desc(d, pred_col).head(k)
    oracle = rank_desc(d, obs_col).head(k)
    return top[obs_col].mean() - d[obs_col].mean(), oracle[obs_col].mean() - d[obs_col].mean(), k
