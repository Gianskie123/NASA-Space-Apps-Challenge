"""Tests for src/province_trends.py (the app's "Where it changed" table).

Run from the project root:  python -m pytest tests -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import province_trends  # noqa: E402

SCHEMA = ["variable", "adm2_code", "province", "n_months", "tau", "p_value", "q_value", "significant",
          "slope_per_year", "change_pct", "direction"]
MONTHLY = ["alan", "ndvi", "lst_day", "rain_mm"]
YEARLY = ["urban_frac", "forest_frac"]


@pytest.fixture(scope="module")
def tables():
    rng = np.random.default_rng(1)
    years = np.repeat(np.arange(2014, 2026), 12)
    months = np.tile(np.arange(1, 13), 12)
    t = years - 2014 + (months - 0.5) / 12
    season = 5 * np.sin(2 * np.pi * months / 12)
    rows = []
    for code, name, slope in [(1001, "Trendland", 1.0), (2002, "Flatland", 0.0)]:
        base = {"adm2_code": code, "province": name, "adm1": "Region", "year": years, "month": months}
        df = pd.DataFrame(base)
        for v in MONTHLY:
            df[v] = 10 + slope * t + season + rng.normal(0, 0.5, len(t))
        if slope == 0.0:
            df["ndvi"] = np.nan                       # fully cloudy province
        rows.append(df)
    pm = pd.concat(rows, ignore_index=True)
    yrs = np.arange(2014, 2026)
    pl = pd.concat([pd.DataFrame({"adm2_code": np.int32(code), "province": name, "year": yrs,
                                  "urban_frac": 0.2 + 0.01 * s * (yrs - 2014) + rng.normal(0, 0.001, 12),
                                  "forest_frac": 0.5 + rng.normal(0, 0.01, 12)})
                    for code, name, s in [(1001, "Trendland", 1), (2002, "Flatland", 0)]], ignore_index=True)
    return pm, pl, province_trends.build_province_trends(pm, pl)


def row(out, code, var):
    r = out[(out["adm2_code"] == code) & (out["variable"] == var)]
    assert len(r) == 1
    return r.iloc[0]


def test_schema(tables):
    out = tables[2]
    assert list(out.columns) == SCHEMA
    assert len(out) == 2 * (len(MONTHLY) + len(YEARLY))
    assert out["adm2_code"].dtype == np.int64


def test_trend_detected(tables):
    r = row(tables[2], 1001, "alan")
    assert bool(r["significant"]) and r["direction"] == "increasing"
    assert abs(r["slope_per_year"] - 1.0) < 0.1
    assert r["province"] == "Trendland"


def test_all_nan_variable(tables):
    r = row(tables[2], 2002, "ndvi")
    assert not bool(r["significant"])
    assert r["direction"] == "no significant trend"


def test_n_months(tables):
    out = tables[2]
    assert row(out, 1001, "alan")["n_months"] == 144
    assert row(out, 1001, "urban_frac")["n_months"] == 144
