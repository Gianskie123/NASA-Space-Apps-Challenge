"""Page 3: About the data."""

from pathlib import Path

import streamlit as st

import ui

ROOT = Path(__file__).resolve().parents[2]

ui.page_header("How we know", "Where the numbers come from, how we tested them, and what they cannot tell you.")

ui.section("In short")
ui.numbered([
    ("Satellites, not guesses", "Five free NASA satellite datasets measure night light, greenery, ground "
     "temperature and rain every month, and land cover every year, from 2014 to 2025, for every province."),
    ("A change only counts if it is steady", "We use standard trend tests that ignore the normal wet and dry seasons "
     "and only call a change real when it is very unlikely to be chance."),
    ("Real birdwatching records", "Bird results use only complete checklists from eBird, where birdwatchers report "
     "every species they saw. Places nobody visited are left blank, never counted as zero birds."),
])

ui.section("Datasets")
EE = "https://developers.google.com/earth-engine/datasets/catalog/"
DATASETS = [
    ("NASA Black Marble VNP46A2", EE + "NASA_VIIRS_002_VNP46A2", "NASA, VIIRS, NASA/VIIRS/002/VNP46A2",
     "Night-time light: band DNB_BRDF_Corrected_NTL, days with quality flag 0 or 1, monthly median (nW/cm²/sr)."),
    ("MODIS MOD13A1.061", EE + "MODIS_061_MOD13A1", "NASA, MODIS Terra, MODIS/061/MOD13A1",
     "Terra Vegetation Indices: NDVI from good-quality 16-day composites, monthly mean."),
    ("MODIS MOD11A2.061", EE + "MODIS_061_MOD11A2", "NASA, MODIS Terra, MODIS/061/MOD11A2",
     "Terra Land Surface Temperature: daytime values from good-quality 8-day composites, monthly mean (°C)."),
    ("GPM IMERG Release 07", EE + "NASA_GPM_L3_IMERG_V07", "NASA and JAXA, NASA/GPM_L3/IMERG_V07",
     "Rainfall: half-hourly estimates summed to monthly totals (mm/month)."),
    ("MODIS MCD12Q1.061", EE + "MODIS_061_MCD12Q1", "NASA, MODIS, MODIS/061/MCD12Q1",
     "Yearly land cover (LC_Type1), turned into the share of each area that is urban, forest, cropland, "
     "grass and shrub, wetland or water."),
    ("eBird Basic Dataset", "https://science.ebird.org/en/use-ebird-data/download-ebird-data-products",
     "Cornell Lab of Ornithology", "Complete birdwatcher checklists for Greater Manila, 2014–2025."),
    ("FAO GAUL 2025, level 2", EE + "FAO_GAUL_2025_level2", "FAO, FAO/GAUL/2025/level2",
     "Province boundaries (85 areas)."),
    ("JRC Global Surface Water v1.4", EE + "JRC_GSW1_4_GlobalSurfaceWater", "EC JRC, JRC/GSW1_4/GlobalSurfaceWater",
     "Marks cells that are mostly water (Manila Bay, Laguna de Bay)."),
]
st.markdown('<div class="av-legend">' + "".join(ui.dataset(*d) for d in DATASETS) + "</div>", unsafe_allow_html=True)
ui.gloss("All satellite products were processed with the Google Earth Engine Python API.")

ui.section("Data choices worth knowing")
st.markdown("""
- **Newer boundaries.** Provinces use FAO GAUL 2025, which replaced the older, retired GAUL 2015.
  Metro Manila appears as a single area, the National Capital Region.
- **Rainfall from half-hourly data.** The monthly IMERG V07 collection did not reach December 2025 when the data
  was extracted, so half-hourly IMERG V07 was summed to months instead.
- **Land cover stops at 2024.** MCD12Q1's latest map is 2024, so the 2025 rows repeat the 2024 shares.
- **Cloudy months stay missing.** A month is left blank when fewer than 30% of its pixels are usable. Across the
  Greater Manila grid that blanks about 38% of vegetation and 24% of land temperature values (under 3% at
  province level); night light and rain are nearly complete.
- **Small quality artefacts are kept, not hidden.** About 0.06% of land temperature values are below 15 °C, a
  known MODIS quality artefact, and land-cover shares sum to about 0.99 rather than exactly 1.
""")

ui.section("Method in six steps", "The technical detail behind the results.")
ui.numbered([
    ("Satellite data to monthly tables",
            "Google Earth Engine averages each NASA product per province and per 1 km cell, January 2014 to "
            "December 2025 (144 months). Months with under 30% usable pixels, mostly cloud, are left missing."),
    ("Trend test",
            "Monthly series use the Seasonal Mann–Kendall test, which compares each January only with other Januaries "
            "so the monsoon cannot fake a trend. Yearly series use Mann–Kendall with the Hamed–Rao correction. "
            "Sen's slope, the median rate of change, gives the size."),
    ("Many provinces at once",
            "When every province is tested, significance is corrected with the Benjamini–Hochberg false discovery "
            "rate, so a few provinces do not look significant by chance."),
    ("Checklists, true absences and gaps",
            "Yearly eBird files are rebuilt into complete checklists (validated against real eBird IDs for 2025, "
            "within 0.4%) and filtered by eBird best practice. A focus species missing from a complete checklist "
            "was looked for and not found: a true absence. A cell with no checklist is an observation gap and stays blank."),
    ("Bird model",
            "A logistic regression with standard errors clustered by cell tests whether night light affects "
            "light-sensitive species differently from light-tolerant ones, controlling for forest, heat, rain, "
            "season and birding effort. Busy hotspots are thinned so they do not dominate."),
    ("No circularity",
            "Significance tests and model results use real checklists only. Nothing predicted from the satellite "
            "data is ever fed back into a test."),
])

ui.section("Limitations")
st.markdown("""
- **Observation gaps.** Most cells have no birdwatcher. They are never treated as zero birds and never filled in.
- **Uneven years.** 88% of checklists are from 2020–2025, so early years carry little weight.
- **Cloud gaps.** Optical satellites cannot see through cloud, so vegetation and land temperature miss more monsoon months.
- **Land temperature drifts after 2020.** MODIS Terra's overpass time drifts earlier, so daytime land temperature reads cooler from 2021 onward; the falling trend seen in every province is likely partly an instrument artefact.
- **The light effect is concentrated in resident species.** Migratory light-sensitive and light-tolerant species respond alike.
- **Wetland hotspots sit outside the main model.** Cells that are more than half water are left out, which removes the Las Piñas–Parañaque, Tanza, Paombong and Balanga sites; a refit that keeps them gives the same result.
- **Association, not causation.** The model shows where light and bird reports go together, not that light causes it.
- **Detection, not abundance.** eBird records whether a species was reported, not how many birds live there.
- **Night birds are under-sampled.** Daytime birding misses many nocturnal species, which may be the most affected by light.
- **Greater Manila only** for the bird analysis; the Trend Explorer covers every province.
- **Future work:** an occupancy model, to separate "is the bird there" from "was it detected".
""")

ui.section("References")
refs = ROOT / "REFERENCES.md"
if refs.exists():
    # Rendered as plain Markdown (no raw HTML). The file's own title is dropped and its headings shifted down a
    # level so they sit under this section; its AI assistance section covers the disclosure.
    lines = refs.read_text(encoding="utf-8").splitlines()
    body = "\n".join("###" + ln if ln.startswith("#") else ln for ln in lines if not ln.startswith("# "))
    with st.expander("Full list of references, software and AI assistance"):
        st.markdown(body)
else:
    st.markdown("""
- Google Earth Engine Python API. Google for Developers.
- Datasets: every product listed under Datasets above, with its Earth Engine catalog ID.
- eBird Basic Dataset. Cornell Lab of Ornithology, Ithaca, New York.
- Software: Streamlit, Plotly, pandas, NumPy, SciPy and PyArrow.
""")
    ui.section("AI assistance")
    st.markdown("AI tools helped with parts of the code and text; the idea, analysis choices and checks are the team's "
                "own. OpenAI Codex and Claude were used; see REFERENCES.md.")
