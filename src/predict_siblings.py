"""Stage 3: the sibling stages of the plot-cut scenario.

Timeline this stage simulates (not a January decision):
  January 2008   decide how to spend the plots: a share of EVERY family is planted (here: half).
  After harvest  the sampled siblings are phenotyped; rank the UNTESTED siblings and decide which advance.
The held-out lines' real 2008 yields are the only thing the models never see; they score the decision.

(a) four prediction schemes on the held-out half, (b) breeder's equation and plots saved,
(c) the ranked advancement list on five criteria -> results/advance2008.csv

Split is stratified by family (>= 1 known and >= 1 held out per family) and centering uses training
plots only (see src/common.py). Ranking ties break on LINE_ID.
"""
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from common import (TRAITS, load_plots, genotype_index, lines_2008, split_families, centered_lines,
                    attach_genotypes, rank_desc, top_k_gain)

t0 = time.time()
G, gidx = genotype_index(); p = G.shape[1]
y = load_plots()
LAM = {"YLD": 26199, "MST": 5406, "TWT": 11644, "ERM": 26199, "RTLP": 11644, "STLP": 11644}

# ---- split first, then centre on training plots only ----
te = lines_2008(y, gidx)
rng = np.random.default_rng(0)
te["known"] = split_families(te, 0.5, rng)
heldout = set(te.loc[~te.known, "LINE_ID"])
line = attach_genotypes(centered_lines(y, heldout, TRAITS), gidx)
known = line[line.LINE_ID.isin(te.loc[te.known, "LINE_ID"])].copy()
unknown = line[line.LINE_ID.isin(heldout)].sort_values("gi").copy()
hist = line[line.YEAR < 2008]
print(f"2008: {len(known)} lines phenotyped (known siblings), {len(unknown)} held out, "
      f"{te.POP.nunique()} families, {int((te.groupby('POP').known.sum() == 0).sum())} single-line families with no sample | {time.time()-t0:.0f}s")


def xtx(rows, yv):
    A = np.zeros((p, p)); b = np.zeros(p)
    for i in range(0, len(rows), 20000):
        xb = np.asarray(G[rows[i:i+20000]], dtype=np.float64); A += xb.T @ xb; b += xb.T @ yv[i:i+20000]
    return A, b


def fit_predict(tr, tst, col):
    trt = tr[tr[col].notna()].sort_values("gi"); yv = trt[col].values; ym = yv.mean()
    A, b = xtx(trt.gi.values, yv - ym); beta = np.linalg.solve(A + LAM[col[:-2]] * np.eye(p), b)
    return np.asarray(G[tst.gi.values], dtype=np.float64) @ beta + ym


def score(tst, pred, col, frac=0.2):
    d = tst.assign(_p=pred); d = d[d[col].notna()]
    r = np.corrcoef(d._p, d[col])[0, 1]
    gain, gmax, _ = top_k_gain(d, "_p", col, frac)
    return r, gain, gmax


def two_stage(col, min_known=30):
    """Family mean of the phenotyped siblings + within-family ridge on marker deviations.
    Global marker model (scheme B) only for a family with no phenotyped sibling."""
    mk = fit_predict(pd.concat([hist, known]), unknown, col)
    sib = pd.Series(np.nan, index=unknown.index); two = pd.Series(np.nan, index=unknown.index)
    for pop, un in unknown.groupby("POP"):
        kn = known[(known.POP == pop) & known[col].notna()]
        if len(kn) == 0: continue
        mu = kn[col].mean(); dev = np.zeros(len(un))
        if len(kn) >= min_known:
            X = np.asarray(G[kn.gi.values], dtype=np.float64); keep = X.std(0) > 0
            m = Ridge(alpha=len(kn) * 2.0).fit(X[:, keep], kn[col].values - mu)
            dev = m.predict(np.asarray(G[un.gi.values], dtype=np.float64)[:, keep])
        sib.loc[un.index] = mu; two.loc[un.index] = mu + dev
    return mk, sib.fillna(pd.Series(mk, index=unknown.index)).values, two.fillna(pd.Series(mk, index=unknown.index)).values


rows, rows_b = [], []
P = {}
for t in ["YLD", "MST", "TWT", "ERM"]:
    col = t + "_c"
    pa = fit_predict(hist, unknown, col); ra = score(unknown, pa, col)              # A: pure new year
    pb, pc, pd_ = two_stage(col)                                                    # B: markers + siblings pooled
    rb = score(unknown, pb, col); rc = score(unknown, pc, col); rd = score(unknown, pd_, col)   # C: sibling mean; D: two-stage
    P[t] = dict(new=pa, aug=pb, sib=pc, two=pd_)
    if t != "ERM":
        rows.append(dict(trait=t, r_newyear=ra[0], r_sibmean=rc[0], r_sib_augmented=rb[0], gain_newyear=ra[1], gain_sibmean=rc[1], gain_sib_augmented=rb[1], gain_max=ra[2]))
        rows_b += [dict(trait=t, scheme="sib", r=rc[0], gain=rc[1], gain_max=rc[2]), dict(trait=t, scheme="two_stage", r=rd[0], gain=rd[1], gain_max=rd[2])]
    print(f"{t}: new-year r={ra[0]:.3f} | markers+siblings r={rb[0]:.3f} | sibling-mean r={rc[0]:.3f} | two-stage r={rd[0]:.3f} | gain {ra[1]:+.2f} / {rb[1]:+.2f} / {rc[1]:+.2f} / {rd[1]:+.2f} of {ra[2]:+.2f} | {time.time()-t0:.0f}s")
pd.DataFrame(rows).to_csv("results_summary/stage3_schemes.csv", index=False)
pd.DataFrame(rows_b).to_csv("results_summary/stage3b_two_stage.csv", index=False)

# ---- breeder's equation ----
d = unknown[unknown.YLD_c.notna()]
sd_obs = d.YLD_c.std(); rel = 0.46; sd_true = sd_obs * np.sqrt(rel); i20 = 1.40
print(f"\nyield line-mean sd {sd_obs:.2f} bu/ac, reliability {rel}, true genetic sd ~ {sd_true:.2f} bu/ac")
for r in [0.14, 0.25, 0.35, 0.5]: print(f"  breeder's equation, top 20%, r={r:.2f}: {i20*r*sd_true:+.2f} bu/ac")
plots = int(y[y.YEAR == 2008].shape[0]); lines08 = y[y.YEAR == 2008].LINE_ID.nunique()
plots_known = int(known.n.sum())
print(f"2008 as tested: {lines08:,} lines x {plots/lines08:.1f} plots = {plots:,} plots. Sampling half of each family used {plots_known:,} of them.")

# ---- advancement list ----
# Yield: the sibling mean is the empirical winner for yield alone (scheme C >= D); the within-family marker
# term earns its keep on moisture and test weight. Both yield variants are scored on the full index below.
# Rule: if their realised index gains are within 0.1 bu/ac, use two-stage, because it can rank siblings
# within a family and keeps many more families in the advancement set; otherwise use the better one.
# Both outcomes and the rule are written to results_summary/stage3_index_choice.csv.
adv = unknown[["LINE_ID", "POP", "HG", "P1", "P2"]].copy()
adv["sib_n"] = adv.POP.map(known.groupby("POP").size()).fillna(0).astype(int)
adv["pred_yld_new"] = P["YLD"]["new"]; adv["pred_yld_aug"] = P["YLD"]["aug"]
adv["pred_yld_sib"] = P["YLD"]["sib"]; adv["pred_yld_two"] = P["YLD"]["two"]
for t in ["MST", "TWT", "ERM"]:
    adv["pred_" + t.lower()] = P[t]["two"]
lodg = known.assign(lodg=known.RTLP_c.fillna(0) + known.STLP_c.fillna(0)).groupby("POP").lodg.mean()
adv["pop_lodging_obs"] = adv.POP.map(lodg).fillna(0)
adv["obs_yld_2008"] = unknown.set_index("LINE_ID").loc[adv.LINE_ID, "YLD_c"].values
z = lambda s: (s - s.mean()) / s.std()
W = {"yld": 0.5, "pred_twt": 0.1, "pred_mst": -0.15, "pred_erm": -0.05, "pop_lodging_obs": -0.2}
choice = []
for name, ycol in [("sibling mean", "pred_yld_sib"), ("two-stage", "pred_yld_two")]:
    idx = sum(w * z(adv[ycol if c == "yld" else c]) for c, w in W.items())
    tmp = adv.assign(index=idx)
    g, gmax, k = top_k_gain(tmp, "index", "obs_yld_2008")
    top = rank_desc(tmp, "index").head(k)
    choice.append(dict(yield_predictor=name, r_yield=np.corrcoef(adv[ycol], adv.obs_yld_2008)[0, 1], index_gain=g, oracle=gmax,
                       families_in_top20=top.POP.nunique(), yield_only_gain=top_k_gain(adv, ycol, "obs_yld_2008")[0]))
ch = pd.DataFrame(choice); ch.to_csv("results_summary/stage3_index_choice.csv", index=False)
print("\nindex on each yield predictor:\n" + ch.round(3).to_string(index=False))
diff = ch.iloc[0].index_gain - ch.iloc[1].index_gain
use = "pred_yld_two" if abs(diff) <= 0.1 else ("pred_yld_sib" if diff > 0 else "pred_yld_two")
ch["used"] = ch.yield_predictor.eq("two-stage" if use == "pred_yld_two" else "sibling mean"); ch["rule"] = "two-stage if index gains within 0.1 bu/ac, else the higher"
ch.to_csv("results_summary/stage3_index_choice.csv", index=False)
adv["pred_yld"] = adv[use]
adv["index"] = sum(w * z(adv[c if c != "yld" else "pred_yld"]) for c, w in W.items())
adv = rank_desc(adv, "index"); adv["rank"] = np.arange(1, len(adv) + 1); adv["advance_top20"] = adv["rank"] <= int(0.2 * len(adv))
adv.round(4).to_csv("results/advance2008.csv", index=False)
top = adv[adv.advance_top20]
print(f"\nadvancement list uses {use} for yield. index top-20% realised yield gain: {top.obs_yld_2008.mean()-adv.obs_yld_2008.mean():+.4f} bu/ac | "
      f"r(pred_yld, obs) = {np.corrcoef(adv.pred_yld, adv.obs_yld_2008)[0,1]:.3f}")
print(f"advance list: {len(adv)} lines, {len(top)} flagged, HG split {top.HG.value_counts().to_dict()}, families represented {top.POP.nunique()}")
print(f"done {time.time()-t0:.0f}s")
