"""Trend detection for AviTrend PH (Member 3, part A).

Answers the Challenge 2 questions for one variable, one region and one time window:
is it changing, in which direction, by how much, and is the change statistically significant?

Methods
-------
* Monthly data: Seasonal Mann-Kendall test (Hirsch, Slack & Smith 1982). Each calendar month is
  compared only with the same month in other years, so the monsoon cycle cannot fake a trend.
  Slope = seasonal Sen's slope (median of within-month pairwise slopes), in units per year.
* Annual data (and yearly variables such as land cover): Mann-Kendall test with the Hamed & Rao (1998)
  variance correction for autocorrelation. Slope = Sen's (1968) slope with a 95% confidence interval.
* Many regions at once: Benjamini-Hochberg false discovery rate correction (`fdr_bh`).

Missing months are allowed (cloudy months are set to NaN upstream). Pairs are only formed between
observed values, using their real time distance, so gaps do not distort the slope.

Dependencies: numpy, pandas, scipy only.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05
MIN_YEARS = 3                 # shortest window that gets a trend test
ANNUAL_MIN_MONTHS = 9         # a year needs this many valid months to get an annual mean
MISSING_WARN_SHARE = 0.30     # warn when more than this share of months is missing

# Display names and units for the app. Keys match the column names in the plan.
VARIABLES = {
    "alan": ("Night-time light", "nW/cm²/sr"),
    "ndvi": ("Vegetation (NDVI)", "NDVI units"),
    "lst_day": ("Land surface temperature", "°C"),
    "rain_mm": ("Rainfall", "mm/month"),
    "urban_frac": ("Urban land share", "share of area"),
    "forest_frac": ("Forest land share", "share of area"),
    "cropland_frac": ("Cropland share", "share of area"),
    "grass_shrub_frac": ("Grass and shrub share", "share of area"),
    "wetland_frac": ("Wetland share", "share of area"),
    "water_lc_frac": ("Water share", "share of area"),
}
YEARLY_VARIABLES = {k for k in VARIABLES if k.endswith("_frac")}


# --------------------------------------------------------------------------- input handling
def monthly_series(df: pd.DataFrame, value_col: str, year_col: str = "year", month_col: str = "month") -> pd.Series:
    """Turn a table with year/month columns into a monthly Series (PeriodIndex), gaps as NaN."""
    idx = pd.PeriodIndex.from_fields(year=df[year_col].astype(int), month=df[month_col].astype(int), freq="M")
    s = pd.Series(pd.to_numeric(df[value_col], errors="coerce").to_numpy(), index=idx)
    s = s.groupby(level=0).mean().sort_index()
    return s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))


def yearly_series(df: pd.DataFrame, value_col: str, year_col: str = "year") -> pd.Series:
    """Turn a table with a year column into a yearly Series (PeriodIndex, freq Y), gaps as NaN."""
    idx = pd.PeriodIndex(df[year_col].astype(int).astype(str), freq="Y")
    s = pd.Series(pd.to_numeric(df[value_col], errors="coerce").to_numpy(), index=idx)
    s = s.groupby(level=0).mean().sort_index()
    return s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="Y"))


def _as_period_index(series: pd.Series) -> pd.Series:
    s = series.copy()
    if isinstance(s.index, pd.PeriodIndex):
        return s.sort_index()
    if isinstance(s.index, pd.DatetimeIndex):
        s.index = s.index.to_period("M")
        return s.sort_index()
    if pd.api.types.is_integer_dtype(s.index):            # plain years
        s.index = pd.PeriodIndex(s.index.astype(str), freq="Y")
        return s.sort_index()
    raise TypeError("series index must be a PeriodIndex, DatetimeIndex or integer years")


def _is_yearly(s: pd.Series) -> bool:
    return isinstance(s.index, pd.PeriodIndex) and s.index.freqstr.upper().startswith(("Y", "A"))


# --------------------------------------------------------------------------- statistics
def _mk_s_var(y: np.ndarray) -> tuple[float, float, int]:
    """Mann-Kendall S and its variance (with tie correction) for values already in time order."""
    y = y[~np.isnan(y)]
    n = len(y)
    if n < 2:
        return 0.0, 0.0, n
    diff = y[None, :] - y[:, None]
    s = float(np.sign(diff[np.triu_indices(n, k=1)]).sum())
    _, counts = np.unique(y, return_counts=True)
    ties = counts[counts > 1]
    var = (n * (n - 1) * (2 * n + 5) - np.sum(ties * (ties - 1) * (2 * ties + 5))) / 18.0
    return s, float(var), n


def _z_p(s: float, var: float) -> tuple[float, float]:
    if var <= 0:
        return 0.0, 1.0
    if s > 0:
        z = (s - 1) / math.sqrt(var)
    elif s < 0:
        z = (s + 1) / math.sqrt(var)
    else:
        z = 0.0
    return z, float(2 * (1 - stats.norm.cdf(abs(z))))


def _pair_slopes(y: np.ndarray, t: np.ndarray) -> np.ndarray:
    ok = ~np.isnan(y)
    y, t = y[ok], t[ok]
    if len(y) < 2:
        return np.empty(0)
    i, j = np.triu_indices(len(y), k=1)
    dt = t[j] - t[i]
    keep = dt != 0
    return (y[j][keep] - y[i][keep]) / dt[keep]


def seasonal_kendall(values: np.ndarray, years: np.ndarray, months: np.ndarray) -> dict:
    """Seasonal Mann-Kendall test + seasonal Sen's slope (per year). NaNs are skipped per season."""
    s_tot, var_tot, d_tot, slopes, seasons_used = 0.0, 0.0, 0.0, [], 0
    for m in range(1, 13):
        sel = months == m
        order = np.argsort(years[sel])
        y = values[sel][order].astype(float)
        t = years[sel][order].astype(float)
        s, var, n = _mk_s_var(y)
        if n >= 2:
            seasons_used += 1
            s_tot += s
            var_tot += var
            d_tot += n * (n - 1) / 2
            slopes.append(_pair_slopes(y, t))
    z, p = _z_p(s_tot, var_tot)
    allslopes = np.concatenate(slopes) if slopes else np.empty(0)
    return {"s": s_tot, "var_s": var_tot, "z": z, "p_value": p,
            "tau": s_tot / d_tot if d_tot else np.nan,
            "slope_per_year": float(np.median(allslopes)) if len(allslopes) else np.nan,
            "seasons_used": seasons_used}


def _acf(x: np.ndarray, nlags: int) -> np.ndarray:
    x = x - x.mean()
    denom = np.sum(x * x)
    if denom == 0:
        return np.r_[1.0, np.zeros(nlags)]
    return np.array([1.0] + [np.sum(x[: len(x) - k] * x[k:]) / denom for k in range(1, nlags + 1)])


def hamed_rao_mk(values: np.ndarray, years: np.ndarray, alpha: float = ALPHA) -> dict:
    """Mann-Kendall with the Hamed & Rao (1998) autocorrelation correction + Sen's slope with 95% CI.

    The correction follows the common implementation (as in pymannkendall): ranks of the
    Sen-detrended series, significant autocorrelations at all lags inflate the variance of S.
    """
    ok = ~np.isnan(values)
    y, t = values[ok].astype(float), years[ok].astype(float)
    order = np.argsort(t)
    y, t = y[order], t[order]
    n = len(y)
    s, var, _ = _mk_s_var(y)
    if n >= 3:
        slope, intercept, lo, hi = stats.theilslopes(y, t, alpha=0.95)
        detrended = y - slope * np.arange(1, n + 1)
        ranks = stats.rankdata(detrended)
        acf = _acf(ranks, nlags=n - 1)
        bound = stats.norm.ppf(1 - alpha / 2) / math.sqrt(n)
        sni = sum((n - i) * (n - i - 1) * (n - i - 2) * acf[i]
                  for i in range(1, n - 1) if not (-bound <= acf[i] <= bound))
        n_ns = 1 + (2 / (n * (n - 1) * (n - 2))) * sni
        var = var * n_ns if n_ns > 0 else var
    else:
        slope = intercept = lo = hi = np.nan
    z, p = _z_p(s, var)
    return {"s": s, "var_s": var, "z": z, "p_value": p,
            "tau": s / (n * (n - 1) / 2) if n >= 2 else np.nan,
            "slope_per_year": float(slope), "slope_ci_low": float(lo), "slope_ci_high": float(hi),
            "n_years": n}


def fdr_bh(p_values) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values). NaNs stay NaN."""
    p = np.asarray(p_values, dtype=float)
    q = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    m = ok.sum()
    if m == 0:
        return q
    pv = p[ok]
    order = np.argsort(pv)
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


# --------------------------------------------------------------------------- main entry point
def _fmt_num(x: float) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    ax = abs(x)
    if ax == 0:
        return "0"
    if ax >= 100:
        return f"{x:,.0f}"
    return f"{x:.3g}"


def _fmt_p(p: Optional[float]) -> str:
    if p is None or not np.isfinite(p):
        return "n/a"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def trend_summary(series: pd.Series, start=None, end=None, freq: str = "monthly",
                  variable: Optional[str] = None, label: Optional[str] = None,
                  unit: Optional[str] = None, alpha: float = ALPHA) -> dict:
    """Trend test for one series over one window.

    series   monthly (PeriodIndex 'M' / DatetimeIndex) or yearly (PeriodIndex 'Y' / int years) values.
    start/end  window bounds, e.g. "2014-01" and "2025-12" (or years for yearly series); None = all.
    freq     "monthly" (Seasonal Mann-Kendall) or "annual" (Hamed-Rao Mann-Kendall on yearly means).
             Yearly series always use "annual".
    variable optional key of VARIABLES to fill label and unit.

    Returns a dict with: n_months, n_missing, missing_share, n_years, test, tau, p_value,
    slope_per_year, slope_ci_low/high (annual only), change_total, change_pct, direction,
    significant, intercept, t0 (decimal year the intercept refers to), window, warning, sentence.
    """
    if variable and variable in VARIABLES:
        label = label or VARIABLES[variable][0]
        unit = unit or VARIABLES[variable][1]
    label = label or "Value"
    unit = unit or ""

    s = _as_period_index(series).astype(float)
    yearly_input = _is_yearly(s)
    if yearly_input:
        freq = "annual"
        if start is not None:
            s = s[s.index >= pd.Period(str(start)[:4], freq="Y")]
        if end is not None:
            s = s[s.index <= pd.Period(str(end)[:4], freq="Y")]
        if len(s):
            s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="Y"))
    else:
        if start is not None:
            s = s[s.index >= pd.Period(str(start), freq="M")]
        if end is not None:
            s = s[s.index <= pd.Period(str(end), freq="M")]
        if len(s):
            lo = pd.Period(str(start), freq="M") if start is not None else s.index.min()
            hi = pd.Period(str(end), freq="M") if end is not None else s.index.max()
            s = s.reindex(pd.period_range(lo, hi, freq="M"))

    out = {"variable": variable, "label": label, "unit": unit, "freq": freq,
           "n_months": None, "n_missing": None, "missing_share": None, "n_years": None,
           "test": None, "tau": None, "p_value": None, "slope_per_year": None,
           "slope_ci_low": None, "slope_ci_high": None, "change_total": None, "change_pct": None,
           "direction": None, "significant": False, "intercept": None, "t0": None,
           "window": None, "warning": None, "sentence": None}

    if len(s) == 0 or s.notna().sum() == 0:
        out.update(direction="no data", sentence=f"No {label.lower()} data in the selected window.")
        return out

    years = s.index.year.to_numpy()
    y0, y1 = int(years.min()), int(years.max())
    out["window"] = f"{s.index.min()} to {s.index.max()}"
    warnings_ = []

    if yearly_input:
        n_full_years = len(s)
        out.update(n_years=int(s.notna().sum()), n_missing=int(s.isna().sum()),
                   missing_share=float(s.isna().mean()))
    else:
        months = s.index.month.to_numpy()
        n_full_years = len(s) // 12
        out.update(n_months=int(len(s)), n_missing=int(s.isna().sum()), missing_share=float(s.isna().mean()))
        if out["missing_share"] > MISSING_WARN_SHARE:
            warnings_.append(f"{out['missing_share']:.0%} of months are missing (mostly cloud cover); "
                             "treat the result with caution.")

    if n_full_years < MIN_YEARS:
        out.update(direction="window too short", warning=" ".join(warnings_) or None,
                   sentence=f"Window too short: at least {MIN_YEARS} full years are needed for a trend test.")
        return out

    if freq == "monthly":
        r = seasonal_kendall(s.to_numpy(), years, months)
        out["test"] = "Seasonal Mann-Kendall (Hirsch et al. 1982) with seasonal Sen's slope"
        t = years + (months - 0.5) / 12.0
        baseline = np.nanmean(s.to_numpy()[:12])
        span = (t[-1] - t[0]) if len(t) > 1 else 0.0
        out["n_years"] = n_full_years
    elif freq == "annual":
        if yearly_input:
            ann = s
        else:
            g = s.groupby(s.index.year)
            ann = g.mean().where(g.count() >= ANNUAL_MIN_MONTHS)
            ann.index = pd.PeriodIndex(ann.index.astype(str), freq="Y")
            dropped = int(ann.isna().sum())
            if dropped:
                warnings_.append(f"{dropped} year(s) had fewer than {ANNUAL_MIN_MONTHS} valid months "
                                 "and were left out of the annual test.")
        if ann.notna().sum() < MIN_YEARS:
            out.update(direction="window too short", warning=" ".join(warnings_) or None,
                       sentence=f"Window too short: at least {MIN_YEARS} years with data are needed.")
            return out
        ay = ann.index.year.to_numpy().astype(float)
        r = hamed_rao_mk(ann.to_numpy(), ay, alpha=alpha)
        out["test"] = "Mann-Kendall with Hamed-Rao autocorrelation correction, Sen's slope"
        out.update(slope_ci_low=r["slope_ci_low"], slope_ci_high=r["slope_ci_high"], n_years=r["n_years"])
        t = ay + 0.5
        baseline = ann.dropna().iloc[0]
        valid_t = t[ann.notna().to_numpy()]
        span = (valid_t[-1] - valid_t[0]) if len(valid_t) > 1 else 0.0
        s = ann
    else:
        raise ValueError("freq must be 'monthly' or 'annual'")

    slope, p = r["slope_per_year"], r["p_value"]
    vals = s.to_numpy()
    ok = ~np.isnan(vals)
    t0 = float(t[ok][0])
    intercept = float(np.median(vals[ok] - slope * (t[ok] - t0))) if np.isfinite(slope) else None
    change_total = slope * span if np.isfinite(slope) else None
    change_pct = (100 * change_total / baseline) if (change_total is not None and baseline
                                                      and np.isfinite(baseline) and abs(baseline) > 1e-12) else None
    significant = bool(np.isfinite(p) and p < alpha)
    if significant:
        sign = np.sign(slope) if slope != 0 else np.sign(r["s"])
        direction = "increasing" if sign > 0 else "decreasing"
    else:
        direction = "no significant trend"

    out.update(tau=r["tau"], p_value=p, slope_per_year=slope, change_total=change_total,
               change_pct=change_pct, direction=direction, significant=significant,
               intercept=intercept, t0=t0, warning=" ".join(warnings_) or None)

    period = f"{y0}–{y1}"
    unit_txt = f" {unit}" if unit else ""
    pct_txt = f" ({change_pct:+.0f}% over {period})" if change_pct is not None else f" over {period}"
    if significant:
        verb = "increased" if direction == "increasing" else "decreased"
        out["sentence"] = (f"{label} {verb} by {_fmt_num(abs(slope))}{unit_txt} per year{pct_txt}; "
                           f"statistically significant ({_fmt_p(p)}).")
    else:
        out["sentence"] = (f"No statistically significant trend in {label.lower()} over {period} "
                           f"({_fmt_p(p)}; Sen's slope {_fmt_num(slope)}{unit_txt} per year).")
    return out


def trend_line(result: dict, index: pd.PeriodIndex) -> pd.Series:
    """Sen's-slope line for plotting over `index` (monthly or yearly PeriodIndex)."""
    if result.get("intercept") is None or result.get("slope_per_year") is None:
        return pd.Series(np.nan, index=index)
    if _is_yearly(pd.Series(index=index, dtype=float)):
        t = index.year.to_numpy() + 0.5
    else:
        t = index.year.to_numpy() + (index.month.to_numpy() - 0.5) / 12.0
    return pd.Series(result["intercept"] + result["slope_per_year"] * (t - result["t0"]), index=index)


# --------------------------------------------------------------------------- many regions at once
def region_trends(df: pd.DataFrame, region_col: str, variables: list[str], start=None, end=None,
                  freq: str = "monthly", alpha: float = ALPHA) -> pd.DataFrame:
    """Run trend_summary for every region x variable and add FDR-corrected q-values per variable.

    df must have columns region_col, year, (month for monthly variables) and the variables.
    Yearly variables (land-cover shares) are tested with the annual test automatically.
    """
    rows = []
    for var in variables:
        yearly = var in YEARLY_VARIABLES or "month" not in df.columns
        for region, g in df.groupby(region_col):
            ser = yearly_series(g, var) if yearly else monthly_series(g, var)
            r = trend_summary(ser, start=start, end=end, freq="annual" if yearly else freq,
                              variable=var, alpha=alpha)
            rows.append({region_col: region, "variable": var, "test": r["test"], "n_years": r["n_years"],
                         "missing_share": r["missing_share"], "p_value": r["p_value"], "tau": r["tau"],
                         "slope_per_year": r["slope_per_year"], "change_total": r["change_total"],
                         "change_pct": r["change_pct"], "direction_raw": r["direction"]})
    res = pd.DataFrame(rows)
    res["q_value"] = np.nan
    for var, idx in res.groupby("variable").groups.items():
        res.loc[idx, "q_value"] = fdr_bh(res.loc[idx, "p_value"].astype(float).to_numpy())
    res["significant"] = res["q_value"] < alpha
    res["direction"] = np.where(res["significant"],
                                np.where(res["slope_per_year"] > 0, "increasing", "decreasing"),
                                np.where(res["direction_raw"] == "window too short", "window too short",
                                         "no significant trend"))
    return res.drop(columns="direction_raw")
