"""Stage 5: index-weight sensitivity for the 2008 advancement list.
How much does the flagged top-20% set change when the weights change, and what does each weight buy in
realised 2008 yield, predicted moisture and test weight, and observed family lodging?

Differences are reported in z units (difference of means divided by the candidate sd) so the columns
are comparable. Ties in the index break on LINE_ID. Outputs:
  results_summary/stage5_weight_sensitivity.csv   the named weightings
  results_summary/stage5_random_sweep.csv          summary of the 500 random weightings
"""
import numpy as np
import pandas as pd
from common import rank_desc

adv = pd.read_csv("results/advance2008.csv", dtype={"LINE_ID": str, "POP": str})
z = lambda s: (s - s.mean()) / s.std()
cols = {"yld": "pred_yld", "twt": "pred_twt", "mst": "pred_mst", "erm": "pred_erm", "lodg": "pop_lodging_obs"}
Z = {k: z(adv[c]) for k, c in cols.items()}
k = int(0.2 * len(adv))
sd = {c: adv[c].std() for c in ["pred_mst", "pred_twt", "pop_lodging_obs"]}


def score(w, name):
    d = adv.assign(_i=sum(w.get(t, 0) * Z[t] for t in cols))
    top = rank_desc(d, "_i").head(k)
    return dict(scheme=name, **{f"w_{t}": w.get(t, 0) for t in cols},
                yld_gain=top.obs_yld_2008.mean() - adv.obs_yld_2008.mean(),
                mst_pred_z=(top.pred_mst.mean() - adv.pred_mst.mean()) / sd["pred_mst"],
                twt_pred_z=(top.pred_twt.mean() - adv.pred_twt.mean()) / sd["pred_twt"],
                lodg_obs_z=(top.pop_lodging_obs.mean() - adv.pop_lodging_obs.mean()) / sd["pop_lodging_obs"],
                families=top.POP.nunique(), top_set=set(top.LINE_ID))


base = {"yld": 0.5, "twt": 0.1, "mst": -0.15, "erm": -0.05, "lodg": -0.2}
schemes = [
    ("yield only", {"yld": 1.0}),
    ("default (0.5/0.1/-0.15/-0.05/-0.2)", base),
    ("yield-heavy (0.7, others halved)", {"yld": 0.7, "twt": 0.05, "mst": -0.08, "erm": -0.03, "lodg": -0.1}),
    ("moisture-heavy (mst -0.35)", {**base, "mst": -0.35}),
    ("lodging-heavy (lodg -0.4)", {**base, "lodg": -0.4}),
    ("equal weights (all 0.2, signs kept)", {"yld": 0.2, "twt": 0.2, "mst": -0.2, "erm": -0.2, "lodg": -0.2}),
    ("no lodging term", {"yld": 0.5, "twt": 0.1, "mst": -0.15, "erm": -0.05}),
]
rows = [score(w, n) for n, w in schemes]
ref = rows[1]["top_set"]
for r in rows: r["overlap_with_default"] = len(r["top_set"] & ref) / k
out = pd.DataFrame(rows).drop(columns="top_set")
pd.set_option("display.width", 220)
print(out.round(3).to_string(index=False))
out.round(4).to_csv("results_summary/stage5_weight_sensitivity.csv", index=False)

# random-weight sweep: how stable is the flagged set under any reasonable weighting?
rng = np.random.default_rng(0)
sw = []
for _ in range(500):
    w = {"yld": rng.uniform(0.3, 0.8), "twt": rng.uniform(0, 0.25), "mst": -rng.uniform(0, 0.35), "erm": -rng.uniform(0, 0.15), "lodg": -rng.uniform(0, 0.4)}
    r = score(w, "random"); sw.append(dict(**{kk: v for kk, v in r.items() if kk != "top_set"}, overlap_with_default=len(r["top_set"] & ref) / k))
sw = pd.DataFrame(sw)
q = lambda s: (s.median(), s.quantile(0.05), s.quantile(0.95))
summary = pd.DataFrame([dict(metric=m, median=q(sw[m])[0], p05=q(sw[m])[1], p95=q(sw[m])[2]) for m in ["overlap_with_default", "yld_gain", "mst_pred_z", "lodg_obs_z", "families"]])
summary["n_weightings"] = 500; summary["ranges"] = "yld 0.3-0.8, twt 0-0.25, mst 0 to -0.35, erm 0 to -0.15, lodg 0 to -0.4"
summary.round(4).to_csv("results_summary/stage5_random_sweep.csv", index=False)
o, g = q(sw.overlap_with_default), q(sw.yld_gain)
print(f"\n500 random weightings: overlap with default top-20% median {o[0]:.2f} (5th-95th {o[1]:.2f}-{o[2]:.2f}); "
      f"realised yield gain median {g[0]:+.2f} bu/ac (5th-95th {g[1]:+.2f} to {g[2]:+.2f})")
