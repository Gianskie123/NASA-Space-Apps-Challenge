"""What's changing (meets Challenge 2): what changed, where, by how much, and how sure we are.

Order: three plain controls, the answer in words, the evidence year by year, then the whole country on one map.
The test details (Seasonal Mann-Kendall, Sen's slope, p-values, coverage, the monthly animation) sit in the
"For scientists" panel. All statistics come from src/trends.py through trend_bridge.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts
import load_data as ld
import plain
import trend_bridge
import ui
from config import FOCUS_AREA_LABEL, MAP_STYLE, PH_CENTER, PH_ZOOM, VARIABLES

log = logging.getLogger(__name__)


def fmt(v, signed: bool = False) -> str:
    if v is None or not np.isfinite(v):
        return "–"
    return f"{v:+.3g}" if signed else f"{v:.3g}"


def fmt_p(p) -> str:
    if p is None or not np.isfinite(p):
        return "–"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def animated_map(anim: pd.DataFrame, geo: dict, meta: dict, crange: tuple[float, float], step_word: str) -> go.Figure:
    """Province choropleth with one frame per month (or year). Boundaries are sent once; each frame carries only
    that month's values, so the browser receives under 2 MB instead of ~74 MB."""
    frames_order = list(dict.fromkeys(anim["frame"]))
    by_frame = {f: g for f, g in anim.groupby("frame", sort=False)}
    hover = "%{text}<br>" + step_word + " %{customdata}: %{z:.3g} " + meta["unit"] + "<extra></extra>"

    def trace_for(f: str, full: bool):
        g = by_frame[f]
        kw = dict(locations=g["adm2_code"], z=g["value"], text=g["province"], customdata=[f] * len(g))
        if full:
            kw.update(geojson=geo, featureidkey="properties.adm2_code", colorscale=meta["colorscale"],
                      zmin=crange[0], zmax=crange[1], marker_opacity=0.85, marker_line_width=0.4,
                      hovertemplate=hover, colorbar=dict(title=meta["unit"], thickness=12))
        return go.Choroplethmap(**kw)

    fig = go.Figure(data=[trace_for(frames_order[0], full=True)],
                    frames=[go.Frame(name=f, data=[trace_for(f, full=False)], traces=[0]) for f in frames_order])
    play = dict(frame=dict(duration=250, redraw=True), fromcurrent=True, transition=dict(duration=0))
    fig.update_layout(
        map=dict(style=MAP_STYLE, center=PH_CENTER, zoom=PH_ZOOM), margin=dict(l=0, r=0, t=8, b=88),
        updatemenus=[dict(type="buttons", direction="left", x=0.0, y=0.0, xanchor="left", yanchor="top",
                          pad=dict(t=36, r=8), showactive=False,
                          buttons=[dict(label="Play", method="animate", args=[None, play]),
                                   dict(label="Pause", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])])],
        sliders=[dict(active=0, x=0.27, y=0.0, len=0.73, xanchor="left", yanchor="top", pad=dict(t=30, b=0),
                      currentvalue=dict(prefix=f"{step_word}: ", xanchor="right", offset=6),
                      steps=[dict(label=f, method="animate",
                                  args=[[f], dict(frame=dict(duration=0, redraw=True), mode="immediate")])
                             for f in frames_order])],
    )
    return fig


# ---------------------------------------------------------------- header and controls
ui.page_header("What's changing",
               "Pick something NASA satellites measure, a place and a span of years. We tell you whether it is "
               "really changing, by how much, and how sure we can be.")

with st.container(border=True):
    c_var, c_prov, c_years = st.columns([4, 4, 4], gap="medium")
    var = c_var.selectbox("What", list(VARIABLES), format_func=lambda k: VARIABLES[k]["plain"], key="te_var")
    meta = VARIABLES[var]
    is_lc = meta["table"] == "landcover"
    df = charts.variable_table(var)
    provinces = sorted(df["province"].dropna().unique())
    province = c_prov.selectbox("Where", [FOCUS_AREA_LABEL, *provinces], index=0, key="te_prov",
                                help="Type to search for a province.")
    years = sorted(df["year"].unique().astype(int))
    y0, y1 = c_years.select_slider("Years", options=years, value=(years[0], years[-1]), key="te_years")
    st.caption(f"{meta['plain']}: {meta['about']}.")

freq = "annual" if is_lc else st.session_state.get("te_freq", "monthly")
periods = [pd.Timestamp(p) for p in sorted(df["date"].unique())]
start = max(periods[0], pd.Timestamp(year=y0, month=1, day=1))
end = min(periods[-1], pd.Timestamp(year=y1, month=1 if is_lc else 12, day=1))
s_full = charts.province_series(df, province)
s = s_full[(s_full.index >= start) & (s_full.index <= end)]

if var == "lst_day":
    ui.alert("<b>Read with care.</b> The satellite behind this measurement (MODIS Terra) now passes over earlier in "
             "the morning than it used to, so the ground looks cooler from 2021 onward. Part of any cooling shown "
             "here comes from the satellite, not the weather.", kind="warn", html=True)

# ---------------------------------------------------------------- the answer
result, failed = None, False
if trend_bridge.TREND_AVAILABLE:
    try:
        result = trend_bridge.summarize(s, start, end, freq, yearly=is_lc, label=meta["label"], unit=meta["unit"])
    except Exception:  # never show a traceback or local path to visitors
        log.exception("trend_summary failed for %s / %s", var, province)
        failed = True

question = f"Is {meta['plain'].lower()} changing in {province}, {y0}–{y1}?"
if not trend_bridge.TREND_AVAILABLE or failed or not result:
    ui.verdict(question, "Not available", ["The trend test could not run for this choice. Try another place or "
                                           "span of years."])
else:
    direction = str(result.get("direction") or "")
    significant = bool(result.get("significant"))
    answer = plain.verdict(var, direction, significant)
    if direction == "window too short":
        ui.verdict(question, answer, ["Choose a span of at least 3 years to test for a trend."])
    elif direction == "no data":
        ui.verdict(question, answer, ["There is not enough satellite data for this place and span of years."])
    elif significant:
        color = meta["up"] if (result.get("slope_per_year") or 0) > 0 else meta["down"]
        ui.verdict(question, answer, [
            plain.change_phrase(var, result, str(y0)).capitalize() + ".",
            f"{plain.confidence(result.get('p_value'))} this is a real change, not chance.",
        ], color=color, muted_last=True)
    else:
        ui.verdict(question, answer, [
            "It goes up and down, but there is no steady trend we can be confident about.",
        ], muted_last=True)
    if result.get("warning"):
        ui.alert(result["warning"], kind="warn")

# ---------------------------------------------------------------- evidence
ui.section(f"Year by year in {province}",
           "Dots: the yearly average. Dashed line: the overall trend over the years you picked.")
fig = charts.year_chart(s, var, result, yearly_input=is_lc,
                        line_fn=lambda r, idx: trend_bridge.trend_line(r, idx, yearly=True))
st.plotly_chart(fig, width="stretch", config=ui.CHART_CONFIG)
if province == FOCUS_AREA_LABEL:
    ui.gloss("Greater Manila is the average of Metro Manila, Bulacan, Pampanga, Cavite, Laguna, Rizal and Bataan.")

# ---------------------------------------------------------------- where
up_word, down_word = plain.short_words(var)
ui.section("Across the Philippines",
           f"Every province, 2014–2025. The stronger the colour, the bigger the change. {province} is outlined.")
cmap = charts.change_map(var, highlight=province, height=620, zoom=PH_ZOOM + 0.25)
if cmap is None:
    ui.alert("Province results are not available right now.", kind="pending")
else:
    st.plotly_chart(cmap, width="stretch", config=ui.MAP_CONFIG)
    charts.change_legend(var)
    counts = charts.province_counts(var)
    if counts:
        ui.gloss(f"<b>{counts['up']}</b> provinces {up_word.lower()}, <b>{counts['down']}</b> {down_word.lower()}, "
                 f"<b>{counts['n'] - counts['up'] - counts['down']}</b> with no clear change. Each province was "
                 "tested separately, then checked so that testing 85 provinces at once does not create false alarms.")

# ---------------------------------------------------------------- for scientists
with st.expander("For scientists: test details, raw monthly data and the month-by-month animation"):
    if not is_lc:
        st.radio("Trend test", ["monthly", "annual"], horizontal=True, key="te_freq",
                 format_func=lambda f: "Seasonal Mann–Kendall on monthly values" if f == "monthly"
                 else "Mann–Kendall (Hamed–Rao) on yearly means")
    if result and result.get("direction") not in ("window too short", "no data", None):
        ci = ""
        if result.get("slope_ci_low") is not None and result.get("slope_ci_high") is not None:
            ci = f" (95% CI {fmt(result['slope_ci_low'])} to {fmt(result['slope_ci_high'])})"
        n_total, n_valid = len(s), int(s.notna().sum())
        ui.stats_row([
            ui.stat_html("Test", result.get("test", "–"), compact=True, desc=fmt_p(result.get("p_value"))),
            ui.stat_html("Sen's slope", fmt(result.get("slope_per_year"), signed=True), aside=f"{meta['unit']}/yr",
                         desc=f"Median rate of change{ci}"),
            ui.stat_html("Total change", fmt(result.get("change_total"), signed=True), aside=meta["unit"],
                         desc=(f"{result['change_pct']:+.1f}% of the first year's level"
                               if result.get("change_pct") is not None and np.isfinite(result["change_pct"]) else None)),
            ui.stat_html("Data coverage", f"{(n_valid / n_total if n_total else 0):.0%}",
                         desc=f"{n_valid} of {n_total} {'years' if is_lc else 'months'} usable (cloud gaps left blank)"),
        ])
        ui.gloss(f"{ui.escape(result.get('sentence') or '')} The map uses the full 2014–2025 window, with "
                 "Benjamini–Hochberg false-discovery-rate correction across provinces. Source: "
                 f"{ui.escape(meta['source'])}.")
    if not is_lc:
        raw = go.Figure()
        raw.add_scatter(x=s.index, y=s, mode="lines", line=dict(width=1.3, color=ui.PALETTE["muted"]), name="Monthly")
        raw.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title=meta["unit"], showlegend=False)
        st.plotly_chart(ui.style_fig(raw, height=260), width="stretch", config=ui.CHART_CONFIG)
    if st.toggle("Show the month-by-month animation of all provinces", key="te_anim"):
        geo = ld.provinces_geojson()
        window = df[(df["date"] >= start) & (df["date"] <= end)].dropna(subset=["value"]).sort_values("date").copy()
        all_vals = df["value"].dropna()
        crange = (float(np.percentile(all_vals, 2)), float(np.percentile(all_vals, 98)))
        window["frame"] = window["date"].dt.strftime("%Y" if is_lc else "%Y-%m")
        afig = animated_map(window, geo, meta, crange, "Year" if is_lc else "Month")
        st.plotly_chart(ui.style_fig(afig, height=520, legend_bottom=False), width="stretch", config=ui.MAP_CONFIG)
        st.caption("Press play. The colour scale is fixed across all frames, so a colour means the same value in "
                   "every month.")
