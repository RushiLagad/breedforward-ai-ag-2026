"""Stage 2: cache genotypes, tune ridge on a 2007 hold-out, validate 2007 and 2008, all five traits."""
import os
import glob, os, time
import numpy as np, pandas as pd

t0 = time.time()
TRAITS = ["YLD", "MST", "TWT", "ERM", "RTLP", "STLP"]

# ---------- genotype cache ----------
if not os.path.exists("results/G.npy"):
    files = sorted(glob.glob("data/ImputedPopulations*/*.csv"))
    n_rows = 0; cols = None
    for f in files:
        with open(f) as fh:
            hdr = next(fh); n_rows += sum(1 for l in fh if not l.split(",", 1)[0].strip('"').startswith("PID"))
        if cols is None: cols = [c.strip('"') for c in hdr.strip().split(",")[1:]]
    G = np.empty((n_rows, len(cols)), dtype=np.float32); ids = []; r0 = 0
    for f in files:
        pop = os.path.basename(f).replace("_Imputed.csv", "")
        g = pd.read_csv(f, index_col=0, low_memory=False)
        g = g[~g.index.astype(str).str.startswith("PID")]
        G[r0:r0 + len(g)] = g.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32); r0 += len(g)
        ids += [f"{pop}|{str(i).lstrip('0') or '0'}" for i in g.index]
    mu = np.nan_to_num(np.nanmean(G, axis=0)).astype(np.float32)
    nan = np.isnan(G); G[nan] = np.take(mu, np.where(nan)[1]); del nan; G -= mu
    np.save("results/G.npy", G); pd.Series(ids).to_csv("results/G_ids.csv", index=False, header=False)
    print(f"cached G {G.shape} | {time.time()-t0:.0f}s")
G = np.load("results/G.npy", mmap_mode="r"); gidx = pd.Index(pd.read_csv("results/G_ids.csv", header=None)[0])
p = G.shape[1]

# ---------- line means per trait, adjusted for ENV x TESTER ----------
y = pd.read_pickle("results/pheno_env_parents.pkl")
y["TESTER"] = y["TESTER"].fillna("NA")
for t in TRAITS:
    y[t + "_c"] = y[t] - y.groupby(["ENV", "TESTER"])[t].transform("mean")
line = y.groupby(["LINE_ID", "POP", "YEAR", "HG", "P1", "P2", "LINE"]).agg(
    **{t + "_c": (t + "_c", "mean") for t in TRAITS}, n=("YLD", "size")).reset_index()
line["key"] = [s[:-2] if s.endswith(".0") else s for s in line["LINE"]]
line["key"] = [s.lstrip("0") or "0" for s in line["key"]]
line["gkey"] = line["POP"] + "|" + line["key"]
line = line[line["gkey"].isin(gidx)].copy()
line["gi"] = gidx.get_indexer(line["gkey"])
print("lines", len(line), "| per year", line.groupby("YEAR").size().to_dict(), f"| {time.time()-t0:.0f}s")

def xtx(rows, yv):
    A = np.zeros((p, p)); b = np.zeros(p)
    for i in range(0, len(rows), 20000):
        xb = np.asarray(G[rows[i:i+20000]], dtype=np.float64); A += xb.T @ xb; b += xb.T @ yv[i:i+20000]
    return A, b

def parent_gca(tr, te, col):
    par = pd.concat([tr.assign(PARENT=tr.P1), tr.assign(PARENT=tr.P2)]).groupby("PARENT")[col].mean()
    return (te["P1"].map(par).fillna(0).values + te["P2"].map(par).fillna(0).values) / 2

def evaluate(te, pred, col, frac=0.2):
    ok = te[col].notna().values; d = te[ok]; pr = pred[ok]
    r = np.corrcoef(pr, d[col])[0, 1]
    k = int(frac * len(d)); top = d.iloc[np.argsort(-pr)[:k]][col].mean(); best = d.nlargest(k, col)[col].mean(); base = d[col].mean()
    return r, top - base, best - base, len(d)

def run(test_year, lam_grid, tuned=None):
    out = []
    tr = line[line.YEAR < test_year]; te = line[line.YEAR == test_year]
    for t in TRAITS:
        col = t + "_c"
        trt = tr[tr[col].notna()].groupby("gi")[col].mean(); rows = trt.index.values; yv = trt.values
        ym = yv.mean(); A, b = xtx(rows, yv - ym)
        te_s = te.groupby("gi").agg({**{c: "mean" for c in [x + "_c" for x in TRAITS]}, "P1": "first", "P2": "first"}).reset_index()
        Xte = np.asarray(G[te_s.gi.values], dtype=np.float64)
        pg = parent_gca(tr, te_s, col)
        best = None
        lams = lam_grid if tuned is None else [tuned[t]]
        for lam in lams:
            beta = np.linalg.solve(A + lam * np.eye(p), b)
            pm = Xte @ beta + ym
            r_m, g_m, g_max, n = evaluate(te_s, pm, col)
            r_c, g_c, _, _ = evaluate(te_s, pm + pg, col)
            r_p, g_p, _, _ = evaluate(te_s, pg, col)
            row = dict(year=test_year, trait=t, lam=lam, n=n, r_parent=r_p, r_markers=r_m, r_combined=r_c,
                       gain_parent=g_p, gain_markers=g_m, gain_combined=g_c, gain_max=g_max)
            if best is None or r_c > best["r_combined"]: best = row
        out.append(best)
    return pd.DataFrame(out)

grid = [p * (1 - h) / h for h in (0.05, 0.1, 0.2, 0.35, 0.5, 0.7)]
tune = run(2007, grid)
print("\n=== tune on 2007 hold-out (train 2000-2006) ===")
print(tune.round(3).to_string(index=False))
tuned = dict(zip(tune.trait, tune.lam))
res = run(2008, None, tuned)
print("\n=== 2008 hold-out (train 2000-2007), lambda from 2007 ===")
print(res.round(3).to_string(index=False))
pd.concat([tune, res]).to_csv("results_summary/stage2_results.csv", index=False)
print(f"done {time.time()-t0:.0f}s")
