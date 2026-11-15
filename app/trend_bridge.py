"""Thin wrapper around Member 3's src/trends.py.

The app never re-implements the statistics: the verdict, slope, p-value, sentence and the Sen's-slope
line all come from trends.trend_summary / trends.trend_line, so the app matches Member 3's notebook.
If trends.py is missing, TREND_AVAILABLE is False and the page shows a pending state.
"""

from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

try:
    import trends as _trends  # src/trends.py (Member 3)

    TREND_AVAILABLE = True
except Exception:  # ImportError, or an error inside the module; details go to the server log only
    log.exception("Could not import src/trends.py")
    _trends = None
    TREND_AVAILABLE = False


def to_periods(series: pd.Series, yearly: bool) -> pd.Series:
    """Month-start Timestamps -> monthly PeriodIndex, or yearly PeriodIndex for yearly variables."""
    s = series.copy()
    if yearly:
        s.index = pd.PeriodIndex(s.index.year.astype(str), freq="Y")
    else:
        s.index = s.index.to_period("M")
    return s.sort_index()


def summarize(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp, freq: str, *, yearly: bool,
              label: str, unit: str) -> dict:
    """Run trend_summary on one window. `series` is indexed by month-start Timestamps."""
    if _trends is None:
        raise RuntimeError("trends.py not available")
    s = to_periods(series, yearly)
    if yearly:
        return _trends.trend_summary(s, str(start.year), str(end.year), "annual", label=label, unit=unit)
    return _trends.trend_summary(s, start.strftime("%Y-%m"), end.strftime("%Y-%m"), freq, label=label, unit=unit)


def trend_line(result: dict, index: pd.DatetimeIndex, yearly: bool) -> pd.Series:
    """Member 3's Sen's-slope line over the plotted index (returned with the same Timestamp index)."""
    if _trends is None:
        return pd.Series(float("nan"), index=index)
    pidx = pd.PeriodIndex(index.year.astype(str), freq="Y") if yearly else index.to_period("M")
    line = _trends.trend_line(result, pidx)
    return pd.Series(line.to_numpy(), index=index)
