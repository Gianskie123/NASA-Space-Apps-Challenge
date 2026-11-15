"""Tests for src/plain.py: the plain-language layer the app shows to non-technical readers."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import plain  # noqa: E402


def test_verdict_words_per_variable():
    assert plain.verdict("alan", "increasing", True) == "Getting brighter"
    assert plain.verdict("alan", "decreasing", True) == "Getting darker"
    assert plain.verdict("ndvi", "increasing", True) == "Getting greener"
    assert plain.verdict("rain_mm", "decreasing", True) == "Getting drier"
    assert plain.verdict("urban_frac", "increasing", True) == "More built-up"


def test_verdict_not_significant_is_no_clear_change():
    assert plain.verdict("alan", "increasing", False) == "No clear change"
    assert plain.verdict("alan", "no significant trend", False) == "No clear change"


def test_verdict_too_short_or_no_data():
    assert plain.verdict("alan", "window too short", False) == "Not enough years"
    assert plain.verdict("alan", "no data", False) == "Not enough data"


def test_confidence_words():
    assert plain.confidence(0.0) == "Very confident"
    assert plain.confidence(0.004) == "Very confident"
    assert plain.confidence(0.03) == "Confident"
    assert plain.confidence(0.2).startswith("Not confident")
    assert plain.confidence(None) == "Not enough data"
    assert plain.confidence(float("nan")) == "Not enough data"


def test_change_phrase_percent_and_times():
    assert plain.change_phrase("alan", {"change_pct": 32.9, "change_total": 3.1}, "2014") == "about 33% brighter than in 2014"
    assert plain.change_phrase("alan", {"change_pct": 124.6, "change_total": 1.9}, "2014") == "about 2.2× the 2014 level"
    assert plain.change_phrase("ndvi", {"change_pct": -4.2, "change_total": -0.03}, "2014") == "about 4% less green than in 2014"


def test_change_phrase_rain_and_small_changes():
    assert plain.change_phrase("rain_mm", {"change_pct": 21.3, "change_total": 40}, "2014") == "about 21% wetter than in 2014"
    assert plain.change_phrase("alan", {"change_pct": 0.4, "change_total": 0.1}, "2014") == "less than 1% brighter than in 2014"


def test_change_phrase_land_cover_uses_percentage_points():
    out = plain.change_phrase("urban_frac", {"change_pct": 10.6, "change_total": 0.0088}, "2014")
    assert out == "+0.9 percentage points of the area since 2014"


def test_change_phrase_missing_values():
    assert plain.change_phrase("alan", {"change_pct": None, "change_total": None}, "2014") == ""
    assert plain.change_phrase("alan", {"change_pct": np.nan, "change_total": 2.0}, "2014") == ""


def _curve(s_dark, s_bright, t_dark, t_bright):
    rows = []
    for grp, sens, a, b in [("Light-sensitive", 1, s_dark, s_bright), ("Light-tolerant", 0, t_dark, t_bright)]:
        for i, x in enumerate(np.linspace(0, 50, 5)):
            rows.append({"group": grp, "sensitive": sens, "alan": x, "prob": a + (b - a) * i / 4})
    return pd.DataFrame(rows)


def test_bird_headline_clear_effect():
    h = plain.bird_headline(_curve(0.14, 0.02, 0.19, 0.13))
    assert h["clear"] is True
    assert round(h["ratio"]) == 7
    assert "7× less likely" in h["text"]
    assert "14%" in h["text"] and "2%" in h["text"]


def test_bird_headline_no_difference():
    h = plain.bird_headline(_curve(0.10, 0.10, 0.19, 0.18))
    assert h["clear"] is False
    assert "no clear difference" in h["text"].lower()
