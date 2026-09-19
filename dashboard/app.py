"""BreedForward dashboard shell.

Reads a saved results file. It NEVER fits a model. On presentation day the
laptop must open this in two seconds, with no network and no compute.

    streamlit run dashboard/app.py -- --results results/results.csv

Expected columns: entity, condition, estimate, se, n  (see src/rank.py).
Optional second file: a per-entity trait table (entity, <trait>, ...) for the
quadrant plot.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.demo import demo_results  # noqa: E402
from src.rank import score  # noqa: E402

st.set_page_config(page_title="BreedForward", layout="wide")

DEFAULT_RESULTS = "results/results.csv"
DEFAULT_TRAITS = "results/traits.csv"


@st.cache_data
def load(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"entity": str})


st.sidebar.title("BreedForward")
path = st.sidebar.text_input("results file", DEFAULT_RESULTS)
if Path(path).exists():
    res = load(path)
    st.sidebar.success(f"{res['entity'].nunique():,} entities loaded")
else:
    res = demo_results()
    st.sidebar.warning("Demo data. Point this at results/results.csv when it exists.")

conds = sorted(res["condition"].unique())
min_n = st.sidebar.slider("minimum n per cell", 1, 20, 5)

st.sidebar.subheader("Decision weights")
st.sidebar.caption("Weights are a project choice. Move them and watch the shortlist react.")
weights = {c: st.sidebar.slider(c, 0.0, 1.0, round(1 / len(conds), 2), 0.05) for c in conds}
penalty = st.sidebar.slider("instability penalty", 0.0, 2.0, 0.5, 0.1)

if sum(weights.values()) == 0:
    st.error("All weights are zero.")
    st.stop()

ranked = score(res, weights, penalty=penalty, min_n=min_n)

st.title("Environment-aware selection")
c1, c2, c3 = st.columns(3)
c1.metric("entities ranked", f"{len(ranked):,}")
c2.metric("conditions", len(conds))
top_mean = set(ranked.sort_values("performance", ascending=False).head(10).index)
c3.metric("top-10 overlap, mean vs score", f"{len(top_mean & set(ranked.head(10).index))}/10")

tab1, tab2, tab3, tab4 = st.tabs(["Shortlist", "Entity profile", "Reversal", "2008 advancement"])

with tab1:
    st.subheader("Top 25 by decision score")
    show = ranked.head(25).copy()
    show.insert(0, "rank", range(1, len(show) + 1))
    st.dataframe(show.round(2), use_container_width=True)
    st.download_button("download shortlist", show.to_csv().encode(), "shortlist.csv")

with tab2:
    ent = st.selectbox("entity", ranked.index.tolist())
    prof = res[res["entity"] == ent].set_index("condition").reindex(conds)
    st.subheader(f"{ent}: performance by condition")
    st.bar_chart(prof["estimate"])
    st.caption("Bars are condition-centered estimates. Error is se; n per cell below.")
    st.dataframe(prof[["estimate", "se", "n"]].round(2), use_container_width=True)

with tab3:
    st.subheader("Who the decision score adds and drops")
    by_mean = ranked.sort_values("performance", ascending=False).head(10).index
    by_score = ranked.head(10).index
    a, b = st.columns(2)
    a.write("**Top 10 by mean performance**")
    a.write(list(by_mean))
    b.write("**Top 10 by decision score**")
    b.write(list(by_score))
    dropped = [e for e in by_mean if e not in by_score]
    st.info(f"Dropped by the stability penalty: {dropped or 'none'}")

with tab4:
    st.subheader("Bayer scenario: which 2008 lines advance")
    adv_path = "results/advance2008.csv"
    if Path(adv_path).exists():
        adv = pd.read_csv(adv_path, dtype={"LINE_ID": str, "POP": str})
        c1, c2, c3 = st.columns(3)
        c1.metric("candidate lines", f"{len(adv):,}")
        c2.metric("flagged to advance (top 20%)", f"{int(adv.advance_top20.sum()):,}")
        top = adv[adv.advance_top20]
        c3.metric("realised 2008 yield gain of flagged set", f"{top.obs_yld_2008.mean() - adv.obs_yld_2008.mean():+.2f} bu/ac")
        pop = st.selectbox("population", ["all"] + sorted(adv.POP.unique().tolist()))
        d = adv if pop == "all" else adv[adv.POP == pop]
        cols = ["rank", "LINE_ID", "POP", "HG", "pred_yld_aug", "pred_mst", "pred_twt", "pred_erm", "pop_lodging_obs", "index", "advance_top20", "obs_yld_2008"]
        st.dataframe(d[cols].head(200).round(2), use_container_width=True, hide_index=True)
        st.caption("pred_* are model predictions before the 2008 season; obs_yld_2008 is what actually happened, shown only to score ourselves.")
        st.scatter_chart(d.sample(min(len(d), 3000), random_state=0), x="pred_yld_aug", y="obs_yld_2008", color="advance_top20")
    else:
        st.info("Run src/predict_siblings.py to create results/advance2008.csv.")
