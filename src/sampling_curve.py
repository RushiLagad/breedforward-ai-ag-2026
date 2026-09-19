"""Plots-sampled curve: phenotype a fraction f of each 2008 family, predict the rest.
Schemes at each f: sibling mean; sibling mean + within-family markers; genotype-only (f=0 reference).
Repeated over 3 random draws. Output: results_summary/stage4_sampling_curve.csv"""
import time, numpy as np, pandas as pd
from sklearn.linear_model import Ridge
t0 = time.time()
G = np.load("results/G.npy", mmap_mode="r"); gidx = pd.Index(pd.read_csv("results/G_ids.csv", header=None)[0])
y = pd.read_pickle("results/pheno_env_parents.pkl"); y["TESTER"] = y.TESTER.fillna("NA")
TR = ["YLD", "MST", "TWT"]
for t in TR: y[t + "_c"] = y[t] - y.groupby(["ENV", "TESTER"])[t].transform("mean")
line = y.groupby(["LINE_ID", "POP", "YEAR", "LINE"]).agg(**{t + "_c": (t + "_c", "mean") for t in TR}, n=("YLD", "size")).reset_index()
line["key"] = [s[:-2] if s.endswith(".0") else s for s in line.LINE]; line["key"] = [s.lstrip("0") or "0" for s in line.key]
line["gi"] = gidx.get_indexer(line.POP + "|" + line.key); line = line[line.gi >= 0].drop_duplicates("gi")
te = line[line.YEAR == 2008].copy()
# genotype-only prediction from the across-population model (f = 0 reference), yield only, from stage 3 output
g0 = pd.read_csv("advance2008.csv", dtype={"LINE_ID": str})[["LINE_ID", "pred_yld_new"]] if False else None

plots_per_line = 4.8
rows = []
for rep in range(3):
    rng = np.random.default_rng(rep)
    te["u"] = rng.random(len(te))
    for f in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75]:
        for t in TR:
            col = t + "_c"; preds = []
            for pop, d in te.groupby("POP"):
                kn = d[(d.u < f) & d[col].notna()]; un = d[d.u >= f]
                if len(un) == 0: continue
                mu = kn[col].mean() if len(kn) else 0.0
                dev = np.zeros(len(un))
                if len(kn) >= 25:
                    X = np.asarray(G[kn.gi.values], dtype=np.float64); keep = X.std(0) > 0; X = X[:, keep]
                    m = Ridge(alpha=len(kn) * 2.0).fit(X, kn[col].values - mu)
                    dev = m.predict(np.asarray(G[un.gi.values], dtype=np.float64)[:, keep])
                preds.append(pd.DataFrame({"gi": un.gi.values, "sib": mu, "two": mu + dev, "nk": len(kn)}))
            P = pd.concat(preds).merge(te[["gi", col]], on="gi").dropna()
            for name in ["sib", "two"]:
                r = np.corrcoef(P[name], P[col])[0, 1]; k = int(0.2 * len(P))
                gain = P.nlargest(k, name)[col].mean() - P[col].mean(); gmax = P.nlargest(k, col)[col].mean() - P[col].mean()
                rows.append(dict(rep=rep, frac=f, trait=t, scheme=name, n_pred=len(P), r=r, gain=gain, gain_max=gmax,
                                 plots_used=int(f * len(te) * plots_per_line)))
        print(f"rep {rep} f={f:.2f} done | {time.time()-t0:.0f}s")
res = pd.DataFrame(rows)
summ = res.groupby(["frac", "trait", "scheme"]).agg(r=("r", "mean"), r_sd=("r", "std"), gain=("gain", "mean"), gain_max=("gain_max", "mean"), plots_used=("plots_used", "first")).reset_index()
summ.to_csv("results_summary/stage4_sampling_curve.csv", index=False)
print(summ[summ.trait == "YLD"].round(3).to_string(index=False))
print(f"done {time.time()-t0:.0f}s")
