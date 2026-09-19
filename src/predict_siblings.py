"""Stage 3: (a) sibling-augmented prediction of 2008 (half of each 2008 population phenotyped),
(b) breeder's equation / plots saved, (c) ranked 2008 advancement list on five criteria."""
import time, numpy as np, pandas as pd
t0 = time.time()
TRAITS = ["YLD", "MST", "TWT", "ERM", "RTLP", "STLP"]
G = np.load("results/G.npy", mmap_mode="r"); gidx = pd.Index(pd.read_csv("results/G_ids.csv", header=None)[0]); p = G.shape[1]
y = pd.read_pickle("results/pheno_env_parents.pkl"); y["TESTER"] = y["TESTER"].fillna("NA")
for t in TRAITS: y[t + "_c"] = y[t] - y.groupby(["ENV", "TESTER"])[t].transform("mean")
line = y.groupby(["LINE_ID", "POP", "YEAR", "HG", "P1", "P2", "LINE"]).agg(**{t + "_c": (t + "_c", "mean") for t in TRAITS}, n=("YLD", "size")).reset_index()
line["key"] = [s[:-2] if s.endswith(".0") else s for s in line["LINE"]]; line["key"] = [s.lstrip("0") or "0" for s in line["key"]]
line["gi"] = gidx.get_indexer(line["POP"] + "|" + line["key"]); line = line[line.gi >= 0].drop_duplicates("gi").copy()
LAM = {"YLD": 26199, "MST": 5406, "TWT": 11644, "ERM": 26199, "RTLP": 11644, "STLP": 11644}

def xtx(rows, yv):
    A = np.zeros((p, p)); b = np.zeros(p)
    for i in range(0, len(rows), 20000):
        xb = np.asarray(G[rows[i:i+20000]], dtype=np.float64); A += xb.T @ xb; b += xb.T @ yv[i:i+20000]
    return A, b

def fit_predict(tr, te, col):
    trt = tr[tr[col].notna()].sort_values("gi"); yv = trt[col].values; ym = yv.mean()
    A, b = xtx(trt.gi.values, yv - ym); beta = np.linalg.solve(A + LAM[col[:-2]] * np.eye(p), b)
    return np.asarray(G[te.gi.values], dtype=np.float64) @ beta + ym

def score(te, pred, col, frac=0.2):
    ok = te[col].notna().values; d = te[ok]; pr = pred[ok]
    r = np.corrcoef(pr, d[col])[0, 1]; k = int(frac * len(d))
    return r, d.iloc[np.argsort(-pr)[:k]][col].mean() - d[col].mean(), d.nlargest(k, col)[col].mean() - d[col].mean()

rng = np.random.default_rng(0)
te08 = line[line.YEAR == 2008].copy(); te08["half"] = rng.integers(0, 2, len(te08))
known = te08[te08.half == 0]; unknown = te08[te08.half == 1].sort_values("gi")
print(f"2008: {len(known)} lines phenotyped (known siblings), {len(unknown)} to predict | {time.time()-t0:.0f}s")

rows = []
for t in ["YLD", "MST", "TWT"]:
    col = t + "_c"
    # scheme A: pure new year (train < 2008)
    pa = fit_predict(line[line.YEAR < 2008], unknown, col); ra = score(unknown, pa, col)
    # scheme B: new year + half of each 2008 population phenotyped (the scenario's "related lines")
    pb = fit_predict(pd.concat([line[line.YEAR < 2008], known]), unknown, col); rb = score(unknown, pb, col)
    # scheme C: sibling mean only (no markers): predict each unknown line by the mean of its known siblings
    sib = known.groupby("POP")[col].mean(); pc = unknown["POP"].map(sib).fillna(0).values; rc = score(unknown, pc, col)
    # scheme D: B + within-population ridge on siblings only (local model), averaged with B
    rows.append(dict(trait=t, r_newyear=ra[0], r_sibmean=rc[0], r_sib_augmented=rb[0], gain_newyear=ra[1], gain_sibmean=rc[1], gain_sib_augmented=rb[1], gain_max=ra[2]))
    print(f"{t}: new-year r={ra[0]:.3f} | sibling-mean r={rc[0]:.3f} | markers+siblings r={rb[0]:.3f} | gain {ra[1]:+.2f} / {rc[1]:+.2f} / {rb[1]:+.2f} of {ra[2]:+.2f} | {time.time()-t0:.0f}s")
    if t == "YLD": unknown["pred_yld_aug"] = pb; unknown["pred_yld_new"] = pa
res = pd.DataFrame(rows); res.to_csv("results_summary/stage3_schemes.csv", index=False)

# --- breeder's equation ---
d = unknown[unknown.YLD_c.notna()]
sd_obs = d.YLD_c.std(); rel = 0.46; sd_true = sd_obs * np.sqrt(rel)
i20 = 1.40  # selection intensity for top 20%
print(f"\nyield line-mean sd {sd_obs:.2f} bu/ac, reliability {rel}, true genetic sd ~ {sd_true:.2f} bu/ac")
print("breeder's equation, top 20% advanced, expected gain = i * r * sd_true (bu/ac):")
for r in [0.14, 0.25, 0.35, 0.5]: print(f"  r={r:.2f}: {i20*r*sd_true:+.2f} bu/ac")
plots = int(y[y.YEAR == 2008].shape[0]); lines08 = y[y.YEAR == 2008].LINE_ID.nunique()
print(f"2008 as tested: {lines08:,} lines x {plots/lines08:.1f} plots = {plots:,} plots. Advancing only the predicted top 20% saves ~{0.8*plots:,.0f} plots.")

# --- ranked advancement list on five criteria ---
# The predictor is the one the schemes above recommend: the mean of the phenotyped siblings, plus a
# within-family marker model for the Mendelian-sampling part (fit on families with >= 30 phenotyped
# siblings; see src/predict_two_stage.py). The global marker model (scheme B) is used only for a family
# with no phenotyped sibling. Lodging is not predictable here and enters as the observed family mean.
# pred_yld_aug (scheme B) and pred_yld_new (scheme A) are kept for reference.
from sklearn.linear_model import Ridge
def two_stage(col):
    mk = fit_predict(pd.concat([line[line.YEAR < 2008], known]), unknown, col)   # fallback: global markers
    out = pd.Series(mk, index=unknown.index)
    for pop, un in unknown.groupby("POP"):
        kn = known[(known.POP == pop) & known[col].notna()]
        if len(kn) == 0: continue
        mu = kn[col].mean(); dev = np.zeros(len(un))
        if len(kn) >= 30:
            X = np.asarray(G[kn.gi.values], dtype=np.float64); keep = X.std(0) > 0
            m = Ridge(alpha=len(kn) * 2.0).fit(X[:, keep], kn[col].values - mu)
            dev = m.predict(np.asarray(G[un.gi.values], dtype=np.float64)[:, keep])
        out.loc[un.index] = mu + dev
    return out.values
adv = unknown[["LINE_ID", "POP", "HG", "P1", "P2", "pred_yld_aug", "pred_yld_new"]].copy()
adv["sib_n"] = adv.POP.map(known.groupby("POP").size()).fillna(0).astype(int)
for t in ["YLD", "MST", "TWT", "ERM"]:
    adv["pred_" + t.lower()] = two_stage(t + "_c")
print(f"\nadvancement predictor: sibling mean + within-family markers; global-marker fallback for {int((adv.sib_n == 0).sum())} lines in {adv[adv.sib_n == 0].POP.nunique()} families with no phenotyped sibling")
lodg = known.assign(lodg=known.RTLP_c.fillna(0) + known.STLP_c.fillna(0)).groupby("POP").lodg.mean()
adv["pop_lodging_obs"] = adv.POP.map(lodg).fillna(0)
z = lambda s: (s - s.mean()) / s.std()
W = {"pred_yld": 0.5, "pred_twt": 0.1, "pred_mst": -0.15, "pred_erm": -0.05, "pop_lodging_obs": -0.2}
adv["index"] = sum(w * z(adv[c]) for c, w in W.items())
adv = adv.sort_values("index", ascending=False); adv["rank"] = np.arange(1, len(adv) + 1); adv["advance_top20"] = adv["rank"] <= int(0.2 * len(adv))
adv["obs_yld_2008"] = unknown.set_index("LINE_ID").loc[adv.LINE_ID, "YLD_c"].values
adv.round(3).to_csv("results/advance2008.csv", index=False)
top = adv[adv.advance_top20]; print(f"\nindex top-20% realised yield gain: {top.obs_yld_2008.mean()-adv.obs_yld_2008.mean():+.2f} bu/ac | yield-only top-20%: {adv.nlargest(len(top),'pred_yld').obs_yld_2008.mean()-adv.obs_yld_2008.mean():+.2f} | r(pred_yld, obs) = {np.corrcoef(adv.pred_yld, adv.obs_yld_2008)[0,1]:.3f}")
print(f"advance list: {len(adv)} lines, {top.shape[0]} flagged, HG split {top.HG.value_counts().to_dict()}, pops represented {top.POP.nunique()}")
print(f"done {time.time()-t0:.0f}s")
