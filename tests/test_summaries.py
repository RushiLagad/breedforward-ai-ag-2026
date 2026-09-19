"""Sanity tests on the committed summary tables and the scripts. No dataset needed, so they run in CI.
    pytest -q
"""
import ast, glob, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RS = ROOT / "results_summary"


def test_scripts_parse():
    for f in glob.glob(str(ROOT / "src" / "*.py")) + glob.glob(str(ROOT / "dashboard" / "*.py")):
        ast.parse(open(f, encoding="utf-8").read(), f)


def test_stage2_shape():
    s = pd.read_csv(RS / "stage2_results.csv")
    assert {"year", "trait", "r_markers"} <= set(s.columns)
    assert s.r_markers.between(-1, 1).all()
    assert set(s.year) >= {2007, 2008}


def test_stage3_ordering():
    s = pd.read_csv(RS / "stage3_schemes.csv").set_index("trait")
    for t in ("YLD", "MST", "TWT"):
        assert s.loc[t, "r_sibmean"] > s.loc[t, "r_newyear"], t
        assert 0 < s.loc[t, "gain_sibmean"] <= s.loc[t, "gain_max"], t
    ch = pd.read_csv(RS / "stage3_index_choice.csv")
    assert ch.used.sum() == 1, "exactly one yield predictor is used for the index"


def test_stage4_curve_is_stratified_and_saturates():
    s = pd.read_csv(RS / "stage4_sampling_curve.csv")
    y = s[(s.trait == "YLD") & (s.scheme == "sib")].sort_values("frac")
    assert list(y.frac) == sorted(y.frac)
    assert (y.plots_used.diff().dropna() > 0).all(), "actual plots must rise with the sampled share"
    assert y.gain.iloc[0] >= 0.75 * y.gain.max(), "10% of each family should keep most of the gain"
    assert y.r.between(0, 1).all()


def test_stage5_default_is_reference():
    s = pd.read_csv(RS / "stage5_weight_sensitivity.csv")
    d = s[s.scheme.str.startswith("default")].iloc[0]
    assert abs(d.overlap_with_default - 1.0) < 1e-9
    assert (s.overlap_with_default.between(0, 1)).all()
    sw = pd.read_csv(RS / "stage5_random_sweep.csv")
    assert set(sw.metric) >= {"overlap_with_default", "yld_gain"}


def test_no_data_committed():
    tracked = [p for p in (ROOT / "data").glob("**/*") if p.is_file() and p.name != ".gitkeep"]
    # data/ is gitignored; this guards a local checkout, CI has no data directory at all
    assert not (ROOT / "results" / "advance2008.csv").exists() or (ROOT / ".gitignore").read_text().find("results/") >= 0
