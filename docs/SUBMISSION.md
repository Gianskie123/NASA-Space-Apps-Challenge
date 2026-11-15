# Project Submission page: copy-paste text

One section per field on the Space Apps Project Submission page (team brief, section 4). Fill the `<...>` placeholders, paste each block into its field, click **Save Progress** often, then run the pre-submission checklist at the bottom. Deadline: **Sun Nov 15, 2026, 11:59 p.m.** local time.

---

## Project Name

AviTrend PH

## High-Level Project Summary

AviTrend PH is a free, no-login web app that turns 12 years of NASA satellite data into plain answers for every province of the Philippines: what is changing, where, by how much, and whether the change is statistically significant. Users pick a variable (night-time light, vegetation, land temperature, rain or land cover), a province and a time window, watch a weather-map-style animation, and get a verdict such as "Increasing, +0.68 nW/cm²/sr per year, significant (p < 0.001)". We then go one step further than a trend tool: we combine NASA Black Marble night light with 12,953 real birdwatcher checklists to show that light-sensitive birds are reported far less often where Greater Manila has grown brighter (odds ×0.53 vs ×0.88 for light-tolerant birds per 3× more light), and we map 116 places where sensitive birds still occur but light is rising fast. That gives the Philippines' Biodiversity Management Bureau and local governments a data-backed list of where to act on light pollution before those birds disappear.

## Link to Project Demo

`<public link to the 7-slide deck (PDF/Slides on Google Drive, set to "Anyone with the link") — test in incognito>`

## Link to Final Project

`<https://<your-app>.streamlit.app>` (app) · https://github.com/Gianskie123/NASA-Space-Apps-Challenge (code)

## Detailed Project Description

**What it does**

AviTrend PH answers Challenge 2 for the whole Philippines (85 provinces, 2014–2025) and adds an ecological layer.

1. **What's changing.** Choose a variable, a province (or the Greater Manila focus area), a start and end month, and monthly or annual resolution. The app shows an animated province map with a fixed colour scale, so a colour means the same value in every month; a time series with a 12-month rolling mean and the trend line; and result cards with direction, slope per year with units, total and percentage change, p-value and the test used. A second map shows which provinces changed significantly after correcting for testing all 85 at once. Windows that are too short or have too many missing months get a warning instead of a misleading p-value.
2. **What it means for birds.** For Greater Manila on a 1 km grid, the app shows the NASA covariates, observed bird reporting rates for light-sensitive and light-tolerant species, and an effect curve from our model. Places where nobody went birding are drawn grey as "observation gaps", never as zero birds.
3. **Where to act.** An overview map of 116 places where light-sensitive birds are still reported and night light has risen at least 1.5× since 2014–2016, named by public eBird hotspot (for example the Tanza mudflats in Navotas, Tunasan Baywalk in Muntinlupa, and sites in Imus, Tanay and Silang).
4. **How we know.** Every dataset with a link, the method, the limitations, the references and our AI disclosure.

**Key findings**

- Night light rose significantly in 82 of 85 provinces (median +54%). The fastest growth is at Manila's edges: Cavite +152%, Pampanga +127%, Bulacan +125%; urban land share is rising significantly in the same provinces.
- Vegetation greened significantly in 72 provinces; rain increased significantly in 21.
- In Greater Manila, per 1 SD more night light (about 3× brighter), the odds of detecting a light-sensitive species fall to ×0.53 (95% CI 0.47–0.59), versus ×0.88 (0.82–0.95) for light-tolerant species. The difference is significant (p ≤ 0.001), survives every robustness check (no thinning, ≤ 5 km checklists, wetland cells included, without land temperature, larger spatial clusters) and is driven by resident species (×0.35 vs ×0.89).
- Honest limits: this is association, not causation; eBird measures detection, not abundance; MODIS Terra's daytime land temperature reads cooler after 2020 because its overpass time drifts, and the app warns about it.

**How it works**

- NASA satellite products are averaged per province and per 1 km cell, per month, in Google Earth Engine.
- Trends: Seasonal Mann–Kendall test (each month compared only with the same month in other years, so the monsoon cannot fake a trend) with seasonal Sen's slope; annual series use Mann–Kendall with the Hamed–Rao autocorrelation correction; Benjamini–Hochberg false-discovery-rate correction across provinces. The test runs live in the app in under a second.
- Birds: eBird checklists are rebuilt and filtered to complete checklists, so an unreported species is a true absence. Unvisited cells stay blank; Moran's I shows they are spatially clustered (I = 0.29, p ≤ 0.001), so filling them would bias results.
- Model: a binomial GLM of detection on night light × light tolerance, controlling for forest cover, land temperature, rain, month, time of day and observer effort, with standard errors clustered by grid cell and hotspot checklists thinned. Nothing predicted from the covariates is ever fed back into a test.

**Benefits and what we hope to achieve**

- Anyone, with no GIS or statistics background, can check whether their province is getting brighter, greener, wetter or more built-up, and whether that change is real or noise.
- Conservation planners get evidence that artificial light is linked to fewer sensitive birds and a short list of places to prioritise for dark-sky or lighting rules. We hope the Biodiversity Management Bureau (DENR-BMB) and local governments use it, as with our earlier AviLight project.
- The method uses only free, global data, so it can be rerun for any country with eBird coverage.

**Tools, languages and software**

Python; Google Earth Engine Python API; Streamlit; Plotly; pandas, NumPy, SciPy, PyArrow; statsmodels, libpysal and esda (PySAL); pymannkendall (cross-check); pytest; GitHub Actions (keep-alive); hosted on Streamlit Community Cloud. Basemap: CARTO Positron, © OpenStreetMap contributors.

## Use of Super Intelligence (SI)

Yes. We used AI coding and writing assistants as tools, not to come up with the idea or the analysis design. OpenAI Codex helped write and debug Google Earth Engine extraction and data-validation code and draft hand-off notes. Claude (Anthropic) helped write the web app code, interface, documentation and submission text, and with code review. The research question, data choices, statistical method, checks and all final decisions are the team's. No AI-generated images, video or audio are used. AI use is disclosed in REFERENCES.md, the README and the app's "How we know" page.

## NASA Data

- **NASA Black Marble VNP46A2** (VIIRS Lunar Gap-Filled BRDF Nighttime Lights, daily, 500 m): night-time light, the core trend variable and the bird model's main predictor. https://developers.google.com/earth-engine/datasets/catalog/NASA_VIIRS_002_VNP46A2
- **MODIS Terra MOD13A1.061** Vegetation Indices (NDVI, 16-day, 500 m). https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13A1
- **MODIS Terra MOD11A2.061** Land Surface Temperature (8-day, 1 km). https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A2
- **GPM IMERG V07** (NASA/JAXA), half-hourly precipitation summed to monthly. https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07
- **MODIS MCD12Q1.061** Land Cover Type (yearly, 500 m, `LC_Type1`). https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1

## Space Agency Partner Data & Other References

- **JAXA** (Space Agency Partner): co-producer of the GPM IMERG precipitation data above.
- JRC Global Surface Water Mapping Layers v1.4 (water mask). https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
- FAO GAUL 2025, level 2 (province boundaries). https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2025_level2
- eBird Basic Dataset, Philippines, 2014–2025. Cornell Lab of Ornithology. https://science.ebird.org/en/use-ebird-data/download-ebird-data-products
- Species light-tolerance and migratory traits: the team's earlier AviLight species masterlist.
- Methods: Hirsch, Slack & Smith (1982) Seasonal Mann–Kendall; Hamed & Rao (1998); Sen (1968); Benjamini & Hochberg (1995); Moran (1950); Strimas-Mackey et al., Best Practices for Using eBird Data.
- Software: Google Earth Engine, Streamlit, Plotly, pandas, NumPy, SciPy, PyArrow, statsmodels, libpysal, esda, pymannkendall, pytest. Basemap CARTO Positron, © OpenStreetMap contributors. Hallmark design guidelines (MIT licence).
- Full list with links: https://github.com/Gianskie123/NASA-Space-Apps-Challenge/blob/main/REFERENCES.md
- No copyrighted material is used without permission. All data used is openly licensed or used under its published terms.

---

## Pre-submission checklist (team brief, page 9)

Status as of Nov 15. **Done** = verified in the repo; **To do** = needs a person.

**Team and eligibility**

- [ ] To do: all members registered, same Local Event, none waitlisted, all on the Members tab (max 6).
- [x] Done: project responds to Challenge 2, Be An Earth System Trend Detective!
- [x] Done: no one under 18 appears in any image, video, audio or likeness (the app and deck contain no people).

**Demo**

- [x] Done: 7 slides including title: https://claude.ai/artifact/BTi4EmaTUJLHni1JGja4Mi (private; export it as PDF from Share › Export, then host the PDF publicly).
- [ ] To do: fill team name and member names on slide 1.
- [x] Done: deck is in English and shows the project, the user experience and how NASA data makes it work.
- [ ] To do: upload the PDF to Google Drive, share as "Anyone with the link", test in incognito, paste link above.

**Project page**

- [x] Done: Project Name, High-Level Summary, Detailed Description drafted above.
- [ ] To do: deploy the app, make the GitHub repo public, test both links in incognito, paste the app URL above and in `README.md`.
- [x] Done: five NASA datasets named specifically; NASA data is the trend engine.
- [ ] To do: Members 1 and 3 confirm their AI-assistance entries in `REFERENCES.md`.
- [x] Done: no copyrighted material used without permission.
- [x] Done: SI answer drafted; no AI images/video/audio; AI code and text acknowledged in `REFERENCES.md`, `README.md` and the About page.
- [x] Done: no NASA logos, flags or mission identifiers in the app or deck.
- [x] Done: all content in English.

**Submit**

- [ ] To do: tick both agreement boxes (Terms & Conditions; All Work is Original).
- [ ] To do: click "Submit for Judging" and see the confirmation banner.
- [ ] To do: any later edit saved **and** resubmitted before 11:59 p.m.
