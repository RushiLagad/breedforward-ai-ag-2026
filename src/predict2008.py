"""Leave-2008-out genomic prediction across all populations on the shared 2,911-SNP panel.

Stage 1: line BLUE = mean of yield centered within ENV x TESTER (removes env, tester, env x tester).
Stage 2: ridge on markers, train years < 2008, predict 2008 lines. Baselines: population mean of
training lines (0 for new pops), parent GCA from training years.
Evaluate on 2008 observed line means: overall r, within-population r, and top-20% selection gain.
"""
import os
import glob, sys, time
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge

t0 = time.time()
y = pd.read_pickle("results/pheno_env_parents.pkl").dropna(subset=["YLD"]).copy()
# stage 1: adjust for environment x tester cell (keeps line + population + line x env noise)
y["TESTER"] = y["TESTER"].fillna("NA")
y["yc"] = y["YLD"] - y.groupby(["ENV", "TESTER"])["YLD"].transform("mean")
line = y.groupby(["LINE_ID", "POP", "YEAR", "HG", "P1", "P2", "LINE"]).agg(yc=("yc", "mean"), n=("yc", "size")).reset_index()
# C2 file stores LINE as "12.0" and LINE_UNIQUE_ID as "C2.1.12.0": strip the float suffix, then leading zeros
line["key"] = [s[:-2] if s.endswith(".0") else s for s in line["LINE"]]
line["key"] = [s.lstrip("0") or "0" for s in line["key"]]
print("lines", len(line), "| 2008:", (line.YEAR == 2008).sum(), f"| {time.time()-t0:.0f}s")

# --- load genotypes into one preallocated float32 array (memory-lean) ---
files = sorted(glob.glob("data/ImputedPopulations*/*.csv"))
# pass 1: count rows and fix column order
n_rows = 0; cols = None
for f in files:
    with open(f) as fh:
        hdr = next(fh); n = sum(1 for l in fh if not l.split(",",1)[0].strip('"').startswith("PID"))
    n_rows += n
    if cols is None: cols = hdr.strip().split(",")[1:]
p = len(cols); G = np.empty((n_rows, p), dtype=np.float32); ids = []
r0 = 0
for f in files:
    pop = os.path.basename(f).replace("_Imputed.csv", "")
    g = pd.read_csv(f, index_col=0, low_memory=False)
    assert list(g.columns) == [c.strip('"') for c in cols]
    g = g[~g.index.astype(str).str.startswith("PID")]
    vals = g.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    G[r0:r0+len(g)] = vals; r0 += len(g)
    ids += [f"{pop}|{str(i).lstrip('0') or '0'}" for i in g.index]
    del g, vals
print("genotype matrix", G.shape, f"| {time.time()-t0:.0f}s")
mu = np.nan_to_num(np.nanmean(G, axis=0)).astype(np.float32)
nan = np.isnan(G); G[nan] = np.take(mu, np.where(nan)[1]); del nan
G -= mu
gidx = pd.Index(ids)

line["gkey"] = line["POP"] + "|" + line["key"]
line = line[line["gkey"].isin(gidx)].copy()
print("lines with genotypes", len(line), "| 2008:", (line.YEAR == 2008).sum())

tr = line[line.YEAR < 2008]; te = line[line.YEAR == 2008]
Xtr = G[gidx.get_indexer(tr.gkey)]; Xte = G[gidx.get_indexer(te.gkey)]; del G
ytr = tr["yc"].values; yte = te["yc"].values

# --- model 1: ridge on markers (GBLUP-equivalent), lambda from marker count and h2 ---
p = Xtr.shape[1]; h2 = 0.45
lam = p * (1 - h2) / h2
ym = ytr.mean()
XtX = np.zeros((p, p)); Xty = np.zeros(p)
for i in range(0, len(Xtr), 20000):
    xb = Xtr[i:i+20000].astype(np.float64); XtX += xb.T @ xb; Xty += xb.T @ (ytr[i:i+20000] - ym)
beta = np.linalg.solve(XtX + lam * np.eye(p), Xty)
pred_g = Xte.astype(np.float64) @ beta + ym
print(f"ridge solved | lambda {lam:.0f} | {time.time()-t0:.0f}s")

# --- baselines ---
pop_mean = tr.groupby("POP")["yc"].mean()
pred_pop = te["POP"].map(pop_mean).fillna(0).values      # new pops -> 0
par = pd.concat([tr.assign(PARENT=tr.P1), tr.assign(PARENT=tr.P2)]).groupby("PARENT")["yc"].mean()
pred_par = (te["P1"].map(par).fillna(0).values + te["P2"].map(par).fillna(0).values) / 2
pred_gp = pred_g + pred_par

def report(name, pred):
    r = np.corrcoef(pred, yte)[0, 1]
    d = te.assign(pred=pred)
    within = d.groupby("POP").apply(lambda g: np.corrcoef(g.pred, g.yc)[0, 1] if len(g) > 20 else np.nan).dropna()
    k = int(0.2 * len(d)); top = d.nlargest(k, "pred")["yc"].mean(); rnd = d["yc"].mean(); best = d.nlargest(k, "yc")["yc"].mean()
    print(f"{name:22s} r_overall={r:.3f}  r_within_pop(median)={within.median():.3f}  "
          f"top20% gain={top-rnd:+.2f} bu/ac (oracle {best-rnd:+.2f})  realised {100*(top-rnd)/(best-rnd):.0f}% of max")
    return d

print("\n=== 2008 hold-out, yield (env x tester centred), n =", len(te), "===")
report("population mean", pred_pop)
report("parent GCA", pred_par)
report("markers (ridge)", pred_g)
d = report("markers + parent GCA", pred_gp)
d[["LINE_ID", "POP", "HG", "yc", "n", "pred"]].to_csv("results/pred2008.csv", index=False)
np.save("results/beta_markers.npy", beta)
print(f"done {time.time()-t0:.0f}s")
