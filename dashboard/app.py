"""BreedForward demo: which 2008 lines advance under a plot cut.

Reads results/advance2008.csv (written by src/predict_siblings.py). Never fits a model.

    streamlit run dashboard/app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BreedForward", layout="wide")
PATH = Path("results/advance2008.csv")
if not PATH.exists():
    st.error("results/advance2008.csv not found. Run `python src/predict_siblings.py` from the repo root first.")
    st.stop()


@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv(PATH, dtype={"LINE_ID": str, "POP": str})


adv = load()
z = lambda s: (s - s.mean()) / s.std()
Z = {"yld": z(adv.pred_yld_aug), "twt": z(adv.pred_twt), "mst": z(adv.pred_mst), "erm": z(adv.pred_erm), "lodg": z(adv.pop_lodging_obs)}

# ---------------- sidebar: the breeder's lever ----------------
st.sidebar.title("BreedForward")
st.sidebar.caption("January 2008. Plots are cut. Which of these lines advance?")
st.sidebar.subheader("Index weights")
preset = st.sidebar.radio("preset", ["default", "yield only", "equal weights", "custom"], horizontal=True)
presets = {
    "default": dict(yld=0.5, twt=0.1, mst=-0.15, erm=-0.05, lodg=-0.2),
    "yield only": dict(yld=1.0, twt=0.0, mst=0.0, erm=0.0, lodg=0.0),
    "equal weights": dict(yld=0.2, twt=0.2, mst=-0.2, erm=-0.2, lodg=-0.2),
}
base = presets.get(preset, presets["default"])
w = {}
labels = {"yld": "yield (predicted)", "twt": "test weight (predicted)", "mst": "moisture (predicted, negative = drier is better)",
          "erm": "maturity (predicted, negative = earlier is better)", "lodg": "family lodging (observed, negative = less is better)"}
for k in Z:
    w[k] = st.sidebar.slider(labels[k], -0.5, 1.0, float(base[k]), 0.05, disabled=(preset != "custom"), key=f"w_{k}")
frac = st.sidebar.slider("share of candidates to advance", 0.05, 0.5, 0.20, 0.05)

# ---------------- recompute the list under these weights ----------------
adv = adv.copy()
adv["index"] = sum(w[k] * Z[k] for k in Z)
adv = adv.sort_values("index", ascending=False)
adv["rank"] = np.arange(1, len(adv) + 1)
k = int(frac * len(adv))
adv["advance"] = adv["rank"] <= k
top = adv[adv.advance]
gain = top.obs_yld_2008.mean() - adv.obs_yld_2008.mean()
oracle = adv.nlargest(k, "obs_yld_2008").obs_yld_2008.mean() - adv.obs_yld_2008.mean()

st.title("Which 2008 lines should advance?")
c1, c2, c3, c4 = st.columns(4)
c1.metric("candidate lines", f"{len(adv):,}")
c2.metric(f"advanced (top {frac:.0%})", f"{k:,}")
c3.metric("realised 2008 yield gain", f"{gain:+.2f} bu/ac", help="mean observed 2008 yield of the advanced set minus the mean of all candidates")
c4.metric("of what perfect foresight would get", f"{100 * gain / oracle:.0f}%", help=f"perfect foresight: {oracle:+.2f} bu/ac")
if gain < 0:
    st.warning("These weights advance lines that yielded *below* average in 2008. Maturity and moisture are now weighted as heavily as yield, so the index selects early, dry, low-yielding lines.")

tab1, tab2, tab3 = st.tabs(["Advancement list", "Family view", "How good is the prediction"])

with tab1:
    pop = st.selectbox("filter to a family", ["all"] + sorted(adv.POP.unique().tolist()))
    d = adv if pop == "all" else adv[adv.POP == pop]
    cols = ["rank", "LINE_ID", "POP", "HG", "pred_yld_aug", "pred_mst", "pred_twt", "pred_erm", "pop_lodging_obs", "index", "advance", "obs_yld_2008"]
    st.dataframe(d[cols].head(300).round(2), hide_index=True, width="stretch")
    st.caption("pred_* are model predictions made as of January 2008. obs_yld_2008 is what actually happened, shown only to score ourselves.")
    st.download_button("download full list", adv[cols].to_csv(index=False).encode(), "advance2008_ranked.csv")

with tab2:
    fam = adv.groupby("POP").agg(lines=("LINE_ID", "size"), advanced=("advance", "sum"), pred_yld=("pred_yld_aug", "mean"),
                                 obs_yld=("obs_yld_2008", "mean"), lodging=("pop_lodging_obs", "first")).reset_index()
    fam["share_advanced"] = fam.advanced / fam.lines
    st.subheader("Families, not lines, carry most of the signal")
    st.scatter_chart(fam, x="pred_yld", y="obs_yld", size="lines", color="share_advanced")
    st.caption("each dot is a family: predicted mean vs observed 2008 mean, dot size = number of candidate lines")
    st.dataframe(fam.sort_values("obs_yld", ascending=False).round(2), hide_index=True, width="stretch")

with tab3:
    r = np.corrcoef(adv.pred_yld_aug, adv.obs_yld_2008)[0, 1]
    st.subheader(f"Predicted vs observed 2008 yield, r = {r:.2f}")
    st.scatter_chart(adv.sample(min(len(adv), 4000), random_state=0), x="pred_yld_aug", y="obs_yld_2008", color="advance")
    st.caption("real signal, lots of noise. The advanced set (colored) sits visibly higher on average than the rest. "
               "The ceiling is r ~ 0.68 because each 2008 line mean rests on only ~5 plots.")
