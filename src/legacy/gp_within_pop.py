"""Within-population genomic prediction, CV1 (new lines, same population).

Ridge on polymorphic SNPs from the imputed files; target is the line mean of
yield centered within environment x population. Reports r per population.
Literature on this data: 0.41-0.59 with GBLUP (Lian et al. 2014). Anything
above that from a quick ridge means leakage.

    python src/gp_within_pop.py            # 50 random populations
    python src/gp_within_pop.py 999        # all
"""
import sys, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold

warnings.filterwarnings("ignore")
N_POPS = int(sys.argv[1]) if len(sys.argv) > 1 else 50

y = pd.read_pickle("results/pheno_env_ready.pkl").dropna(subset=["YLD"]).copy()
y["yc"] = y["YLD"] - y.groupby(["ENV", "POP"])["YLD"].transform("mean")
blue = y.groupby(["POP", "LINE_ID", "LINE"]).agg(yc=("yc", "mean"), mst=("MST", "mean"), n=("yc", "size")).reset_index()
# C2 file stores LINE as "12.0": strip the float suffix, then leading zeros
blue["key"] = [s[:-2] if s.endswith(".0") else s for s in blue["LINE"]]
blue["key"] = [s.lstrip("0") or "0" for s in blue["key"]]

rng = np.random.default_rng(0)
pops = sorted(blue["POP"].unique())
pick = pops if N_POPS >= len(pops) else rng.choice(pops, N_POPS, replace=False)
res = []
for pop in pick:
    grp = pop.split(".")[0]
    try:
        g = pd.read_csv(f"data/ImputedPopulations{grp}/{pop}_Imputed.csv", index_col=0, low_memory=False)
    except FileNotFoundError:
        continue
    g = g[~g.index.astype(str).str.startswith("PID")]
    g.index = [str(i).lstrip("0") or "0" for i in g.index]
    g = g.apply(pd.to_numeric, errors="coerce"); g = g.loc[:, g.std() > 0]; g = g.fillna(g.mean())
    b = blue[(blue["POP"] == pop) & (blue["n"] >= 3)].set_index("key")
    common = g.index.intersection(b.index)
    if len(common) < 60 or g.shape[1] < 50:
        continue
    X = g.loc[common].values
    for trait in ["yc", "mst"]:
        t = b.loc[common, trait].values; ok = ~np.isnan(t); Xo, to = X[ok], t[ok]
        if len(to) < 60:
            continue
        pred = np.zeros(len(to))
        for tr, te in KFold(5, shuffle=True, random_state=0).split(Xo):
            pred[te] = RidgeCV(alphas=np.logspace(0, 4, 9)).fit(Xo[tr], to[tr]).predict(Xo[te])
        res.append({"pop": pop, "trait": "YLD" if trait == "yc" else "MST", "n_lines": len(to),
                    "n_markers": X.shape[1], "r_cv1": np.corrcoef(pred, to)[0, 1]})

r = pd.DataFrame(res)
print(r.groupby("trait")["r_cv1"].describe().round(3))
r.to_csv("results/gp_within_pop.csv", index=False)
print("wrote results/gp_within_pop.csv")
