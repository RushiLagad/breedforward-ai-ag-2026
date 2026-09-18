"""The honest G x E test: do lines re-rank across environment regimes?

Compares the correlation of line effects BETWEEN regimes to the split-half
correlation WITHIN a regime. If between is well below within, G x E is real.
If they are equal, the re-ranking is noise. Run after src/build.py.

    python src/gxe_test.py

Result on the 2025/2026 Bayer legacy data: between 0.23, within 0.18-0.25 (lines);
between 0.50, within 0.45-0.64 (parents with >= 30 environments). No signal.
"""
import glob
import numpy as np
import pandas as pd

df = pd.read_pickle("results/pheno_env_ready.pkl")
y = df.dropna(subset=["YLD"]).copy()
# center within environment x population: removes env, tester and population at once
y["yc"] = y["YLD"] - y.groupby(["ENV", "POP"])["YLD"].transform("mean")
rng = np.random.default_rng(0)
y["h"] = rng.integers(0, 2, len(y))
REG = "REGIME_STRESS"


def split_half(sub, key, min_n=2):
    m = sub.groupby([key, "h"])["yc"].agg(["mean", "count"]).unstack()
    ok = (m["count"] >= min_n).all(axis=1)
    return m.loc[ok, "mean"].corr().iloc[0, 1], int(ok.sum())


def between(sub, key, a, b, min_n=2):
    m = sub[sub[REG].isin([a, b])].groupby([key, REG], observed=True)["yc"].agg(["mean", "count"]).unstack()
    ok = (m["count"][[a, b]] >= min_n).all(axis=1)
    return m.loc[ok, "mean"][[a, b]].corr().iloc[0, 1], int(ok.sum())


print("== LINE level ==")
for r in ["HotDry", "CoolWet"]:
    c, n = split_half(y[y[REG] == r], "LINE_ID"); print(f"  within {r:8s} split-half r = {c:.3f}  ({n:,} lines)")
for a, b in [("HotDry", "CoolWet"), ("HotDry", "Moderate")]:
    c, n = between(y, "LINE_ID", a, b); print(f"  between {a} vs {b}: r = {c:.3f}  ({n:,} lines)")

# heritability proxy
g = y.groupby("LINE_ID")["yc"]; n = g.count(); m = g.mean()
within = y.groupby("LINE_ID")["yc"].var().mean()
bet = m[n >= 5].var() - within / n[n >= 5].mean()
print(f"  line var {bet:.1f}, residual {within:.1f} -> plot h2 {bet/(bet+within):.2f}, line-mean h2 at n=7 {bet/(bet+within/7):.2f}")

# regime share of environment mean yield
em = y.groupby("ENV").agg(YLD=("YLD", "mean"), R=(REG, "first"))
share = 1 - (em["YLD"] - em.groupby("R", observed=True)["YLD"].transform("mean")).var() / em["YLD"].var()
print(f"  regime explains {share:.1%} of environment mean yield:", em.groupby("R", observed=True)["YLD"].mean().round(1).to_dict())

# == PARENT level: parents from imputed genotype files (first two rows) ==
par = {}
for grp in ["C1", "C2"]:
    for f in glob.glob(f"data/ImputedPopulations{grp}/*.csv"):
        pop = f.split("/")[-1].replace("_Imputed.csv", "")
        with open(f) as fh:
            next(fh); ps = []
            for line in fh:
                i = line.split(",", 1)[0].strip('"')
                if i.startswith("PID"): ps.append(i)
                else: break
        par[pop] = ps
if par:
    pp = pd.DataFrame([(k, *(v + [None, None])[:2]) for k, v in par.items()], columns=["POP", "P1", "P2"])
    y = y.merge(pp, on="POP", how="left")
    y["ye"] = y["YLD"] - y.groupby("ENV")["YLD"].transform("mean")
    long = pd.concat([y.assign(PARENT=y["P1"]), y.assign(PARENT=y["P2"])])
    cell = long.groupby(["PARENT", REG, "ENV"], observed=True).agg(yc=("ye", "mean")).reset_index()
    cell["h"] = rng.integers(0, 2, len(cell))
    good = cell.groupby("PARENT")["ENV"].nunique(); cell = cell[cell["PARENT"].isin(good[good >= 30].index)]
    print(f"== PARENT level ({cell.PARENT.nunique()} parents with >= 30 environments, env-level means) ==")
    for r in ["HotDry", "CoolWet"]:
        c, n = split_half(cell[cell[REG] == r], "PARENT", 8); print(f"  within {r:8s} split-half r = {c:.3f}  ({n} parents)")
    for a, b in [("HotDry", "CoolWet"), ("HotDry", "Moderate")]:
        c, n = between(cell, "PARENT", a, b, 8); print(f"  between {a} vs {b}: r = {c:.3f}  ({n} parents)")
    y.to_pickle("results/pheno_env_parents.pkl")
