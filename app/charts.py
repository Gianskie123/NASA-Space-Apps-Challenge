"""Figures shared by the pages: the province change map, the year-by-year chart, the bird charts and maps.

Every figure speaks plain words: colour bars say "Brighter / Darker", hovers say "about 33% higher than in
2014", axes say "darkest places / brightest places". Technical numbers stay in the scientist panels.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import load_data as ld
import plain
import ui
from config import FOCUS_AREA_LABEL, FOCUS_CENTER, FOCUS_PROVINCES, MAP_STYLE, PH_CENTER, PH_ZOOM, VARIABLES

NEUTRAL = "#eeeee9"
PRIORITY_LOW, PRIORITY_HIGH = "#f3c34b", "#b34700"


# ---------------------------------------------------------------- data shaping
@st.cache_data(show_spinner=False)
def variable_table(var: str) -> pd.DataFrame:
    """Long table: adm2_code, province, year, month, date, value for one variable."""
    lookup = ld.province_lookup()
    if VARIABLES[var]["table"] == "landcover":
        lc = ld.province_landcover()
        cols = ["adm2_code", "year", var] + (["province"] if "province" in lc.columns else [])
        df = lc[cols].rename(columns={var: "value"})
        df["month"] = 1
        if "province" not in df.columns:
            df = df.merge(lookup[["adm2_code", "province"]], on="adm2_code", how="left")
    else:
        df = ld.province_monthly(("province", "adm2_code", "year", "month", var)).rename(columns={var: "value"})
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df


def province_series(df: pd.DataFrame, province: str) -> pd.Series:
    if province == FOCUS_AREA_LABEL:
        s = df[df["province"].isin(FOCUS_PROVINCES)].groupby("date")["value"].mean()
    else:
        s = df[df["province"] == province].set_index("date")["value"]
    return s.sort_index()


def to_annual(s: pd.Series) -> pd.Series:
    """Yearly means; a year needs >= 9 valid months (the same rule trends.py applies)."""
    g = s.groupby(s.index.year)
    out = g.mean().where(g.count() >= 9)
    out.index = pd.to_datetime([f"{y}-07-01" for y in out.index])
    return out


# ---------------------------------------------------------------- province change map
def _province_table(var: str) -> pd.DataFrame | None:
    if not ld.available("province_trends.parquet"):
        return None
    pt = ld.province_trends()
    pt = pt[pt["variable"] == var].copy()
    if pt.empty:
        return None
    # Colour by relative change (% of the starting level), so rural provinces that doubled are as visible as a
    # city that grew by a large absolute amount. Land-cover shares use their slope (percentage points a year).
    pt["colour_value"] = pt["slope_per_year"] * 100 if var in plain.SHARE_VARIABLES else pt["change_pct"]
    pt["colour_value"] = pt["colour_value"].fillna(pt["slope_per_year"])
    return pt


def change_scale(var: str) -> dict | None:
    """Colour range shared by the map and its legend: lim (90th percentile of significant changes), whether
    any province rose or fell, and how to word the end values."""
    pt = _province_table(var)
    if pt is None:
        return None
    sig = pt[pt["significant"]]
    lim = float(np.nanpercentile(np.abs(sig["colour_value"]), 90)) if len(sig) else 1.0
    has_down = bool((sig["colour_value"] < 0).any())
    has_up = bool((sig["colour_value"] > 0).any())
    fmt = (lambda v: f"{v:.1f} points a year") if var in plain.SHARE_VARIABLES else (lambda v: f"{v:.0f}%")
    return {"lim": lim or 1.0, "has_down": has_down, "has_up": has_up, "fmt": fmt}


def _colorscale(var: str, sc: dict) -> tuple[list[list], float, float]:
    m = VARIABLES[var]
    if sc["has_down"] and sc["has_up"]:
        return [[0.0, m["down"]], [0.5, NEUTRAL], [1.0, m["up"]]], -sc["lim"], sc["lim"]
    if sc["has_down"]:
        return [[0.0, m["down"]], [1.0, NEUTRAL]], -sc["lim"], 0.0
    return [[0.0, NEUTRAL], [1.0, m["up"]]], 0.0, sc["lim"]


def change_map(var: str, highlight: str | None = None, height: int = 560, zoom: float = PH_ZOOM) -> go.Figure | None:
    """Every province coloured by its 2014-2025 trend; provinces without a clear trend are light grey."""
    pt = _province_table(var)
    if pt is None:
        return None
    sc = change_scale(var)
    cscale, zmin, zmax = _colorscale(var, sc)
    geo = ld.provinces_geojson()
    pt["verdict"] = [plain.verdict(var, d, s) for d, s in zip(pt["direction"], pt["significant"])]
    pt["phrase"] = [plain.change_phrase(var, r, "2014") for r in pt.to_dict("records")]
    sig = pt[pt["significant"]]
    fig = go.Figure()
    grey = pt[~pt["significant"]]
    if len(grey):
        fig.add_trace(go.Choroplethmap(
            geojson=geo, locations=grey["adm2_code"], featureidkey="properties.adm2_code", z=np.zeros(len(grey)),
            colorscale=[[0, ui.PALETTE["neutral"]], [1, ui.PALETTE["neutral"]]], showscale=False,
            marker_opacity=0.7, marker_line_width=0.5, marker_line_color="#ffffff",
            text=grey["province"], hovertemplate="<b>%{text}</b><br>No clear change<extra></extra>"))
    if len(sig):
        fig.add_trace(go.Choroplethmap(
            geojson=geo, locations=sig["adm2_code"], featureidkey="properties.adm2_code",
            z=sig["colour_value"].clip(zmin, zmax), zmin=zmin, zmax=zmax, colorscale=cscale, showscale=False,
            marker_opacity=0.9, marker_line_width=0.5, marker_line_color="#ffffff",
            text=sig["province"], customdata=np.c_[sig["verdict"], sig["phrase"]],
            hovertemplate="<b>%{text}</b><br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>"))
    if highlight:
        h = pt[pt["province"] == highlight] if highlight != FOCUS_AREA_LABEL else pt[pt["province"].isin(FOCUS_PROVINCES)]
        if len(h):
            fig.add_trace(go.Choroplethmap(
                geojson=geo, locations=h["adm2_code"], featureidkey="properties.adm2_code", z=np.zeros(len(h)),
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                marker_line_width=2.5, marker_line_color=ui.PALETTE["ink"], hoverinfo="skip"))
    fig.update_layout(map=dict(style=MAP_STYLE, center=PH_CENTER, zoom=zoom), margin=dict(l=0, r=0, t=0, b=0),
                      showlegend=False)
    return ui.style_fig(fig, height=height, legend_bottom=False)


def change_legend(var: str, container=None) -> None:
    """Plain legend for change_map with numbers at the ends, plus the grey 'no clear change' swatch."""
    sc = change_scale(var)
    if sc is None:
        return
    up_word, down_word = plain.short_words(var)
    m, v = VARIABLES[var], sc["fmt"](sc["lim"])
    extras = [(ui.PALETTE["neutral"], "No clear change")]
    if sc["has_down"] and sc["has_up"]:
        ui.gradient_legend(f"{down_word} (−{v} or more)", f"{up_word} (+{v} or more)", [m["down"], NEUTRAL, m["up"]],
                           extras=extras, container=container)
    elif sc["has_down"]:
        ui.gradient_legend(f"{down_word}: −{v} or more", "small fall", [m["down"], NEUTRAL], extras=extras,
                           container=container)
    else:
        ui.gradient_legend(f"{up_word}: small rise", f"+{v} or more", [NEUTRAL, m["up"]], extras=extras,
                           container=container)


def province_counts(var: str) -> dict | None:
    """How many provinces rose, fell or showed no clear change (FDR-corrected), and the Metro Manila row."""
    if not ld.available("province_trends.parquet"):
        return None
    pt = ld.province_trends()
    pt = pt[pt["variable"] == var]
    if pt.empty:
        return None
    up = int((pt["significant"] & (pt["slope_per_year"] > 0)).sum())
    down = int((pt["significant"] & (pt["slope_per_year"] < 0)).sum())
    mm = pt[pt["province"].isin(["National Capital Region", "Metropolitan Manila"])]
    return {"n": len(pt), "up": up, "down": down, "metro": mm.iloc[0].to_dict() if len(mm) else None}


# ---------------------------------------------------------------- year-by-year chart
def year_chart(s: pd.Series, var: str, result: dict | None, yearly_input: bool, line_fn) -> go.Figure:
    """Yearly values as dots joined by a line, with the fitted trend as a dashed line."""
    meta = VARIABLES[var]
    ys = s.copy() if yearly_input else to_annual(s)
    if yearly_input:
        ys.index = pd.to_datetime([f"{d.year}-07-01" for d in ys.index])
    values = ys * 100 if var in plain.SHARE_VARIABLES else ys
    unit = meta["plain_unit"]
    fig = go.Figure()
    fig.add_scatter(x=ys.index, y=values, mode="lines+markers", name="Yearly average",
                    line=dict(width=2, color=ui.PALETTE["ink2"]), marker=dict(size=7, color=ui.PALETTE["ink2"]),
                    hovertemplate="%{x|%Y}: %{y:.3g} " + unit + "<extra></extra>")
    if result and result.get("intercept") is not None and ys.notna().any():
        line = line_fn(result, ys.index)
        if var in plain.SHARE_VARIABLES:
            line = line * 100
        color = meta["up"] if (result.get("significant") and (result.get("slope_per_year") or 0) > 0) else (
            meta["down"] if result.get("significant") else ui.PALETTE["muted"])
        fig.add_scatter(x=line.index, y=line, mode="lines", name="Overall trend",
                        line=dict(width=3, color=color, dash="dash"), hoverinfo="skip")
    years = ys.index.year
    step = 1 if len(ys) <= 8 else 2
    if var == "alan" and 2020 in set(years):
        fig.add_annotation(x=pd.Timestamp("2020-07-01"), y=float(values.loc[values.index.year == 2020].iloc[0]),
                           text="2020: COVID lockdown", showarrow=True, arrowhead=0, ax=0, ay=36,
                           font=dict(size=12, color=ui.PALETTE["muted"]), arrowcolor=ui.PALETTE["muted"])
    fig.update_layout(margin=dict(l=0, r=10, t=36, b=44), yaxis_title=unit, hovermode="x unified",
                      legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", bgcolor="rgba(0,0,0,0)",
                                  font=dict(color=ui.PALETTE["ink2"])),
                      xaxis=dict(tickvals=list(ys.index[::step]), ticktext=[str(y) for y in years[::step]],
                                 tickangle=0, range=[f"{years.min()}-01-01", f"{years.max()}-12-31"]))
    return ui.style_fig(fig, height=360, legend_bottom=False)


# ---------------------------------------------------------------- birds
def effect_chart(ec: pd.DataFrame) -> go.Figure:
    """Chance of seeing a species on a typical one-hour birdwatch, from the darkest to the brightest places."""
    fig = go.Figure()
    for grp, sub in ec.groupby("group"):
        sub = sub.sort_values("alan").reset_index(drop=True)
        key = "Sensitive" if "sensitive" in str(grp).lower() else "Tolerant"
        name = "Birds that need darkness" if key == "Sensitive" else "Birds that tolerate light"
        color = ui.GROUP_COLORS[key]
        x = 5 + 90 * np.arange(len(sub)) / max(len(sub) - 1, 1)
        fig.add_scatter(x=np.r_[x, x[::-1]], y=np.r_[sub["ci_high"], sub["ci_low"][::-1]], fill="toself",
                        fillcolor=color, opacity=0.13, line=dict(width=0), hoverinfo="skip", showlegend=False)
        fig.add_scatter(x=x, y=sub["prob"], mode="lines", line=dict(color=color, width=3.5), name=name,
                        hovertemplate=name + ": %{y:.0%} chance<extra></extra>")
    top = float(ec["ci_high"].max()) * 1.06
    fig.update_layout(margin=dict(l=0, r=10, t=40, b=56), hovermode="x unified",
                      legend=dict(orientation="h", x=0, y=1.12, yanchor="bottom", bgcolor="rgba(0,0,0,0)",
                                  font=dict(size=13, color=ui.PALETTE["ink"])),
                      xaxis=dict(range=[2, 98], tickvals=[8, 50, 92], automargin=True,
                                 ticktext=["Darkest", "In between", "Brightest"],
                                 title=dict(text="Places, from darkest to brightest at night", standoff=8)),
                      yaxis=dict(range=[0, top], tickformat=".0%", title="Chance it is recorded"))
    return ui.style_fig(fig, height=420, legend_bottom=False)


def priority_map(pa: pd.DataFrame, height: int = 520) -> go.Figure:
    """Places where light-sensitive birds were recorded: amber where night light rose at least 1.5x."""
    fig = go.Figure()
    rest = pa[~pa["priority"]]
    pri = pa[pa["priority"]].sort_values("ratio")
    if len(rest):
        fig.add_trace(go.Scattermap(
            lat=rest["lat"], lon=rest["lon"], mode="markers", marker=dict(size=7, color="#8a909b", opacity=0.55),
            text=rest["locality"].fillna("Unnamed birding spot"), customdata=rest["ratio"],
            hovertemplate="<b>%{text}</b><br>Light-sensitive birds recorded<br>Night light ×%{customdata:.1f} "
                          "since 2014–16<extra></extra>"))
    if len(pri):
        fig.add_trace(go.Scattermap(
            lat=pri["lat"], lon=pri["lon"], mode="markers",
            marker=dict(size=11, color=pri["ratio"].clip(upper=4), colorscale=[[0, PRIORITY_LOW], [1, PRIORITY_HIGH]],
                        cmin=1.5, cmax=4, opacity=0.95, showscale=False),
            text=pri["locality"].fillna("Unnamed birding spot"), customdata=pri["ratio"],
            hovertemplate="<b>%{text}</b><br>Light-sensitive birds recorded<br>Night light ×%{customdata:.1f} "
                          "since 2014–16<extra>Priority</extra>"))
    fig.update_layout(map=dict(style=MAP_STYLE, center=FOCUS_CENTER, zoom=8.3), margin=dict(l=0, r=0, t=0, b=0),
                      showlegend=False)
    return ui.style_fig(fig, height=height, legend_bottom=False)


def priority_legend(container=None) -> None:
    ui.gradient_legend("1.5× brighter than 2014–16", "4× or more", [PRIORITY_LOW, PRIORITY_HIGH],
                       extras=[("#8a909b", "Rose less than ×1.5")], container=container)


def top_places(pa: pd.DataFrame, n: int = 8) -> list[tuple[str, str]]:
    """Named priority places with the largest rise in night light; near-duplicate names merged."""
    rows, seen = [], set()
    for r in pa[pa["priority"]].sort_values("ratio", ascending=False).itertuples():
        name = r.locality.strip() if isinstance(r.locality, str) else ""
        key = name.lower()[:14]
        if not name or key in seen:
            continue
        seen.add(key)
        rows.append((name, f"×{r.ratio:.1f}"))
        if len(rows) == n:
            break
    return rows
