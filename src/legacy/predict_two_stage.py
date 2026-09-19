"""Two-stage: population (sibling) mean + within-population marker model for the Mendelian-sampling part."""
import time, numpy as np, pandas as pd
from sklearn.linear_model import Ridge
t0=time.time()
G=np.load("results/G.npy",mmap_mode="r"); gidx=pd.Index(pd.read_csv("results/G_ids.csv",header=None)[0])
y=pd.read_pickle("results/pheno_env_parents.pkl"); y["TESTER"]=y.TESTER.fillna("NA")
for t in ["YLD","MST","TWT"]: y[t+"_c"]=y[t]-y.groupby(["ENV","TESTER"])[t].transform("mean")
line=y.groupby(["LINE_ID","POP","YEAR","LINE"]).agg(YLD_c=("YLD_c","mean"),MST_c=("MST_c","mean"),TWT_c=("TWT_c","mean")).reset_index()
line["key"]=[s[:-2] if s.endswith(".0") else s for s in line.LINE]; line["key"]=[s.lstrip("0") or "0" for s in line.key]
line["gi"]=gidx.get_indexer(line.POP+"|"+line.key); line=line[line.gi>=0].drop_duplicates("gi")
te=line[line.YEAR==2008].copy(); rng=np.random.default_rng(0); te["half"]=rng.integers(0,2,len(te))
out=[]
for t in ["YLD","MST","TWT"]:
    col=t+"_c"; preds=[]
    for pop,d in te.groupby("POP"):
        kn=d[(d.half==0)&d[col].notna()]; un=d[d.half==1]
        if len(un)==0: continue
        mu=kn[col].mean() if len(kn) else 0.0
        if len(kn)>=30:
            X=np.asarray(G[kn.gi.values],dtype=np.float64); keep=X.std(0)>0; X=X[:,keep]
            m=Ridge(alpha=len(kn)*2.0).fit(X,kn[col].values-mu)          # within-pop deviations
            dev=m.predict(np.asarray(G[un.gi.values],dtype=np.float64)[:,keep])
        else: dev=np.zeros(len(un))
        preds.append(pd.DataFrame({"gi":un.gi.values,"sib":mu,"two_stage":mu+dev,"n_known":len(kn)}))
    P=pd.concat(preds).merge(te[["gi",col]],on="gi").dropna()
    for name in ["sib","two_stage"]:
        r=np.corrcoef(P[name],P[col])[0,1]; k=int(0.2*len(P)); g=P.nlargest(k,name)[col].mean()-P[col].mean(); gm=P.nlargest(k,col)[col].mean()-P[col].mean()
        out.append(dict(trait=t,scheme=name,r=r,gain=g,gain_max=gm)); print(f"{t} {name:10s} r={r:.3f} gain {g:+.2f} of {gm:+.2f}")
    big=P[P.n_known>=30]; print(f"   pops with >=30 known sibs: {big.gi.nunique()} lines, two_stage r={np.corrcoef(big.two_stage,big[col])[0,1]:.3f} vs sib r={np.corrcoef(big.sib,big[col])[0,1]:.3f}")
pd.DataFrame(out).to_csv("results_summary/stage3b_two_stage.csv",index=False); print(f"done {time.time()-t0:.0f}s")
