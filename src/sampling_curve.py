"""Stage 4: the sampling curve. Phenotype a share f of EVERY 2008 family (stratified, >= 1 line per family),
predict the rest from the family mean (with and without the within-family marker term), score on real
2008 yield. Three random draws per f. Plots are counted as the actual plots of the sampled lines.
Centering uses training plots only for each draw (src/common.py).

Output: results_summary/stage4_sampling_curve.csv (and the per-draw rows in stage4_sampling_curve_draws.csv)
"""
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from common import load_plots, genotype_index, lines_2008, split_families, centered_lines, attach_genotypes, top_k_gain

t0 = time.time()
G, gidx = genotype_index()
y = load_plots()
TR = ["YLD", "MST", "TWT"]
te = lines_2008(y, gidx)
FR = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75]
rows = []
for rep in range(3):
    for f in FR:
        rng = np.random.default_rng(1000 * rep + int(f * 100))
        kn_mask = split_families(te, f, rng)
        heldout = set(te.loc[~kn_mask, "LINE_ID"])
        line = attach_genotypes(centered_lines(y, heldout, TR, extra_keys=("YEAR",)), gidx)
        known = line[line.LINE_ID.isin(te.loc[kn_mask, "LINE_ID"])]
        unknown = line[line.LINE_ID.isin(heldout)]
        plots_used = int(known.n.sum())
        for t in TR:
            col = t + "_c"; preds = []
            kn_by_pop = {pop: d[d[col].notna()] for pop, d in known.groupby("POP")}
            for pop, un in unknown.groupby("POP"):
                kn = kn_by_pop.get(pop)
                if kn is None or len(kn) == 0:
                    continue   # no phenotyped sibling (single-line family): not predictable by this scheme
                mu = kn[col].mean(); dev = np.zeros(len(un))
                if len(kn) >= 30:
                    X = np.asarray(G[kn.gi.values], dtype=np.float64); keep = X.std(0) > 0
                    m = Ridge(alpha=len(kn) * 2.0).fit(X[:, keep], kn[col].values - mu)
                    dev = m.predict(np.asarray(G[un.gi.values], dtype=np.float64)[:, keep])
                preds.append(pd.DataFrame({"LINE_ID": un.LINE_ID.values, "obs": un[col].values, "sib": mu, "two": mu + dev}))
            P = pd.concat(preds).dropna()
            for name in ["sib", "two"]:
                r = np.corrcoef(P[name], P.obs)[0, 1]
                gain, gmax, k = top_k_gain(P, name, "obs")
                rows.append(dict(rep=rep, frac=f, trait=t, scheme=name, n_pred=len(P), r=r, gain=gain, gain_max=gmax, plots_used=plots_used))
        print(f"rep {rep} f={f:.2f}: {len(known):,} sampled lines, {plots_used:,} plots, {len(unknown):,} predicted | {time.time()-t0:.0f}s")
res = pd.DataFrame(rows)
res.round(5).to_csv("results_summary/stage4_sampling_curve_draws.csv", index=False)
summ = res.groupby(["frac", "trait", "scheme"]).agg(r=("r", "mean"), r_sd=("r", "std"), gain=("gain", "mean"), gain_sd=("gain", "std"),
                                                    gain_max=("gain_max", "mean"), plots_used=("plots_used", "mean"), n_pred=("n_pred", "mean")).reset_index()
summ["plots_used"] = summ.plots_used.round().astype(int); summ["n_pred"] = summ.n_pred.round().astype(int)
summ.to_csv("results_summary/stage4_sampling_curve.csv", index=False)
print(summ[summ.trait == "YLD"].round(3).to_string(index=False))
print(f"done {time.time()-t0:.0f}s")
