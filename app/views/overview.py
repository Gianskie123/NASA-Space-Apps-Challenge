"""Overview: the whole story in 30 seconds, for policymakers and anyone new to the app.

Every number comes from the data files (province_trends, effect_curve, priority_areas, checklists).
"""

from __future__ import annotations

import streamlit as st

import charts
import load_data as ld
import plain
import ui
from config import VARIABLES

counts = charts.province_counts("alan")
ec = ld.effect_curve() if ld.available("effect_curve.parquet") else None
head = plain.bird_headline(ec) if ec is not None else None
pa = ld.priority_areas()
n_priority = int(pa["priority"].sum()) if pa is not None else None
n_ck = ld.n_checklists() if ld.available("checklists.parquet") else None

brighter = counts is not None and counts["up"] > counts["n"] / 2
title = ("The Philippines is getting brighter at night. Around Manila, birds that need darkness are rarely "
         "recorded where nights are brightest."
         if brighter and head and head["clear"] else "How the Philippines is changing, seen from space, and what it means for birds.")
ui.page_header(
    title,
    "Free NASA satellite data shows where night-time light, greenery, rain and land use are changing in every "
    "province. Birdwatcher records show which birds that change affects. Built to help DENR-BMB decide where "
    "to act.", hero=True)

# ---------------------------------------------------------------- three findings
items = []
if counts:
    metro = counts["metro"]
    metro_txt = f" Metro Manila is {plain.change_phrase('alan', metro, '2014')}." if metro else ""
    items.append(("Night light is spreading", f"{counts['up']} of {counts['n']}",
                  f"provinces got brighter at night between 2014 and 2025, a real trend and not chance.{metro_txt} "
                  "Source: NASA Black Marble.", VARIABLES["alan"]["up"]))
if head:
    if head["clear"]:
        items.append(("Around Manila: birds that need darkness", f"{plain.times_text(head['ratio'])}× less likely",
                      "to be recorded in the brightest places than in the darkest. Birds that live here all year are "
                      "hit hardest.", ui.GROUP_COLORS["Sensitive"]))
    else:
        items.append(("Birds and night light", "No clear difference",
                      "between birds that need darkness and birds that tolerate light.", ui.GROUP_COLORS["Sensitive"]))
if n_priority is not None:
    items.append(("Where to act first", f"{n_priority} places",
                  "around Greater Manila still have light-sensitive birds, and their nights are now at least 1.5× "
                  "as bright as in 2014–16.", "#b34700"))
if items:
    ui.cards(items)

# ---------------------------------------------------------------- two maps
c1, c2 = st.columns(2, gap="medium")
with c1:
    ui.section("Where nights got brighter", "Each province, 2014 to 2025. Darker orange: a bigger rise.")
    fig = charts.change_map("alan", height=480, zoom=4.3)
    if fig is None:
        ui.alert("Province results are not available right now.", kind="pending")
    else:
        st.plotly_chart(fig, width="stretch", config=ui.MAP_CONFIG)
        charts.change_legend("alan")
with c2:
    ui.section("Where birds that need darkness meet fast-rising light",
               "Places in Greater Manila where they were recorded. Orange: nights now at least 1.5× brighter.")
    if pa is None:
        ui.alert("The places map is not available right now.", kind="pending")
    else:
        st.plotly_chart(charts.priority_map(pa, height=480), width="stretch", config=ui.MAP_CONFIG)
        charts.priority_legend()

# ---------------------------------------------------------------- the other NASA measurements
ui.section("Other changes NASA satellites show", "How many of the 85 provinces changed between 2014 and 2025.")
tiles = []
for key in ["ndvi", "rain_mm", "urban_frac", "forest_frac", "lst_day"]:
    c = charts.province_counts(key)
    if not c:
        continue
    up_w, down_w = plain.short_words(key)
    big, small = (up_w, down_w) if c["up"] >= c["down"] else (down_w, up_w)
    n_big, n_small = max(c["up"], c["down"]), min(c["up"], c["down"])
    desc = f"{n_small} {small.lower()}, {c['n'] - c['up'] - c['down']} with no clear change."
    if key == "lst_day":
        desc += " Read with care: the satellite's timing changed after 2020."
    tiles.append(ui.stat_html(VARIABLES[key]["plain"], f"{n_big} {big.lower()}", desc=desc))
ui.stats_row(tiles)
st.page_link("views/trend_explorer.py", label="Explore any measurement, province and span of years",
             icon=":material/arrow_forward:")

# ---------------------------------------------------------------- what to do
ui.section("What this means for DENR-BMB", "Practical steps that follow from the evidence.")
ui.numbered([
    ("Act first where light is rising fastest",
     "The orange places still have light-sensitive birds, but their nights are now at least 1.5× as bright as in "
     "2014–16. Acting now costs far less than bringing birds back later."),
    ("Set lighting guidelines near bird habitats",
     "Shielded, downward-facing, warm-coloured and dimmable lights around protected areas, wetlands and roosts, "
     "such as the Las Piñas–Parañaque Critical Habitat and Ecotourism Area (a Ramsar wetland)."),
    ("Watch the growing edges of the city",
     "Many fast-brightening bird places are new housing developments at the edge of Greater Manila. Lighting "
     "can be considered early, when these areas are planned."),
    ("Check progress every year with free NASA data",
     "The same satellite data and method can be rerun each year to see whether lighting measures are working."),
])
ui.gloss("These results show where night light and missing birds go together. Brighter places are also more "
         "built-up, so light is a strong warning sign rather than proof that it is the only cause."
         + (f" Based on {n_ck:,} complete birdwatcher checklists (eBird) and five NASA satellite datasets."
            if n_ck else ""))

# ---------------------------------------------------------------- go deeper
ui.section("Go deeper")
l1, l2, l3 = st.columns(3, gap="medium")
l1.page_link("views/trend_explorer.py", label="What's changing in your province", icon=":material/insights:", use_container_width=True)
l2.page_link("views/birds_and_light.py", label="What it means for birds", icon=":material/flutter_dash:", use_container_width=True)
l3.page_link("views/about.py", label="How we know: data and methods", icon=":material/menu_book:", use_container_width=True)
