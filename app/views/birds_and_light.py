"""What it means for birds: the finding in plain words, where to act, how sure we are.

Order: the finding (sentence + chart + example species), where to act (priority map + named places), how sure we
are, then two optional panels: explore the bird data (effort, reporting rates, satellite values; gaps drawn as
gaps, never zero) and the model details for scientists. Numbers come from the data files, never typed in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import charts
import load_data as ld
import plain
import ui
from config import (FIRST_YEAR, FOCUS_CENTER, GAP_COLOR, GAP_LABEL, GITHUB_URL, GRID_VARIABLES, LAST_YEAR,
                    MAP_STYLE, VARIABLES)


def p_txt(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


n_ck = ld.n_checklists() if ld.available("checklists.parquet") else None
ui.page_header("What it means for birds",
               "Greater Manila, 2014–2025. We compared birdwatcher records with NASA night-light data to see which "
               "birds lose out where nights get brighter."
               + (f" Based on {n_ck:,} complete birdwatching checklists from eBird." if n_ck else ""))

# ---------------------------------------------------------------- the finding
ec = ld.effect_curve() if ld.available("effect_curve.parquet") else None
head = plain.bird_headline(ec) if ec is not None else None
sp = ld.species() if ld.available("species.parquet") else pd.DataFrame()
focus = sp[sp["focus"]] if not sp.empty else sp

c_txt, c_fig = st.columns([2, 3], gap="large")
with c_txt:
    ui.section("The finding")
    if head:
        ui.insight(head["text"], meta="Predicted for a typical one-hour birdwatch by one person in the morning, "
                                      "taking birdwatching effort, season, forest, heat and rain into account.")
    else:
        ui.alert("The finding is not available right now.", kind="pending")
    if not focus.empty:
        def examples(tol: str) -> str:
            f = focus[(focus["light_tolerance"].astype(str).str.lower() == tol)
                      & (focus["migratory_status"].astype(str).str.lower() == "resident")]
            return ", ".join(f.nlargest(5, "n_detections")["species"].astype(str))
        ui.legend("Which birds?", [
            (ui.GROUP_COLORS["Sensitive"], "Birds that need darkness", f"For example {examples('sensitive')}."),
            (ui.GROUP_COLORS["Tolerant"], "Birds that tolerate light", f"For example {examples('tolerant')}."),
        ], note="Groups follow the light-tolerance list from the team's Avilight project.")
with c_fig:
    ui.section("Chance of seeing a bird, from dark to bright places")
    if ec is not None:
        st.plotly_chart(charts.effect_chart(ec), width="stretch", config=ui.CHART_CONFIG)
        ui.gloss("Shaded bands show the range we are 95% sure the true value lies in.")

# ---------------------------------------------------------------- where to act
pa = ld.priority_areas()
ui.section("Where to act",
           "Each dot is a 1 km area where birdwatchers recorded birds that need darkness. Orange dots are where "
           "nights are now at least 1.5× as bright as in 2014–16: these are the places to protect first.")
if pa is None:
    ui.alert("The places map is not available right now.", kind="pending")
else:
    c_map, c_list = st.columns([3, 1], gap="medium")
    with c_map:
        st.plotly_chart(charts.priority_map(pa, height=560), width="stretch", config=ui.MAP_CONFIG)
        charts.priority_legend()
    with c_list:
        n_pri = int(pa["priority"].sum())
        ui.places("Fastest-brightening bird places", charts.top_places(pa, 9),
                  note=f"{n_pri} of {len(pa)} places with birds that need darkness are now at least 1.5× as bright "
                       "at night. Names are birdwatchers' own place labels. This map describes what was recorded; "
                       "it is not a prediction.")

# ---------------------------------------------------------------- how sure
ui.section("How sure are we?")
bullets = []
rb = ld.robustness()
if rb is not None and len(rb) > 1:
    refits = rb.iloc[1:]
    held = int(((refits["interaction_or"] < 1) & (refits["p_value"] < 0.05)).sum())
    bullets.append(("The pattern holds up",
                    f"It stayed the same in {held} of {len(refits)} extra checks with different data filters and model "
                    "choices, and it is very unlikely to be chance."))
bs = ld.by_status()
if bs is not None:
    mig = bs[bs["status"] == "Migrant"]
    p_mig = float(mig["p_sensitive_vs_tolerant"].iloc[0]) if len(mig) else 1.0
    bullets.append(("Resident birds are hit hardest",
                    "The difference comes from birds that live here all year. "
                    + ("Migratory birds that need darkness and those that tolerate light respond about the same."
                       if p_mig >= 0.05 else "Migratory birds show a smaller difference.")))
bullets.append(("Light is a warning sign, not the whole story",
                "Brighter places are also more built-up and noisier, so we cannot say light is the only cause. "
                "What we can say: where nights get brighter, these birds are seen much less."))
bullets.append(("Missing data is not counted as missing birds",
                "Places nobody birdwatched are left blank, never treated as zero birds."))
ui.numbered(bullets)

# ---------------------------------------------------------------- explore the bird data
water = ld.water_cells()


def with_geometry(values: pd.DataFrame, effort: pd.DataFrame, keep_observed_water: bool = True) -> pd.DataFrame:
    cells = effort.merge(values, on="cell_id", how="left")
    cells = cells.merge(ld.cell_centers(cells["cell_id"]), on="cell_id")
    cells["water"] = cells["cell_id"].isin(water) if water is not None else False
    if water is not None:
        cells = cells[~cells["water"] | (keep_observed_water & ~cells["is_gap"])]
    cells["label"] = np.where(cells["water"], cells["cell_id"] + " (mostly water)", cells["cell_id"])
    return cells


def range_of(v: pd.Series) -> tuple[float, float]:
    v = v.dropna()
    return (float(np.nanpercentile(v, 2)), float(np.nanpercentile(v, 98))) if len(v) else (0.0, 1.0)


def build_map(cells: pd.DataFrame, unit: str, cscale: str, crange: tuple[float, float], rated_only: bool,
              show_gaps: bool) -> go.Figure:
    shown = cells[cells["value"].notna() & ~cells["is_gap"]] if rated_only else (
        cells[~cells["is_gap"]] if show_gaps else cells)
    thin = cells[~cells["is_gap"] & cells["value"].isna()] if rated_only else cells.iloc[0:0]
    gaps = cells[cells["is_gap"]] if show_gaps else cells.iloc[0:0]
    fig = go.Figure()
    if len(gaps):
        fig.add_trace(go.Scattermap(lat=gaps["lat"], lon=gaps["lon"], mode="markers",
                                    marker=dict(size=5, color=GAP_COLOR, opacity=0.35), hoverinfo="skip"))
    if len(thin):
        fig.add_trace(go.Scattermap(lat=thin["lat"], lon=thin["lon"], mode="markers",
                                    marker=dict(size=6, color="#8a909b", opacity=0.8), hoverinfo="skip"))
    if len(shown):
        fig.add_trace(go.Scattermap(
            lat=shown["lat"], lon=shown["lon"], mode="markers",
            marker=dict(size=7, color=shown["value"], colorscale=cscale, cmin=crange[0], cmax=crange[1], opacity=0.92,
                        colorbar=dict(title=dict(text=unit, side="right"), thickness=12)),
            customdata=shown[["n_checklists"]],
            hovertemplate="%{marker.color:.3g} " + unit + "<br>%{customdata[0]:,} checklists<extra></extra>"))
    fig.update_layout(map=dict(style=MAP_STYLE, center=FOCUS_CENTER, zoom=8.3), margin=dict(l=0, r=0, t=0, b=0),
                      showlegend=False)
    return ui.style_fig(fig, height=560, legend_bottom=False)


with st.expander("Explore the bird data: where people birdwatched, what they recorded, and the satellite values"):
    modes = {"Where people birdwatched": "effort", "How often birds were recorded": "rate",
             "Satellite values": "cov"}
    if not ld.available("cell_rates.parquet"):
        modes.pop("How often birds were recorded")
    mode = modes[st.segmented_control("Show", list(modes), default="Where people birdwatched", key="bl_mode")
                 or "Where people birdwatched"]
    if mode == "effort":
        eff = ld.effort_by_cell()
        vals = eff[["cell_id"]].assign(value=np.log10(eff["n_checklists"].where(eff["n_checklists"] > 0)))
        cells = with_geometry(vals, eff)
        fig = build_map(cells, "checklists", "Viridis", range_of(cells["value"]), rated_only=False, show_gaps=True)
        tick = [1, 10, 100, 1000]
        fig.update_traces(selector=dict(type="scattermap"), marker_colorbar=dict(
            tickvals=np.log10(tick), ticktext=[f"{t:,}" for t in tick], title=dict(text="checklists", side="right")))
        note = "Colour: number of complete birdwatching checklists, 2014–2025."
    elif mode == "rate":
        rates = ld.cell_rates()
        c1, c2 = st.columns(2)
        group = c1.radio("Birds", ["Sensitive", "Tolerant"], horizontal=True, key="bl_group",
                         format_func=lambda g: "Need darkness" if g == "Sensitive" else "Tolerate light")
        periods = sorted(rates["period"].unique())
        period = c2.radio("Years", periods, index=len(periods) - 1, horizontal=True, key="bl_period",
                          format_func=lambda p: p.replace("-", "–"))
        y0, y1 = (int(x) for x in period.split("-"))
        sel = rates[(rates["group"] == group) & (rates["period"] == period)]
        cells = with_geometry(sel[["cell_id", "reporting_rate"]].rename(columns={"reporting_rate": "value"}),
                              ld.effort_by_cell((y0, y1)))
        fig = build_map(cells, "share recorded", "Viridis", range_of(cells["value"]), rated_only=True, show_gaps=True)
        note = ("Colour: how often these birds were recorded on a checklist (places with 5 or more checklists). "
                "Dark grey: birdwatched, but too few checklists to say.")
    else:
        c1, c2 = st.columns(2)
        gvar = c1.selectbox("Measurement", GRID_VARIABLES, format_func=lambda k: VARIABLES[k]["plain"], key="bl_gvar")
        year = c2.select_slider("Year", options=list(range(FIRST_YEAR, LAST_YEAR + 1)), value=LAST_YEAR, key="bl_year")
        meta = VARIABLES[gvar]
        ga = ld.grid_annual(("cell_id", "year", gvar))
        vals = ga[ga["year"] == year][["cell_id", gvar]].rename(columns={gvar: "value"})
        cells = with_geometry(vals, ld.effort_by_cell((year, year)), keep_observed_water=False)
        fig = build_map(cells, meta["unit"], meta["colorscale"], range_of(cells["value"]), rated_only=False,
                        show_gaps=False)
        note = f"Colour: yearly average per 1 km cell. Source: {meta['source']}."
    st.plotly_chart(fig, width="stretch", config=ui.MAP_CONFIG)
    gap_note = "" if mode == "cov" else f" Light grey: {GAP_LABEL.lower()}."
    ui.gloss(ui.escape(note + gap_note + " Open water is hidden."))

# ---------------------------------------------------------------- for scientists
with st.expander("For scientists: model, robustness and spatial checks"):
    coefs = ld.model_coefficients()
    if coefs and coefs[1] == "full":
        co = coefs[0].set_index("term")
        tiles = []
        for term, label in [("z_log_alan (sensitive)", "Light-sensitive species"),
                            ("z_log_alan", "Light-tolerant species"),
                            ("z_log_alan:sensitive", "Difference (interaction)")]:
            if term in co.index:
                r = co.loc[term]
                tiles.append(ui.stat_html(label, f"{r['odds_ratio']:.2f}×",
                                          desc=f"odds ratio per 1 SD of log night light; 95% CI {r['ci_low']:.2f}–"
                                               f"{r['ci_high']:.2f}, {p_txt(r['p_value'])}"))
        ui.stats_row(tiles)
    ui.gloss("Binomial GLM (logistic regression) on checklist × trait-group counts, cell-clustered standard errors, "
             "≤ 2 km checklists with hotspot thinning; covariates: log night light × sensitivity, forest share, "
             "daytime LST, rain, effort terms, month and year. NDVI and urban share left out (|r| &gt; 0.7 with "
             "night light).")
    if rb is not None:
        st.dataframe(rb.rename(columns={"variant": "Check", "interaction_or": "Interaction OR",
                                        "p_value": "p", "n_checklists": "Checklists"})
                     [["Check", "Interaction OR", "p", "Checklists"]].round(4), hide_index=True, width="stretch")
    sc = ld.spatial_checks()
    if sc is not None:
        ui.gloss("Moran's I (999 permutations): " + "; ".join(
            f"{ui.escape(str(r['test']))} I = {r['moran_i']:.2f}" for _, r in sc.iterrows())
                 + ". Gaps cluster in space, so they are kept blank rather than filled. Residuals stay clustered; "
                   "with 5×5-cell block clusters the interaction is still p ≤ 0.001.")
    st.markdown(f"Full write-up: [findings.md on GitHub]({GITHUB_URL}/blob/main/data/processed/findings.md)")
