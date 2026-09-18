"""BreedForward: build pheno_env_ready.csv from C1/C2 + environmental_features.
Key facts baked in (verified on C1):
  - LINE is only unique within a population. Use LINE_UNIQUE_ID (e.g. C1.1.191).
  - Every line is tested in exactly ONE year (~7 locations). YEAR is nested in population.
  - YEAR_y == YEAR_x everywhere; the _x/_y columns are merge debris. Keep one.
  - CLUSTER is just C1 vs C2 (heterotic group), not a data-driven cluster.
  - Regimes must be defined on unique YEAR x LOC, not on plot rows.
"""
import numpy as np
import pandas as pd

KEEP = ["shorthand_x", "YEAR_x", "LOC", "LATITUDE", "LONGITUDE", "LINE_UNIQUE_ID",
        "GENERATION_NAME", "CROSS", "GERMPLASM_ID_TESTER", "CLUSTER", "SET",
        "YLD_BE", "MST", "TWT", "PHT", "EHT", "ERM", "RTLP", "STLP"]

def load(path):
    d = pd.read_csv(path, usecols=KEEP, low_memory=False,
                    dtype={"LINE_UNIQUE_ID": str, "SET": str, "GERMPLASM_ID_TESTER": str})
    return d.rename(columns={"shorthand_x": "POP", "YEAR_x": "YEAR", "LINE_UNIQUE_ID": "LINE_ID",
                             "GERMPLASM_ID_TESTER": "TESTER", "CLUSTER": "HG"})

ph = pd.concat([load("C1_Phenotype_Data_V2.csv"), load("C2_Phenotype_Data_V2.csv")], ignore_index=True)
ph["ENV"] = ph["YEAR"].astype(str) + "_" + ph["LOC"]

env = pd.read_csv("environmental_features.csv")
assert not env.duplicated(["YEAR", "LOC"]).any()
prcp = [f"X{m:02d}_PRCP" for m in range(4, 11)]
env["PRCP_SEASON"] = env[prcp].sum(axis=1)
q = env["PRCP_SEASON"].quantile([1/3, 2/3]).values          # environment-level cutoffs
env["REGIME"] = pd.cut(env["PRCP_SEASON"], [-np.inf, *q, np.inf], labels=["Dry", "Normal", "Wet"])

df = ph.merge(env, on=["YEAR", "LOC"], how="inner", validate="many_to_one")

# QC
print("rows", len(ph), "->", len(df))
print("pops", df.POP.nunique(), "lines", df.LINE_ID.nunique(), "envs", df.ENV.nunique())
print("years per line:", df.groupby("LINE_ID").YEAR.nunique().value_counts().to_dict())
print("regime cutoffs (mm):", q.round(0), "| envs per regime:", env.REGIME.value_counts().to_dict())
dups = df.duplicated(["LINE_ID", "ENV", "TESTER"], keep=False)
print("duplicate line x env x tester rows:", int(dups.sum()), "(check SET/reps before averaging)")
print("missing:", df[["YLD_BE", "MST", "PHT", "EHT", "TWT"]].isna().mean().round(2).to_dict())

df.to_csv("pheno_env_ready.csv", index=False)
