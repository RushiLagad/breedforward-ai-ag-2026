"""Clean build: both heterotic groups + environment, with flowering-window stress covariates."""
import os; os.makedirs("results", exist_ok=True)
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

DATA = "data/Simplified Hackathon Dataset V3"
C1 = f"{DATA}/C1_Phenotype_Data_V2.csv"
C2 = f"{DATA}/C2_Phenotype_Data_V2.csv"
ENV = f"{DATA}/environmental_features.csv"

KEEP = {"shorthand_x": "POP", "YEAR_x": "YEAR", "LOC": "LOC", "LATITUDE": "LAT", "LONGITUDE": "LON",
        "LINE_UNIQUE_ID": "LINE_ID", "LINE": "LINE", "GENERATION_NAME": "GEN", "GERMPLASM_ID_TESTER": "TESTER",
        "CLUSTER": "HG", "SET": "SET", "YLD_BE": "YLD", "MST": "MST", "TWT": "TWT", "PHT": "PHT",
        "EHT": "EHT", "ERM": "ERM", "RTLP": "RTLP", "STLP": "STLP"}

def load(p):
    d = pd.read_csv(p, usecols=list(KEEP), low_memory=False,
                    dtype={"LINE_UNIQUE_ID": str, "LINE": str, "SET": str, "GERMPLASM_ID_TESTER": str})
    return d.rename(columns=KEEP)

ph = pd.concat([load(C1), load(C2)], ignore_index=True)
ph["ENV"] = ph["YEAR"].astype(str) + "_" + ph["LOC"]
ph["TESTER"] = ph["TESTER"].str.replace(r"\.0$", "", regex=True)

env = pd.read_csv(ENV)
assert not env.duplicated(["YEAR", "LOC"]).any()
# --- environment covariates: season totals + flowering/grain-fill window (Jul-Aug) stress ---
env["PRCP_SEASON"] = env[[f"X{m:02d}_PRCP" for m in range(4, 11)]].sum(axis=1)
env["PRCP_JA"] = env["X07_PRCP"] + env["X08_PRCP"]
env["CLDD_JA"] = env["X07_CLDD"] + env["X08_CLDD"]          # heat during flowering + grain fill
env["TAVG_JA"] = (env["X07_TAVG"] + env["X08_TAVG"]) / 2
env["CLAY_TOP"] = env[["clay_0_5cm", "clay_5_15cm", "clay_15_30cm"]].mean(axis=1) / 10   # %
env["SAND_TOP"] = env[["sand_0_5cm", "sand_5_15cm", "sand_15_30cm"]].mean(axis=1) / 10
env["SOC_TOP"] = env[["soc_0_5cm", "soc_5_15cm"]].mean(axis=1) * 10 / 1000               # g/kg
env["PH_TOP"] = env["phh2o_0_5cm"] / 10

# env fingerprint: PCA on all weather+soil covariates (standardized), unique environments
covs = [c for c in env.columns if c.startswith("X") or "_cm" in c]
Z = StandardScaler().fit_transform(env[covs])
pca = PCA(n_components=5, random_state=0).fit(Z)
pcs = pca.transform(Z)
for i in range(5): env[f"ENV_PC{i+1}"] = pcs[:, i]
print("env PCA explained:", pca.explained_variance_ratio_.round(3), "cum", pca.explained_variance_ratio_.cumsum()[-1].round(3))

# regime v1: season precip tertiles (baseline, what everyone does)
q = env["PRCP_SEASON"].quantile([1/3, 2/3]).values
env["REGIME_PRCP"] = pd.cut(env["PRCP_SEASON"], [-np.inf, *q, np.inf], labels=["Dry", "Normal", "Wet"])
# regime v2: flowering-window water/heat balance on unique environments (weather only; soil stays a covariate)
z = lambda x: (x - x.mean()) / x.std()
env["STRESS_IDX"] = z(env["PRCP_JA"]) - z(env["CLDD_JA"])       # high = wet & cool Jul-Aug, low = dry & hot
q2 = env["STRESS_IDX"].quantile([1/3, 2/3]).values
env["REGIME_STRESS"] = pd.cut(env["STRESS_IDX"], [-np.inf, *q2, np.inf], labels=["HotDry", "Moderate", "CoolWet"])
print("stress regimes:\n", env.groupby("REGIME_STRESS", observed=True)[["PRCP_JA", "CLDD_JA", "TAVG_JA", "PRCP_SEASON"]].mean().round(1))
print("envs per regime:", env["REGIME_STRESS"].value_counts().to_dict())
print("agreement with precip tertiles:", (env["REGIME_STRESS"].astype(str).map({"HotDry":"Dry","Moderate":"Normal","CoolWet":"Wet"}) == env["REGIME_PRCP"].astype(str)).mean().round(2))

keep_env = ["YEAR", "LOC", "PRCP_SEASON", "STRESS_IDX", "PRCP_JA", "CLDD_JA", "TAVG_JA", "CLAY_TOP", "SAND_TOP", "SOC_TOP", "PH_TOP",
            "REGIME_PRCP", "REGIME_STRESS"] + [f"ENV_PC{i+1}" for i in range(5)]
df = ph.merge(env[keep_env], on=["YEAR", "LOC"], how="inner", validate="many_to_one")
print("rows", len(ph), "->", len(df), "| lines", df.LINE_ID.nunique(), "| pops", df.POP.nunique(), "| envs", df.ENV.nunique())
print("years per line:", df.groupby("LINE_ID").YEAR.nunique().value_counts().to_dict())
print("missing:", df[["YLD", "MST", "TWT", "ERM", "RTLP", "STLP", "PHT", "EHT"]].isna().mean().round(2).to_dict())
print("HG:", df.HG.value_counts().to_dict(), "| testers", df.TESTER.nunique())
df.to_pickle("results/pheno_env_ready.pkl")
env.to_csv("results/env_ready.csv", index=False)
