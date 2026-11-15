"""Page 3: About the data."""

from pathlib import Path

import streamlit as st

import ui

ROOT = Path(__file__).resolve().parents[2]

ui.page_header("About the data", "Where the numbers come from, how we tested them, and what they can't tell you.")

ui.section("Datasets")
EE = "https://developers.google.com/earth-engine/datasets/catalog/"
DATASETS = [
    ("Black Marble VNP46A2", EE + "NASA_VIIRS_002_VNP46A2", "NASA, VIIRS",
     "Monthly median night-time light (nW/cm²/sr) from good-quality days."),
    ("MODIS MOD13A1 NDVI", EE + "MODIS_061_MOD13A1", "NASA, MODIS Terra", "Monthly mean vegetation index."),
    ("MODIS MOD11A2 LST", EE + "MODIS_061_MOD11A2", "NASA, MODIS Terra",
     "Monthly mean daytime land surface temperature (°C)."),
    ("GPM IMERG Monthly V07", EE + "NASA_GPM_L3_IMERG_MONTHLY_V07", "NASA and JAXA, GPM", "Monthly rainfall (mm/month)."),
    ("Land cover", None, "product to be confirmed by Member 2",
     "Yearly share of urban, forest, cropland and other classes."),
    ("eBird Basic Dataset", "https://science.ebird.org/en/use-ebird-data/download-ebird-data-products",
     "Cornell Lab of Ornithology", "Complete birdwatcher checklists for Greater Manila, 2014–2025."),
    ("FAO GAUL 2015 level 2", EE + "FAO_GAUL_2015_level2", "FAO", "Province boundaries."),
    ("JRC Global Surface Water", EE + "JRC_GSW1_4_GlobalSurfaceWater", "EC JRC",
     "Masks water cells (Manila Bay, Laguna de Bay)."),
]
st.markdown('<div class="av-legend">' + "".join(ui.dataset(*d) for d in DATASETS) + "</div>", unsafe_allow_html=True)

ui.section("Method in six steps")
st.markdown("".join([
    ui.step(1, "Satellite data to monthly tables",
            "Google Earth Engine averages each NASA product per province and per 1 km cell, January 2014 to "
            "December 2025 (144 months). Months with under 30% usable pixels, mostly cloud, are left missing."),
    ui.step(2, "Trend test",
            "Monthly series use the Seasonal Mann–Kendall test, which compares each January only with other Januaries "
            "so the monsoon cannot fake a trend. Yearly series use Mann–Kendall with the Hamed–Rao correction. "
            "Sen's slope, the median rate of change, gives the size."),
    ui.step(3, "Many provinces at once",
            "When every province is tested, significance is corrected with the Benjamini–Hochberg false discovery "
            "rate, so a few provinces do not look significant by chance."),
    ui.step(4, "Checklists, true absences and gaps",
            "Yearly eBird files are rebuilt into complete checklists (validated against real eBird IDs for 2025, "
            "within 0.4%) and filtered by eBird best practice. A focus species missing from a complete checklist "
            "was looked for and not found: a true absence. A cell with no checklist is an observation gap and stays blank."),
    ui.step(5, "Bird model",
            "A logistic regression with standard errors clustered by cell tests whether night light affects "
            "light-sensitive species differently from light-tolerant ones, controlling for forest, heat, rain, "
            "season and birding effort. Busy hotspots are thinned so they do not dominate."),
    ui.step(6, "No circularity",
            "Significance tests and model results use real checklists only. Nothing predicted from the satellite "
            "data is ever fed back into a test."),
]), unsafe_allow_html=True)

ui.section("Limitations")
st.markdown("""
- **Observation gaps.** Most cells have no birdwatcher. They are never treated as zero birds and never filled in.
- **Uneven years.** 88% of checklists are from 2020–2025, so early years carry little weight.
- **Cloud gaps.** Optical satellites cannot see through cloud, so vegetation and land temperature miss more monsoon months.
- **Association, not causation.** The model shows where light and bird reports go together, not that light causes it.
- **Detection, not abundance.** eBird records whether a species was reported, not how many birds live there.
- **Night birds are under-sampled.** Daytime birding misses many nocturnal species, which may be the most affected by light.
- **Greater Manila only** for the bird analysis; the Trend Explorer covers every province.
- **Future work:** an occupancy model, to separate "is the bird there" from "was it detected".
""")

ui.section("References")
refs = ROOT / "REFERENCES.md"
if refs.exists():
    st.markdown(refs.read_text())
else:
    ui.alert("REFERENCES.md is not in the repo yet. Every dataset, library and AI tool the team uses will be listed here.",
             kind="pending")

ui.section("AI assistance")
st.markdown("AI tools were used to help write parts of the code and text. Every use is listed under **AI assistance** in "
            "REFERENCES.md. The idea, the analysis choices and the checks are the team's own.")
