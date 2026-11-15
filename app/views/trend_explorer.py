"""Page 1: Trend Explorer (meets Challenge 2).

Order: the controls, then the answer for the selection (direction, size, units, window and significance
together), then the evidence (that province's time series), then where else it changed (two maps).
All statistics come from Member 3's src/trends.py through trend_bridge.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import load_data as ld
import trend_bridge
import ui
from config import FOCUS_AREA_LABEL, FOCUS_PROVINCES, MAP_STYLE, VARIABLES

log = logging.getLogger(__name__)
PH_CENTER, PH_ZOOM = {"lat": 12.3, "lon": 122.3}, 4.2
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PRESETS = {"All years": None, "Last 10 years": 10, "Last 5 years": 5, "Custom": "custom"}


def sig3(x: pd.Series) -> pd.Series:
    """Round to 3 significant digits to keep the browser payload small (display only)."""
    x = pd.to_numeric(x, errors="coerce").astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        mag = np.where((x == 0) | ~np.isfinite(x), 0, np.floor(np.log10(np.abs(x))))
    return pd.Series(np.round(x / 10**mag, 2) * 10**mag, index=x.index)


def fmt(v, unit: str = "", signed: bool = False) -> str:
    if v is None or not np.isfinite(v):
        return "–"
    s = f"{v:+.3g}" if signed else f"{v:.3g}"
    return f"{s} {unit}".strip()


def fmt_p(p) -> str:
    if p is None or not np.isfinite(p):
        return "–"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


@st.cache_data(show_spinner=False)
def variable_table(var: str) -> pd.DataFrame:
    """Long table: adm2_code, province, year, month, date, value for one variable."""
    lookup = ld.province_lookup()
    if VARIABLES[var]["table"] == "landcover":
        df = ld.province_landcover()[["adm2_code", "year", var]].rename(columns={var: "value"})
        df["month"] = 1
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
    """Yearly means for display; a year needs >= 9 valid months (the same rule trends.py applies)."""
    g = s.groupby(s.index.year)
    out = g.mean().where(g.count() >= 9)
    out.index = pd.to_datetime([f"{y}-01-01" for y in out.index])
    return out


def time_window(periods: list[pd.Timestamp], is_lc: bool) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Preset chips for the common windows; Custom opens From / To pickers. Returns (start, end)."""
    first, last = periods[0], periods[-1]
    years = list(range(first.year, last.year + 1))
    choice = st.pills("Time window", list(PRESETS), default="All years", key="tw_preset",
                      help="A trend test needs at least 3 full years.") or "All years"
    n = PRESETS[choice]
    if n is None:
        return first, last
    if n != "custom":
        return max(first, pd.Timestamp(year=last.year - n + 1, month=1, day=1)), last
    # To only offers dates on or after From, so an inverted window cannot be picked.
    c1, c2, c3, c4 = st.columns(4, gap="small")
    y0 = c1.selectbox("From year", years, index=0, key="tw_y0")
    m0 = 1 if is_lc else MONTHS.index(c2.selectbox("From month", MONTHS, index=0, key="tw_m0")) + 1
    to_years = [y for y in years if y >= y0]
    y1 = c3.selectbox("To year", to_years, index=len(to_years) - 1, key="tw_y1")
    if is_lc:
        m1 = 1
    else:
        to_months = MONTHS[m0 - 1:] if y1 == y0 else MONTHS
        m1 = MONTHS.index(c4.selectbox("To month", to_months, index=len(to_months) - 1, key="tw_m1")) + 1
    return max(first, pd.Timestamp(year=y0, month=m0, day=1)), min(last, pd.Timestamp(year=y1, month=m1, day=1))


# ---------------------------------------------------------------- header
ui.page_header("Trend Explorer",
               "Pick a NASA satellite measurement, a province and a time window. The page tells you whether it "
               "changed, by how much per year, and whether the change is statistically significant.")

satellite_src = "mock" if ld.is_mock("province_monthly.parquet") else "satellite"
if satellite_src == "mock":
    ui.alert("<b>Mock data on this page.</b> Member 2's NASA tables are not in yet, so the maps and numbers below "
             "are placeholders that show how the page works. They are not results.", kind="warn", html=True)

# ---------------------------------------------------------------- controls, next to what they change
with st.container(border=True):
    c_var, c_prov, c_test = st.columns([4, 4, 3], gap="medium")
    var = c_var.selectbox("Measurement", list(VARIABLES),
                          format_func=lambda k: f"{VARIABLES[k]['label']} ({VARIABLES[k]['unit']})")
    meta = VARIABLES[var]
    is_lc = meta["table"] == "landcover"
    df = variable_table(var)
    provinces = sorted(df["province"].dropna().unique())
    province = c_prov.selectbox("Province", [FOCUS_AREA_LABEL, *provinces], index=0,
                                help="Type to search. The focus area is the Greater Manila bird study box.")
    if is_lc:
        freq = "annual"
        c_test.markdown('<div class="av-gloss" style="margin-top:28px">Land cover is yearly, so it uses the '
                        'annual test.</div>', unsafe_allow_html=True)
    else:
        freq = c_test.radio("Test on", ["monthly", "annual"], horizontal=True,
                            format_func=lambda f: "Monthly values" if f == "monthly" else "Yearly means",
                            help="Monthly: Seasonal Mann–Kendall, which compares each month only with the same month "
                                 "in other years, so the monsoon cycle cannot fake a trend. Yearly means: Mann–Kendall "
                                 "with the Hamed–Rao correction for year-to-year dependence.")
    periods = [pd.Timestamp(p) for p in sorted(df["date"].unique())]
    start, end = time_window(periods, is_lc)

date_fmt = "%Y" if is_lc else "%b %Y"
start_lbl, end_lbl = start.strftime(date_fmt), end.strftime(date_fmt)
window = df[(df["date"] >= start) & (df["date"] <= end)].copy()
s_full = province_series(df, province)
s = s_full[(s_full.index >= start) & (s_full.index <= end)]

# ---------------------------------------------------------------- the answer
ui.section(f"{meta['label']} in {province}", sub=f"{start_lbl} to {end_lbl}", source=satellite_src)

result, failed = None, False
if trend_bridge.TREND_AVAILABLE:
    try:
        result = trend_bridge.summarize(s, start, end, freq, yearly=is_lc, label=meta["label"], unit=meta["unit"])
    except Exception:  # never show a traceback or local path to visitors
        log.exception("trend_summary failed for %s / %s", var, province)
        failed = True

n_total, n_valid = len(s), int(s.notna().sum())
steps = "years" if is_lc else "months"
coverage_tile = ui.stat_html("Data coverage", f"{(n_valid / n_total if n_total else 0):.0%}",
                             desc=f"{n_valid} of {n_total} {steps} have usable data")

if not trend_bridge.TREND_AVAILABLE:
    ui.alert("<b>Trend test pending.</b> Member 3's <code>src/trends.py</code> is not in the repo yet; direction, "
             "rate and significance appear here once it is.", kind="pending", html=True)
    ui.stats_row([coverage_tile])
elif failed:
    ui.alert("The trend test could not run for this selection. Try another window or province.", kind="danger")
    ui.stats_row([coverage_tile])
elif result:
    direction = str(result.get("direction") or "")
    if result.get("warning"):
        ui.alert(result["warning"], kind="warn")
    if direction in ("window too short", "no data"):
        ui.alert(f"<b>{ui.escape(result.get('sentence') or 'No result.')}</b> Widen the time window.",
                 kind="warn", html=True)
        ui.stats_row([coverage_tile])
    else:
        significant = bool(result.get("significant"))
        slope, pct = result.get("slope_per_year"), result.get("change_pct")
        ci = ""
        if result.get("slope_ci_low") is not None and result.get("slope_ci_high") is not None:
            ci = f" (95% CI {fmt(result['slope_ci_low'])} to {fmt(result['slope_ci_high'])})"
        used = result.get("n_months") if not is_lc else result.get("n_years")
        missing = result.get("n_missing") or 0
        mock_note = " Computed on mock data, so this is not a result." if satellite_src == "mock" else ""
        ui.insight(result.get("sentence") or "", meta=f"{result.get('test', '')}.{mock_note}")
        ui.stats_row([
            ui.stat_html("Direction", direction.capitalize(), accent=significant,
                         desc=f"{fmt_p(result.get('p_value'))}; "
                              + ("significant at the 5% level" if significant else "not significant at the 5% level")),
            ui.stat_html("Rate of change", fmt(slope, signed=True), aside=f"{meta['unit']} per year",
                         desc=f"Sen's slope{ci}"),
            ui.stat_html("Total change", fmt(result.get("change_total"), signed=True), aside=meta["unit"],
                         desc=(f"{pct:+.1f}% of the starting level" if pct is not None and np.isfinite(pct)
                               else "No percentage: the starting level is near zero")),
            ui.stat_html("Window", f"{start_lbl} to {end_lbl}", compact=True,
                         desc=f"{used or 0} {steps} used, {missing} missing (cloud or no data)"),
        ])
        ui.gloss("<b>Sen's slope</b> is the median rate of change, so a few unusual months cannot drag it. "
                 "<b>p</b> is the chance of a trend this strong appearing by luck alone; below 0.05 we call it "
                 "significant. This tests one province on its own; the map further down corrects for testing "
                 "every province at once.")

# ---------------------------------------------------------------- evidence: the time series
ui.section("The evidence", sub=f"{meta['label']} ({meta['unit']}), {province}", source=satellite_src)
if province == FOCUS_AREA_LABEL:
    st.caption("The focus-area series is the plain average of the provinces in the Greater Manila box, "
               "until a dedicated focus-area series is delivered.")
ts = go.Figure()
yearly_plot = freq == "annual" or is_lc
plot_s = to_annual(s) if (freq == "annual" and not is_lc) else s
ts.add_scatter(x=plot_s.index, y=sig3(plot_s), mode="lines+markers" if yearly_plot else "lines",
               name="Yearly value" if is_lc else ("Yearly mean" if freq == "annual" else "Monthly value"),
               line=dict(width=1.5, color=ui.PALETTE["muted"]), opacity=0.9 if yearly_plot else 0.75,
               hovertemplate="%{x|" + ("%Y" if yearly_plot else "%b %Y") + "}: %{y:.3g} " + meta["unit"] + "<extra></extra>")
if not yearly_plot:
    ts.add_scatter(x=s.index, y=sig3(s.rolling(12, min_periods=9).mean()), mode="lines",
                   name="12-month rolling mean", line=dict(width=2, color=ui.PALETTE["accent_soft"]),
                   hovertemplate="12-month mean: %{y:.3g}<extra></extra>")
if result and result.get("intercept") is not None and plot_s.notna().any():
    line = trend_bridge.trend_line(result, plot_s.index, yearly=yearly_plot)
    ts.add_scatter(x=line.index, y=line, mode="lines", name="Trend (Sen's slope)",
                   line=dict(width=2.5, color=ui.PALETTE["accent"]),
                   hovertemplate="Trend: %{y:.3g}<extra></extra>")
ts.update_layout(margin=dict(l=0, r=0, t=16, b=0), yaxis_title=meta["unit"], hovermode="x unified")
ui.style_fig(ts, height=360)
st.plotly_chart(ts, width="stretch")
ui.gloss(f"Grey: the measured values. Light blue: a 12-month rolling mean that smooths out the seasons. "
         f"Blue: the fitted trend. Source: {ui.escape(meta['source'])}.")

# ---------------------------------------------------------------- where else it changed
geo = ld.provinces_geojson()
c_left, c_right = st.columns(2, gap="medium")

with c_left:
    ui.section("Month by month", sub="all provinces", source=satellite_src)
    all_vals = df["value"].dropna()
    crange = (float(np.percentile(all_vals, 2)), float(np.percentile(all_vals, 98)))  # fixed over ALL frames
    anim = window.dropna(subset=["value"]).sort_values("date").copy()
    anim["frame"] = anim["date"].dt.strftime("%Y" if is_lc else "%Y-%m")
    anim["value"] = sig3(anim["value"])
    fig = px.choropleth_map(
        anim, geojson=geo, locations="adm2_code", featureidkey="properties.adm2_code",
        color="value", animation_frame="frame", hover_name="province",
        hover_data={"adm2_code": False, "frame": True, "value": ":.3g"},
        range_color=crange, color_continuous_scale=meta["colorscale"],
        map_style=MAP_STYLE, center=PH_CENTER, zoom=PH_ZOOM, opacity=0.85,
        labels={"value": meta["unit"], "frame": "Year" if is_lc else "Month"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=8, b=0), coloraxis_colorbar=dict(title=meta["unit"], thickness=12))
    ui.style_fig(fig, height=520, legend_bottom=False)
    st.plotly_chart(fig, width="stretch", config=ui.MAP_CONFIG)
    st.caption(f"Press play to animate. The colour scale is fixed across all {len(periods)} frames, so a colour "
               f"means the same value in every frame.")

with c_right:
    trends_src = {"real": "model", "mock": "mock", "pending": "pending"}.get(ld.status("province_trends.parquet"))
    ui.section("Where it changed", sub="2014–2025, every province tested", source=trends_src)
    if not ld.available("province_trends.parquet"):
        ui.alert("Pending: Member 3 builds this map from Member 2's province tables, which are not in yet.",
                 kind="pending")
    else:
        pt = ld.province_trends()
        pt = pt[pt["variable"] == var].copy()
        if pt.empty:
            ui.alert(f"No province results for {meta['label']} yet.", kind="pending")
        else:
            pt["slope"] = np.where(pt["significant"], sig3(pt["slope_per_year"]), np.nan)
            lim = float(np.nanmax(np.abs(pt["slope"]))) if pt["slope"].notna().any() else 1.0
            sig = pt[pt["significant"]]
            wfig = px.choropleth_map(
                sig, geojson=geo, locations="adm2_code", featureidkey="properties.adm2_code",
                color="slope", hover_name="province",
                hover_data={"slope_per_year": ":.3g", "change_pct": ":.1f", "q_value": ":.3g", "adm2_code": False,
                            "slope": False},
                color_continuous_scale="RdBu_r", range_color=(-lim, lim),
                map_style=MAP_STYLE, center=PH_CENTER, zoom=PH_ZOOM, opacity=0.85,
                labels={"slope": f"{meta['unit']}/yr", "slope_per_year": "Sen's slope per year",
                        "change_pct": "Change %", "q_value": "q (FDR-corrected p)"},
            )
            grey = pt[~pt["significant"]]
            if not grey.empty:
                wfig.add_trace(go.Choroplethmap(
                    geojson=geo, locations=grey["adm2_code"], featureidkey="properties.adm2_code",
                    z=np.zeros(len(grey)), colorscale=[[0, ui.PALETTE["muted"]], [1, ui.PALETTE["muted"]]],
                    showscale=False, marker_opacity=0.55, text=grey["province"],
                    hovertemplate="%{text}<br>no significant trend<extra></extra>",
                    name="No significant trend", showlegend=True,
                ))
            wfig.update_layout(margin=dict(l=0, r=0, t=8, b=0),
                               coloraxis_colorbar=dict(title=f"Sen's slope<br>{meta['unit']}/yr", thickness=12),
                               legend=dict(y=0.02, x=0.02, bgcolor=ui.PALETTE["paper2"],
                                           font=dict(color=ui.PALETTE["ink2"])))
            ui.style_fig(wfig, height=520, legend_bottom=False)
            st.plotly_chart(wfig, width="stretch", config=ui.MAP_CONFIG)
            st.caption(f"{int(pt['significant'].sum())} of {len(pt)} provinces changed significantly (coloured); "
                       "grey means no significant trend. Corrected for testing every province at once "
                       "(false discovery rate).")
