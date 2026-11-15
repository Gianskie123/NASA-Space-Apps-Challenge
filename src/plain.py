"""Plain-language wording for non-technical readers and policymakers.

Turns trend results (from trends.py) and the bird effect curve into short phrases: a verdict ("Getting
brighter"), how sure we are ("Very confident"), and how big the change is ("about 33% higher than in 2014").
The statistics themselves are unchanged; this module only words them.
"""
from __future__ import annotations

import math

import pandas as pd

# variable -> (verdict when rising, verdict when falling, short word up, short word down)
WORDS = {
    "alan": ("Getting brighter", "Getting darker", "Brighter", "Darker"),
    "ndvi": ("Getting greener", "Losing greenery", "Greener", "Less green"),
    "lst_day": ("Getting hotter", "Getting cooler", "Hotter", "Cooler"),
    "rain_mm": ("Getting wetter", "Getting drier", "Wetter", "Drier"),
    "urban_frac": ("More built-up", "Less built-up", "More built-up", "Less built-up"),
    "forest_frac": ("More forest", "Less forest", "More forest", "Less forest"),
}
SHARE_VARIABLES = {"urban_frac", "forest_frac"}


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def short_words(var: str) -> tuple[str, str]:
    """('Brighter', 'Darker') style words for map legends."""
    w = WORDS.get(var, ("Increasing", "Decreasing", "Higher", "Lower"))
    return w[2], w[3]


def verdict(var: str, direction: str, significant: bool) -> str:
    direction = (direction or "").lower()
    if direction == "window too short":
        return "Not enough years"
    if direction == "no data":
        return "Not enough data"
    if not significant or direction not in ("increasing", "decreasing"):
        return "No clear change"
    up, down = WORDS.get(var, ("Increasing", "Decreasing"))[:2]
    return up if direction == "increasing" else down


def confidence(p) -> str:
    p = _num(p)
    if p is None:
        return "Not enough data"
    if p < 0.01:
        return "Very confident"
    if p < 0.05:
        return "Confident"
    return "Not confident: could be natural ups and downs"


def change_phrase(var: str, result: dict, start_label: str) -> str:
    """How big the change is, in words. Land-cover shares use percentage points of the area."""
    if var in SHARE_VARIABLES:
        total = _num(result.get("change_total"))
        if total is None:
            return ""
        return f"{total * 100:+.1f} percentage points of the area since {start_label}"
    pct = _num(result.get("change_pct"))
    if pct is None:
        return ""
    ratio = 1 + pct / 100
    if ratio >= 2:
        return f"about {ratio:.1f}× the {start_label} level"
    if abs(pct) < 1:
        return f"less than 1% {'higher' if pct >= 0 else 'lower'} than in {start_label}"
    return f"about {abs(pct):.0f}% {'higher' if pct >= 0 else 'lower'} than in {start_label}"


def _ends(curve: pd.DataFrame, sensitive: int) -> tuple[float, float]:
    c = curve[curve["sensitive"] == sensitive].sort_values("alan")
    return float(c["prob"].iloc[0]), float(c["prob"].iloc[-1])


def times_text(r: float) -> str:
    return f"{r:.0f}" if r >= 3 else f"{r:.1f}"


def bird_headline(curve: pd.DataFrame) -> dict:
    """Headline from effect_curve: chance a species is reported in the darkest vs brightest places."""
    s_dark, s_bright = _ends(curve, 1)
    t_dark, t_bright = _ends(curve, 0)
    ratio = s_dark / s_bright if s_bright > 0 else float("inf")
    t_ratio = t_dark / t_bright if t_bright > 0 else float("inf")
    clear = bool(ratio >= 1.5 and ratio > t_ratio)
    if clear:
        text = (f"In the brightest places, birds that need darkness are about {times_text(ratio)}× less likely to be "
                f"seen than in the darkest places ({s_dark:.0%} → {s_bright:.0%} chance on a typical one-hour "
                f"birdwatch). Birds that tolerate light change much less ({t_dark:.0%} → {t_bright:.0%}).")
    else:
        text = ("Birds that need darkness and birds that tolerate light respond to night light in much the same "
                "way: no clear difference at this scale.")
    return {"text": text, "clear": clear, "ratio": ratio, "s_dark": s_dark, "s_bright": s_bright,
            "t_dark": t_dark, "t_bright": t_bright}
