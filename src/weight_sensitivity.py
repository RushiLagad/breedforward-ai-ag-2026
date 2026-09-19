"""Index-weight sensitivity for the 2008 advancement list.
How much does the flagged top-20% set change when the weights change, and what does each weight buy
in realised 2008 yield, moisture, test weight and observed family lodging?"""
import numpy as np, pandas as pd
adv = pd.read_csv("results/advance2008.csv", dtype={"LINE_ID": str, "POP": str})
z = lambda s: (s - s.mean()) / s.std()
cols = {"yld": "pred_yld_aug", "twt": "pred_twt", "mst": "pred_mst", "erm": "pred_erm", "lodg": "pop_lodging_obs"}
Z = {k: z(adv[c]) for k, c in cols.items()}
k = int(0.2 * len(adv))

# observed 2008 outcomes for scoring (yield observed; other traits use predictions since we only stored obs yield)
def score(w, name):
    idx = sum(w[t] * Z[t] for t in w)
    top = adv.iloc[np.argsort(-idx.values)[:k]]
    return dict(scheme=name, **{f"w_{t}": w.get(t, 0) for t in cols},
                yld_gain=top.obs_yld_2008.mean() - adv.obs_yld_2008.mean(),
                mst_pred=top.pred_mst.mean() - adv.pred_mst.mean(),
                twt_pred=top.pred_twt.mean() - adv.pred_twt.mean(),
                lodg_obs=top.pop_lodging_obs.mean() - adv.pop_lodging_obs.mean(),
                top_set=set(top.LINE_ID))

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
pd.set_option("display.width", 200)
print(out.round(3).to_string(index=False))
out.round(4).to_csv("results_summary/stage5_weight_sensitivity.csv", index=False)

# random-weight sweep: how stable is the flagged set under any reasonable weighting?
rng = np.random.default_rng(0); ov = []; yg = []
for _ in range(500):
    w = {"yld": rng.uniform(0.3, 0.8), "twt": rng.uniform(0, 0.2), "mst": -rng.uniform(0, 0.35), "erm": -rng.uniform(0, 0.15), "lodg": -rng.uniform(0, 0.4)}
    r = score(w, "rand"); ov.append(len(r["top_set"] & ref) / k); yg.append(r["yld_gain"])
print(f"\n500 random weightings (yield 0.3-0.8, others within plausible ranges): overlap with default top-20% "
      f"median {np.median(ov):.2f} (5th-95th {np.percentile(ov,5):.2f}-{np.percentile(ov,95):.2f}); "
      f"realised yield gain median {np.median(yg):+.2f} bu/ac (5th-95th {np.percentile(yg,5):+.2f} to {np.percentile(yg,95):+.2f})")
