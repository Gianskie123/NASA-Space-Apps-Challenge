"""Page 2: Birds & Light (our addition), Greater Manila focus area.

Order: what the page asks, where people actually went birding (observed), what they reported (observed rates),
then what the model says. Sections running on real data name their source.
Gaps are drawn as gaps, never as zero; low-data cells are outlined and never get a rate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import load_data as ld
import ui
from config import FIRST_YEAR, FOCUS_CENTER, GAP_COLOR, GAP_LABEL, GRID_VARIABLES, LAST_YEAR, LOW_DATA_LABEL, MAP_STYLE, VARIABLES

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]
TERM_LABELS = {
    "z_log_alan": "Per 1 SD more night light, light-tolerant species",
    "z_alan": "Per 1 SD more night light, light-tolerant species",
    "z_log_alan:sensitive": "Extra night-light effect for light-sensitive species",
    "z_alan:sensitive": "Extra night-light effect for light-sensitive species",
    "sensitive": "Light-sensitive vs light-tolerant species",
    "year_c": "Per year, light-tolerant species",
    "year_c:sensitive": "Extra yearly change for light-sensitive species",
    "migrant": "Migrant vs resident species",
    "log_duration": "Longer checklist (per log-minute)",
    "distance_km": "Per km travelled",
    "n_observers": "Per extra observer",
    "hour_started": "Later start time (per hour)",
    "hour2": "Start time, squared term",
    "z_forest_frac": "Per 1 SD more forest cover",
    "z_ndvi": "Per 1 SD more vegetation",
    "z_lst_day": "Per 1 SD hotter land surface",
    "z_rain_mm": "Per 1 SD more rain",
}


def term_label(term: str, label: str | None = None) -> str:
    if isinstance(label, str) and label:
        return label
    if term.startswith("C(month)[T."):
        m = int(term.split("T.")[1].rstrip("]"))
        return f"{MONTH_NAMES[m]} vs January"
    return TERM_LABELS.get(term, term)


def p_txt(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def short_headline() -> tuple[str, str] | None:
    """One short sentence from the model's own coefficients, so the headline is short and nothing is invented.
    Returns (sentence, detail) or None when the full model is not loaded."""
    coefs = ld.model_coefficients()
    if not coefs or coefs[1] != "full":
        return None
    co = coefs[0].set_index("term")
    need = {"z_log_alan (sensitive)", "z_log_alan", "z_log_alan:sensitive"}
    if not need <= set(co.index):
        return None
    s_or, t_or = co.loc["z_log_alan (sensitive)", "odds_ratio"], co.loc["z_log_alan", "odds_ratio"]
    p = co.loc["z_log_alan:sensitive", "p_value"]
    if s_or < 1 and s_or < t_or and p < 0.05:
        text = (f"Where nights are brighter, light-sensitive birds are reported less: ×{s_or:.2f} per step of "
                f"light, against ×{t_or:.2f} for light-tolerant birds.")
    else:
        text = (f"Per step of night light, light-sensitive birds ×{s_or:.2f} and light-tolerant birds ×{t_or:.2f}; "
                "no clear difference between the groups.")
    return text, (f"Odds of being reported per 1 SD more night light. Difference between groups {p_txt(p)}. "
                  "Association, not cause.")


SRC = {"real": "observed"}  # a section running on backup data shows no source tag
effort_src = SRC.get(ld.status("effort_grid.parquet"))

# ---------------------------------------------------------------- header and the one rule to read by
ui.page_header("Birds & Light",
               "Are light-sensitive birds reported less where nights are brighter? Greater Manila, in 1 km cells.")
ui.alert("<b>How to read the maps:</b> grey means nobody submitted a complete birding checklist there. "
         "That is an observation gap, not zero birds. Everything here shows association, not cause.",
         kind="info", html=True)

# ---------------------------------------------------------------- the headline finding
fd = ld.findings()
f_status = ld.status("findings.md")
short = short_headline()
if fd and not fd["pending"]:
    ui.section("Headline finding", source="model" if f_status == "real" else None)
    if short:
        ui.insight(short[0], meta=short[1])
        if st.toggle("Show the full finding, with the resident and migrant split", key="bl_full"):
            ui.gloss(ui.escape(fd["headline"]))
            if fd.get("data"):
                ui.gloss(f"<b>Data:</b> {ui.escape(fd['data'])}")
    else:
        ui.insight(fd["headline"], meta=f"Data: {fd['data']}" if fd.get("data") else None)
else:
    ui.section("Headline finding")
    ui.alert("<b>The headline finding is not available yet.</b> It appears once the night-light model results load.",
             kind="pending", html=True)

# ---------------------------------------------------------------- effort summary (observed)
water = ld.water_cells()  # None when only the backup grid is available
effort_all = ld.effort_by_cell()
is_water = effort_all["cell_id"].isin(water) if water is not None else pd.Series(False, index=effort_all.index)
n_cells = int((~is_water).sum())                       # land cells
n_obs = int((~effort_all["is_gap"] & ~is_water).sum())  # observed land cells
n_obs_water = int((~effort_all["is_gap"] & is_water).sum())
n_rated = int((effort_all["n_checklists"] >= 5).sum())
sp = ld.species() if ld.available("species.parquet") else pd.DataFrame()
focus = sp[sp["focus"]] if not sp.empty else sp
tol = focus["light_tolerance"].astype(str).str.lower() if not focus.empty else pd.Series(dtype=str)
n_sens, n_tol = int((tol == "sensitive").sum()), int((tol == "tolerant").sum())
cell_word = "land cells" if water is not None else "cells (water not yet masked)"

ui.section("Where people went birding", sub=f"{FIRST_YEAR}–{LAST_YEAR}", source=effort_src)
ui.stats_row([
    ui.stat_html("Complete checklists", f"{ld.n_checklists():,}" if ld.available("checklists.parquet") else "–",
                 desc="eBird checklists that pass the Best Practices filters"),
    ui.stat_html("Cells with any checklist", f"{n_obs + n_obs_water:,}",
                 desc=(f"{n_obs:,} of {n_cells:,} land cells ({n_obs / n_cells:.0%}), plus {n_obs_water:,} mostly-water "
                       "cells such as coastal wetlands; the rest are observation gaps") if water is not None and n_cells
                 else f"of {n_cells:,} {cell_word}; the rest are observation gaps"),
    ui.stat_html("Cells with 5 or more", f"{n_rated:,}", desc="Over the whole period; only these can carry a rate"),
    ui.stat_html("Focus species", f"{n_sens + n_tol}", desc=f"{n_sens} light-sensitive, {n_tol} light-tolerant"),
])

# ---------------------------------------------------------------- the focus map, controls beside it
satellite_src = "satellite" if ld.status("grid_annual.parquet") == "real" else None
rates_ok = ld.available("cell_rates.parquet")
MODES = {"Birding effort": "effort", "Reporting rate": "rate", "Satellite covariate": "cov"}
if not rates_ok:
    MODES.pop("Reporting rate")

map_heading = st.empty()  # filled once the view is chosen, so the heading sits above its own controls
with st.container(border=True):
    mode_label = st.segmented_control("Map shows", list(MODES), default="Birding effort", key="bl_mode",
                                      help="Effort and reporting rates are observed eBird data. Satellite covariates "
                                           "exist for every cell.") or "Birding effort"
    mode = MODES[mode_label]
    group = period = gvar = None
    show_gaps = True
    if mode == "rate":
        rates = ld.cell_rates()
        periods = sorted(rates["period"].unique())
        c1, c2 = st.columns(2, gap="medium")
        group = c1.radio("Species group", ["Sensitive", "Tolerant"], horizontal=True, key="bl_group",
                         format_func=lambda g: f"Light-{g.lower()}")
        period = c2.radio("Period", periods, index=len(periods) - 1, horizontal=True, key="bl_period",
                          format_func=lambda p: p.replace("-", "–"))
    elif mode == "cov":
        c1, c2, c3 = st.columns([3, 3, 2], gap="medium")
        gvar = c1.selectbox("Covariate", GRID_VARIABLES,
                            format_func=lambda k: f"{VARIABLES[k]['label']} ({VARIABLES[k]['unit']})", key="bl_gvar")
        year = c2.select_slider("Year", options=list(range(FIRST_YEAR, LAST_YEAR + 1)), value=LAST_YEAR, key="bl_year")
        show_gaps = c3.toggle("Grey out gaps", value=False, key="bl_gaps",
                              help="Grey out cells where nobody submitted a checklist that year.")


def build_map(cells: pd.DataFrame, title: str, unit: str, cscale: str, crange: tuple[float, float],
              rated_only: bool, show_gaps: bool, log_hover: bool = False) -> go.Figure:
    """cells: cell_id, lat, lon, value, n_checklists, is_gap, low_data."""
    if rated_only:
        shown = cells[cells["value"].notna() & ~cells["is_gap"]]
        thin = cells[~cells["is_gap"] & cells["value"].isna()]
    else:
        shown = cells[~cells["is_gap"]] if show_gaps else cells
        thin = cells.iloc[0:0]
    gaps = cells[cells["is_gap"]] if show_gaps else cells.iloc[0:0]
    low = shown[shown["low_data"]] if show_gaps else shown.iloc[0:0]
    fig = go.Figure()
    if len(gaps):
        fig.add_trace(go.Scattermap(lat=gaps["lat"], lon=gaps["lon"], mode="markers",
                                    marker=dict(size=5, color=GAP_COLOR, opacity=0.35), name=GAP_LABEL,
                                    text=gaps["cell_id"], hovertemplate="Cell %{text}<br>" + GAP_LABEL + "<extra></extra>"))
    if len(thin):
        fig.add_trace(go.Scattermap(lat=thin["lat"], lon=thin["lon"], mode="markers",
                                    marker=dict(size=6, color=ui.PALETTE["muted"], opacity=0.9),
                                    name="Fewer than 5 checklists", text=thin["label"], customdata=thin[["n_checklists"]],
                                    hovertemplate="Cell %{text}<br>%{customdata[0]} checklists: too few for a rate<extra></extra>"))
    if len(low):  # outline effect: a light ring under the coloured marker
        fig.add_trace(go.Scattermap(lat=low["lat"], lon=low["lon"], mode="markers",
                                    marker=dict(size=10, color=ui.PALETTE["ink"], opacity=0.9), name=LOW_DATA_LABEL,
                                    hoverinfo="skip"))
    if len(shown):
        val_txt = "" if log_hover else unit + ": %{marker.color:.3g}<br>"
        fig.add_trace(go.Scattermap(
            lat=shown["lat"], lon=shown["lon"], mode="markers",
            marker=dict(size=7, color=shown["value"], colorscale=cscale, cmin=crange[0], cmax=crange[1], opacity=0.92,
                        colorbar=dict(title=dict(text=unit, side="right"), thickness=12)),
            name=title, text=shown["label"], customdata=shown[["n_checklists"]],
            hovertemplate="Cell %{text}<br>" + val_txt + "checklists: %{customdata[0]:,}<extra></extra>",
        ))
    fig.update_layout(map=dict(style=MAP_STYLE, center=FOCUS_CENTER, zoom=8.4), margin=dict(l=0, r=0, t=8, b=0),
                      showlegend=False)
    return ui.style_fig(fig, height=620, legend_bottom=False)


def with_geometry(values: pd.DataFrame, effort: pd.DataFrame, keep_observed_water: bool = True) -> pd.DataFrame:
    """Join values and effort to cell centres. Water cells (water_frac > 0.5) are hidden, except, when
    keep_observed_water is set, those with real checklists (coastal wetlands): their observations are kept on the
    map and flagged, because the bird model leaves them out."""
    cells = effort.merge(values, on="cell_id", how="left")
    cells = cells.merge(ld.cell_centers(cells["cell_id"]), on="cell_id")
    cells["water"] = cells["cell_id"].isin(water) if water is not None else False
    if water is not None:
        keep = ~cells["water"] | (keep_observed_water & ~cells["is_gap"])
        cells = cells[keep]
    cells["label"] = np.where(cells["water"], cells["cell_id"] + " (mostly water: excluded from the bird model)",
                              cells["cell_id"])
    return cells


def range_of(v: pd.Series) -> tuple[float, float]:
    v = v.dropna()
    return (float(np.nanpercentile(v, 2)), float(np.nanpercentile(v, 98))) if len(v) else (0.0, 1.0)


legend_items: list[tuple[str, str, str | None]] = []
if mode == "effort":
    eff = ld.effort_by_cell()
    vals = eff[["cell_id"]].assign(value=np.log10(eff["n_checklists"].where(eff["n_checklists"] > 0)))
    cells = with_geometry(vals, eff)
    fig = build_map(cells, "Birding effort", "checklists (log scale)", "Viridis", range_of(cells["value"]),
                    rated_only=False, show_gaps=True, log_hover=True)
    tick = [1, 10, 100, 1000]
    fig.update_traces(selector=dict(name="Birding effort"),
                      marker_colorbar=dict(tickvals=np.log10(tick), ticktext=[f"{t:,}" for t in tick],
                                           title=dict(text="checklists", side="right")))
    map_title, map_src = f"Checklists per cell, {FIRST_YEAR}–{LAST_YEAR}", effort_src
    legend_items.append(("#21918c", "Checklists per cell", "Colour shows how many complete checklists, log scale."))
    source_line = "Source: eBird Basic Dataset, Cornell Lab of Ornithology."
elif mode == "rate":
    sel = rates[(rates["group"] == group) & (rates["period"] == period)]
    y0, y1 = (int(x) for x in period.split("-"))
    eff = ld.effort_by_cell((y0, y1))
    cells = with_geometry(sel[["cell_id", "reporting_rate"]].rename(columns={"reporting_rate": "value"}), eff)
    fig = build_map(cells, "Reporting rate", "share reported", "Viridis", range_of(cells["value"]),
                    rated_only=True, show_gaps=True)
    map_title = f"Light-{group.lower()} reporting rate, {period.replace('-', '–')}"
    map_src = SRC.get(ld.status("cell_rates.parquet"))
    legend_items.append(("#21918c", "Reporting rate", "Share of focus-species detections on complete checklists. "
                                                       "Cells with 5 or more checklists in the period only."))
    legend_items.append((ui.PALETTE["muted"], "Fewer than 5 checklists", "Observed, but too few for a rate."))
    source_line = "Observed data only, no model. Source: eBird via Members 1 and 3."
else:
    ga = ld.grid_annual(("cell_id", "year", "water_frac", gvar)) if ld.available("grid_annual.parquet") else None
    meta = VARIABLES[gvar]
    map_title, map_src = f"{meta['label']}, {year}", satellite_src
    if ga is None:
        fig = None
    else:
        eff = ld.effort_by_cell((year, year))
        vals = ga[ga["year"] == year][["cell_id", gvar]].rename(columns={gvar: "value"})
        cells = with_geometry(vals, eff, keep_observed_water=False)
        if ld.is_backup("grid_annual.parquet"):  # the backup grid covers a small window only
            cells = cells[cells["value"].notna() | cells["is_gap"].eq(False)]
        fig = build_map(cells, meta["label"], meta["unit"], meta["colorscale"], range_of(cells["value"]),
                        rated_only=False, show_gaps=show_gaps)
    legend_items.append((ui.PALETTE["accent"], "Satellite value", f"{meta['source']}, yearly mean per cell."))
    source_line = f"Source: {meta['source']} via Google Earth Engine."

legend_items.append((GAP_COLOR, GAP_LABEL, "No complete checklist. Not the same as zero birds."))
legend_items.append(("ring", LOW_DATA_LABEL, "1 to 4 checklists over 2014–2025. Outlined, never given a rate."))

ui.section("The focus map", sub=map_title, source=map_src, container=map_heading)
c_map, c_side = st.columns([3, 1], gap="medium")
with c_map:
    if fig is None:
        ui.alert("Satellite values per cell are not available right now.", kind="pending")
    else:
        st.plotly_chart(fig, width="stretch", config=ui.MAP_CONFIG)
    st.caption(source_line)
with c_side:
    gap_note = None
    sc = ld.spatial_checks()
    if sc is not None and (sc["test"] == "gaps").any():
        r = sc[sc["test"] == "gaps"].iloc[0]
        scope = " Provisional: water cells still included." if "provisional" in str(r.get("scope", "")) else ""
        gap_note = (f"Why gaps stay blank: unobserved cells cluster in space (Moran's I = {r['moran_i']:.2f}, "
                    f"p ≤ {r['p_sim']:.3f}), so missing data is not random.{scope}")
    if water is None:
        gap_note = (gap_note + " " if gap_note else "") + "Water cells are not marked in this data."
    elif mode != "cov":
        gap_note = (gap_note + " " if gap_note else "") + (
            "Open water is hidden. Mostly-water cells with checklists, such as the Las Piñas–Parañaque wetlands, stay "
            "on the map because people birded there, but the bird model leaves them out.")
    else:
        gap_note = (gap_note + " " if gap_note else "") + "Mostly-water cells are hidden in this view."
    ui.legend("Legend", legend_items, note=gap_note)
    if not focus.empty:
        rows = []
        for g in ("Sensitive", "Tolerant"):
            top = focus[tol == g.lower()].nlargest(4, "n_detections")
            names = ", ".join(top["species"].astype(str))
            rows.append((ui.PALETTE["accent"] if g == "Sensitive" else ui.PALETTE["muted"],
                         f"Light-{g.lower()}: {names}", None))
        ui.legend("Most reported focus species", rows, note=f"Source: eBird species list, {n_sens + n_tol} focus species.")

# ---------------------------------------------------------------- model results
c_eff, c_mod = st.columns([3, 2], gap="medium")
with c_eff:
    ec_status = ld.status("effect_curve.parquet")
    ui.section("Detection and night light", source="model" if ec_status == "real" else None)
    if not ld.available("effect_curve.parquet"):
        ui.alert("The effect curve is not available right now.", kind="pending")
    else:
        ec = ld.effect_curve()
        efig = go.Figure()
        for g, sub in ec.groupby("group"):
            sub = sub.sort_values("alan")
            key = "Sensitive" if "sensitive" in str(g).lower() else "Tolerant"
            c = ui.GROUP_COLORS.get(key, ui.PALETTE["muted"])
            efig.add_scatter(x=pd.concat([sub["alan"], sub["alan"][::-1]]), y=pd.concat([sub["ci_high"], sub["ci_low"][::-1]]),
                             fill="toself", fillcolor=c, opacity=0.18, line=dict(width=0), hoverinfo="skip",
                             showlegend=False)
            efig.add_scatter(x=sub["alan"], y=sub["prob"], mode="lines", line=dict(color=c, width=2.5),
                             name=f"Light-{key.lower()} species",
                             hovertemplate="%{x:.3g} nW/cm²/sr: %{y:.0%}<extra>" + key + "</extra>")
        efig.update_layout(margin=dict(l=0, r=0, t=16, b=0), xaxis_title="Night-time light (nW/cm²/sr)",
                           yaxis_title="Detection probability",
                           # start at zero but fit the data (predictions run about 2-19%), so the lines are not flattened
                           yaxis=dict(range=[0, float(ec["ci_high"].max()) * 1.1], tickformat=".0%"))
        ui.style_fig(efig, height=400)
        st.plotly_chart(efig, width="stretch")
        st.caption("Predicted for a standard checklist (60 min, 1 km, 1 observer, 07:00). Bands: 95% confidence.")

with c_mod:
    coefs = ld.model_coefficients()
    kind = coefs[1] if coefs else None
    src = None
    if coefs:
        src = None if (ld.is_backup("model_coefficients.csv") and kind == "full") else "model"
    ui.section("Model results", sub="baseline, before satellite covariates" if kind == "baseline" else None, source=src)
    if not coefs:
        ui.alert("Model coefficients are not available right now.", kind="pending")
    else:
        co = coefs[0].copy()
        co = co[co["term"] != "Intercept"]
        co["what"] = [term_label(t, lab) for t, lab in zip(co["term"], co.get("label", [None] * len(co)))]
        key_terms = ["z_log_alan (sensitive)", "z_log_alan", "z_alan", "z_log_alan:sensitive", "z_alan:sensitive",
                     "sensitive", "year_c", "year_c:sensitive"]
        tile_names = {"z_log_alan (sensitive)": "Light-sensitive species", "z_log_alan": "Light-tolerant species",
                      "z_alan": "Light-tolerant species", "z_log_alan:sensitive": "Difference between the groups",
                      "z_alan:sensitive": "Difference between the groups"}
        tiles = []
        for t in key_terms:
            r = co[co["term"] == t]
            if len(r) and len(tiles) < 3:
                r = r.iloc[0]
                ci = f"95% CI {r['ci_low']:.2f}–{r['ci_high']:.2f}, {p_txt(r['p_value'])}"
                if t.endswith(":sensitive"):
                    desc = f"how much stronger the light effect is for sensitive species ({ci})"
                elif t in tile_names:
                    desc = f"as likely to be reported per 1 SD more night light ({ci})"
                else:
                    desc = f"as likely to be reported ({ci})"
                tiles.append(ui.stat_html(tile_names.get(t, r["what"]), f"{r['odds_ratio']:.2f}×", desc=desc,
                                          accent=t == "z_log_alan (sensitive)"))
        if tiles:
            ui.stats_row(tiles)
        co["order"] = [0 if t in key_terms else (2 if t.startswith("C(month)") else 1) for t in co["term"]]
        co = co.sort_values(["order"]).reset_index(drop=True)
        st.dataframe(pd.DataFrame({
            "Term, in plain words": co["what"],
            "Odds ratio": co["odds_ratio"].round(2),
            "95% CI": [f"{a:.2f}–{b:.2f}" for a, b in zip(co["ci_low"], co["ci_high"])],
            "p": [("< 0.001" if p < 0.001 else f"{p:.3f}") for p in co["p_value"]],
        }), hide_index=True, width="stretch", height=280)
        notes = ["Odds ratio below 1: less likely to be reported; above 1: more likely. Effort (duration, distance, "
                 "observers, time of day) is controlled for."]
        if kind == "baseline":
            notes.append("This baseline has no night-light term yet, so it cannot answer the light question.")
        if sc is not None and (sc["test"].astype(str).str.startswith("residuals")).any():
            r = sc[sc["test"].astype(str).str.startswith("residuals")].iloc[0]
            if r["p_sim"] <= 0.05 and kind == "full":
                notes.append(f"Model residuals still cluster in space (Moran's I = {r['moran_i']:.2f}); with larger "
                             "5×5-cell block clusters the difference between the groups still has p ≤ 0.001 "
                             "(findings.md).")
            elif r["p_sim"] <= 0.05:
                notes.append(f"Model residuals still cluster in space (Moran's I = {r['moran_i']:.2f}), so these "
                             "p-values may be too small.")
        rb = ld.robustness()
        if rb is not None and kind == "full" and len(rb) > 1:
            refits = rb.iloc[1:]
            held = refits[(refits["interaction_or"] < 1) & (refits["p_value"] < 0.001)]
            notes.append(f"The difference keeps its direction with p < 0.001 in {len(held)} of {len(refits)} refits: "
                         + ", ".join(refits["variant"].astype(str).str.replace("<=", "≤", regex=False)) + ".")
        st.caption(" ".join(notes))

# ---------------------------------------------------------------- limitations, from findings.md when available
caveats = (fd or {}).get("caveats") or [
    "Association, not causation.",
    "eBird detection is not abundance.",
    "Results cover Greater Manila only.",
]
ui.section("Limitations that affect these results")
st.markdown("\n".join(f"- {ui.escape(c)}" for c in caveats))
