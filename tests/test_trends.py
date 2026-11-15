"""Tests for src/trends.py (Member 3, part A checks in docs/TEAM_BUILD_PLAN.md).

Run from the project root:  python -m pytest tests -q
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import trends  # noqa: E402

IDX = pd.period_range("2014-01", "2025-12", freq="M")       # 144 months, the plan's window


def seasonal_series(slope_per_year=0.0, noise=1.0, seed=0, idx=IDX, amp=5.0):
    rng = np.random.default_rng(seed)
    t = idx.year + (idx.month - 0.5) / 12
    season = amp * np.sin(2 * np.pi * (idx.month - 1) / 12)          # monsoon-like cycle
    return pd.Series(10 + slope_per_year * (t - t[0]) + season + rng.normal(0, noise, len(idx)), index=idx)


# --- plan check 1: known slope is recovered --------------------------------------------------
def test_recovers_known_positive_slope():
    r = trends.trend_summary(seasonal_series(1.0, seed=1), "2014-01", "2025-12")
    assert abs(r["slope_per_year"] - 1.0) <= 0.10
    assert r["p_value"] < 0.05 and r["direction"] == "increasing" and r["significant"]
    assert "increased" in r["sentence"]


def test_recovers_negative_slope_annual():
    r = trends.trend_summary(seasonal_series(-0.8, seed=2), freq="annual")
    assert abs(r["slope_per_year"] + 0.8) <= 0.10
    assert r["direction"] == "decreasing"
    assert r["slope_ci_low"] < r["slope_per_year"] < r["slope_ci_high"]


# --- plan check 2: false-positive rate --------------------------------------------------------
def test_false_positive_rate_monthly():
    hits = sum(trends.trend_summary(seasonal_series(0.0, seed=s))["significant"] for s in range(200))
    assert hits / 200 <= 0.10, f"{hits}/200 noise series came out significant"


def test_false_positive_rate_annual():
    hits = sum(trends.trend_summary(seasonal_series(0.0, seed=1000 + s), freq="annual")["significant"]
               for s in range(200))
    assert hits / 200 <= 0.10, f"{hits}/200 noise series came out significant"


def test_seasonality_alone_is_not_a_trend():
    # strong seasonal cycle, no trend, little noise: a naive (non-seasonal) test can be fooled
    r = trends.trend_summary(seasonal_series(0.0, noise=0.2, amp=20, seed=3))
    assert not r["significant"]


# --- plan check 3: constant series and missing months -----------------------------------------
def test_constant_series_no_crash():
    r = trends.trend_summary(pd.Series(5.0, index=IDX))
    assert r["direction"] == "no significant trend" and r["slope_per_year"] == 0


def test_thirty_percent_missing_still_runs():
    s = seasonal_series(1.0, seed=4)
    rng = np.random.default_rng(5)
    s.iloc[rng.choice(len(s), int(0.3 * len(s)), replace=False)] = np.nan
    r = trends.trend_summary(s)
    assert r["significant"] and abs(r["slope_per_year"] - 1.0) <= 0.15
    assert r["n_missing"] == int(0.3 * 144)


def test_heavy_missing_gives_warning():
    s = seasonal_series(1.0, seed=6)
    s.iloc[::2] = np.nan                                   # 50% missing
    assert trends.trend_summary(s)["warning"] is not None


def test_all_missing_is_no_data():
    assert trends.trend_summary(pd.Series(np.nan, index=IDX))["direction"] == "no data"


# --- plan check 4: short window -----------------------------------------------------------------
def test_two_year_window_too_short():
    r = trends.trend_summary(seasonal_series(1.0), "2024-01", "2025-12")
    assert r["direction"] == "window too short" and r["p_value"] is None


def test_window_is_respected():
    s = seasonal_series(0.0, seed=7)
    s[s.index >= pd.Period("2020-01", "M")] += 20          # step only after 2020
    r = trends.trend_summary(s, "2014-01", "2019-12")
    assert r["n_months"] == 72 and not r["significant"]


# --- plan check 5: speed ------------------------------------------------------------------------
def test_fast_enough_for_live_app():
    s = seasonal_series(0.5, seed=8)
    t = time.perf_counter()
    for _ in range(10):
        trends.trend_summary(s)
        trends.trend_summary(s, freq="annual")
    assert (time.perf_counter() - t) / 20 < 1.0


# --- yearly variables (land cover) ----------------------------------------------------------------
def test_yearly_input_uses_annual_test():
    years = np.arange(2014, 2026)
    s = pd.Series(0.30 + 0.01 * (years - 2014), index=years)          # urban share +1 point / year
    r = trends.trend_summary(s, variable="urban_frac")
    assert r["freq"] == "annual" and r["significant"]
    assert abs(r["slope_per_year"] - 0.01) < 1e-9
    assert r["unit"] == "share of area"


def test_annual_needs_nine_valid_months():
    s = seasonal_series(1.0, seed=9)
    s[(s.index.year == 2016) & (s.index.month <= 6)] = np.nan          # 2016 has only 6 months
    r = trends.trend_summary(s, freq="annual")
    assert "fewer than 9 valid months" in r["warning"]


# --- helpers ---------------------------------------------------------------------------------------
def test_monthly_series_from_table_fills_gaps():
    df = pd.DataFrame({"year": [2014, 2014, 2014], "month": [1, 2, 4], "v": [1.0, 2.0, 4.0]})
    s = trends.monthly_series(df, "v")
    assert len(s) == 4 and np.isnan(s.loc[pd.Period("2014-03", "M")])


def test_trend_line_matches_slope():
    s = seasonal_series(1.0, seed=10)
    r = trends.trend_summary(s)
    line = trends.trend_line(r, s.index)
    assert abs((line.iloc[-1] - line.iloc[0]) - r["change_total"]) < 1e-9


def test_fdr_bh_known_values():
    p = np.array([0.01, 0.04, 0.03, 0.20, np.nan])
    q = trends.fdr_bh(p)
    # sorted p 0.01, 0.03, 0.04, 0.20 -> p*m/rank 0.04, 0.06, 0.0533, 0.20 -> running min from the top
    np.testing.assert_allclose(q[:4], [0.04, 0.16 / 3, 0.16 / 3, 0.20])
    assert np.isnan(q[4])


def test_region_trends_with_fdr():
    rows = []
    for k, slope in enumerate([1.0, 0.0, 0.0]):
        s = seasonal_series(slope, seed=20 + k)
        rows.append(pd.DataFrame({"province": f"P{k}", "year": s.index.year, "month": s.index.month,
                                  "alan": s.to_numpy()}))
    res = trends.region_trends(pd.concat(rows), "province", ["alan"])
    assert set(res.columns) >= {"province", "variable", "p_value", "q_value", "significant", "direction"}
    assert res.set_index("province").loc["P0", "significant"]
    assert (res["q_value"] >= res["p_value"]).all()


# --- cross-check against pymannkendall (skipped if not installed) ---------------------------------
def test_matches_pymannkendall_seasonal():
    mk = pytest.importorskip("pymannkendall")
    s = seasonal_series(0.3, seed=11)
    ours = trends.seasonal_kendall(s.to_numpy(), s.index.year.to_numpy(), s.index.month.to_numpy())
    ref = mk.seasonal_test(s.to_numpy(), period=12)
    assert ours["s"] == ref.s
    assert abs(ours["p_value"] - ref.p) < 1e-9
    assert abs(ours["slope_per_year"] - ref.slope) < 1e-9


def test_matches_pymannkendall_hamed_rao():
    mk = pytest.importorskip("pymannkendall")
    s = seasonal_series(0.3, seed=12).groupby(lambda p: p.year).mean()
    ours = trends.hamed_rao_mk(s.to_numpy(), s.index.to_numpy().astype(float))
    ref = mk.hamed_rao_modification_test(s.to_numpy())
    assert ours["s"] == ref.s
    assert abs(ours["p_value"] - ref.p) < 1e-6
    assert abs(ours["slope_per_year"] - ref.slope) < 1e-9
