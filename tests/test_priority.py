"""Tests for src/priority.py: places where light-sensitive birds are still reported and night light rose."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import priority  # noqa: E402


def _inputs():
    years = np.arange(2014, 2026)
    ga = pd.concat([
        pd.DataFrame({"cell_id": "A", "year": years, "alan": np.where(years <= 2016, 2.0, 8.0)}),
        pd.DataFrame({"cell_id": "B", "year": years, "alan": 5.0}),
        pd.DataFrame({"cell_id": "C", "year": years, "alan": np.where(years <= 2016, 1.0, 9.0)}),
    ])
    rates = pd.DataFrame({
        "cell_id": ["A", "A", "B", "C", "D", "A"],
        "lat": [14.1, 14.1, 14.2, 14.3, 14.4, 14.1], "lon": [121.0, 121.0, 121.1, 121.2, 121.3, 121.0],
        "period": ["2018-2021", "2022-2025", "2022-2025", "2022-2025", "2022-2025", "2022-2025"],
        "group": ["Light-sensitive", "Light-sensitive", "Light-sensitive", "Light-sensitive", "Light-sensitive",
                  "Light-tolerant"],
        "n_checklists": [6, 10, 8, 7, 9, 10],
        "reporting_rate": [0.02, 0.05, 0.03, 0.0, 0.04, 0.2],
    })
    ck = pd.DataFrame({"cell_id": ["A", "A", "A", "B", "D"],
                       "locality": ["La Mesa", "La Mesa", "Other", "Imus", "Tanay"]})
    return ga, rates, ck


def test_only_cells_with_sensitive_birds():
    out = priority.build_priority(*_inputs())
    assert set(out["cell_id"]) == {"A", "B", "D"}          # C: sensitive rate 0 -> excluded


def test_ratio_and_priority_flag():
    out = priority.build_priority(*_inputs()).set_index("cell_id")
    assert abs(out.loc["A", "ratio"] - (8.5 / 2.5)) < 1e-9
    assert bool(out.loc["A", "priority"]) is True
    assert abs(out.loc["B", "ratio"] - 1.0) < 1e-9
    assert bool(out.loc["B", "priority"]) is False


def test_missing_light_data_is_not_priority():
    out = priority.build_priority(*_inputs()).set_index("cell_id")
    assert np.isnan(out.loc["D", "ratio"])
    assert bool(out.loc["D", "priority"]) is False


def test_locality_rate_and_checklists():
    out = priority.build_priority(*_inputs()).set_index("cell_id")
    assert out.loc["A", "locality"] == "La Mesa"
    assert abs(out.loc["A", "sensitive_rate"] - 0.05) < 1e-12   # highest period rate
    assert out.loc["A", "n_checklists"] == 16                    # both periods, sensitive rows only


def test_sorted_brightest_rise_first():
    out = priority.build_priority(*_inputs())
    assert out["cell_id"].iloc[0] == "A"


def test_clean_locality():
    c = priority.clean_locality
    assert c("Mexico, Central Luzon, PH (15.053, 120.772)") == "Mexico, Central Luzon"
    assert c("Ph--Sampaguita Village") == "Sampaguita Village"
    assert c("Pueblo de Oro Malvar Townscape,  Calabarzon, PH (14,039, 121,14)") == "Pueblo de Oro Malvar Townscape, Calabarzon"
    assert c("Puting Kahoy, Silang PH-Cavite (14.2216,121.0354)") == "Puting Kahoy, Silang, Cavite"
    assert c("Vermosa Sports Hub, Imus") == "Vermosa Sports Hub, Imus"
    assert c("LPPWP--Freedom Island") == "LPPWP, Freedom Island"
    assert c(None) == ""
