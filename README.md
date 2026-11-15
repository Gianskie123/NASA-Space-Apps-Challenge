# AviTrend PH

**NASA Space Apps Challenge 2026 · Challenge 2: Be An Earth System Trend Detective!**

AviTrend PH is a public web app that answers the challenge question for the Philippines: **what is changing, where, by how much, and is the change statistically significant?** It then asks what other trend tools don't: **does that change matter for birds?**

NASA satellites show where night-time light, vegetation, land temperature, rain and land cover are changing across all 85 provinces from 2014 to 2025. Real birdwatcher checklists then show which bird species respond, starting with Greater Manila, where city light is spreading outward into Cavite, Bulacan, Pampanga, Rizal and Laguna.

- **Live app:** `<APP URL — add after deploying on Streamlit Community Cloud>`
- **Demo (7 slides):** `<DEMO LINK>`
- **Submission text:** [`docs/SUBMISSION.md`](docs/SUBMISSION.md)
- **All data, software and AI use:** [`REFERENCES.md`](REFERENCES.md)

## What we found

| | Result (2014–2025, monthly, Seasonal Mann–Kendall + Sen's slope, FDR-corrected across provinces) |
| --- | --- |
| Night light (NASA Black Marble) | Significantly brighter in **82 of 85 provinces**; median **+54%**. Fastest growth at Manila's edges: Cavite **+152%**, Pampanga **+127%**, Bulacan **+125%**. |
| Vegetation (MODIS NDVI) | Significant greening in 72 provinces, browning in 2. |
| Urban land (MODIS land cover) | Urban share rising significantly in 25 provinces, led by Cavite and Bulacan. |
| Rain (GPM IMERG) | Significant increase in 21 provinces; no significant trend elsewhere. |
| Land temperature (MODIS Terra) | Reads "decreasing" everywhere after 2020. We treat this as an instrument artifact (Terra's overpass drifts earlier) and say so in the app. |
| Birds (eBird, Greater Manila) | Per 1 SD more night light (about 3× brighter), the odds of detecting a **light-sensitive** species fall to **×0.53** (95% CI 0.47–0.59) versus **×0.88** (0.82–0.95) for light-tolerant species; difference p ≤ 0.001, and it holds with 5×5-cell block clusters. The effect is driven by resident species. |
| Where to act | **116 places** in Greater Manila where light-sensitive birds are still reported and night light has risen at least 1.5× since 2014–2016. |

Association, not causation. Full results and caveats: [`data/processed/findings.md`](data/processed/findings.md).

## The app

| Page | What it does |
| --- | --- |
| **Overview** | The story in one screen and the "where to act" map. |
| **What's changing** | Pick a variable, province and window. A PAGASA-style animated monthly map (fixed colour scale), a time series with the Sen's slope line, and a plain-language verdict: direction, slope per year with units, total % change, p-value. A map of which provinces changed significantly. |
| **What it means for birds** | Greater Manila 1 km grid: covariates, observed reporting rates, and observation gaps shown in grey (never as zero birds). Effect curve and model table. |
| **How we know** | Datasets with links, method, limitations, references and AI disclosure. |

## Data

NASA data is the trend engine; eBird is the effect layer.

| Variable | Dataset | Resolution |
| --- | --- | --- |
| Night-time light | NASA Black Marble VNP46A2 (VIIRS) | 500 m, daily → monthly |
| Vegetation | MODIS Terra MOD13A1 NDVI | 500 m, 16-day → monthly |
| Land surface temperature | MODIS Terra MOD11A2 (day) | 1 km, 8-day → monthly |
| Rain | GPM IMERG V07 (NASA/JAXA) | half-hourly → monthly |
| Land cover | MODIS MCD12Q1 `LC_Type1` | 500 m, yearly |
| Water mask | JRC Global Surface Water v1.4 | 30 m |
| Boundaries | FAO GAUL 2025 level 2 | 85 units |
| Birds | eBird Basic Dataset, Philippines (Cornell Lab) | checklists |

Satellite data was processed in Google Earth Engine (`notebooks/*_Extraction_PH.ipynb`).

## Method in brief

1. **Trends:** Seasonal Mann–Kendall test (Hamed–Rao correction for autocorrelation on annual series), Sen's slope, Benjamini–Hochberg FDR across provinces. `src/trends.py`, run live in the app (under 1 s per call).
2. **Birds:** complete eBird checklists only, so a missing species is a true absence. Places with no checklist are observation gaps and are never filled (Moran's I shows gaps are spatially clustered, I = 0.29, p ≤ 0.001).
3. **Model:** binomial GLM of detection on night light × light tolerance, controlling for forest, land temperature, rain and observer effort, with standard errors clustered by cell; hotspots thinned. `notebooks/03_member3_bird_model.ipynb`.
4. **No circularity:** nothing predicted from covariates ever enters a significance test.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
pytest            # trend module, plain-language text, priority areas, app pages
```

Processed data is in `data/processed/` (`grid_monthly.parquet` is only needed to rerun the bird model). `scripts/make_mock_data.py` writes mock files if you want to run without the real data.

## Repo layout

```
app/                Streamlit app (entry: app/streamlit_app.py, pages in app/views/)
src/                trends.py, province_trends.py, plain.py, priority.py
notebooks/          Earth Engine extraction, eBird ingestion, bird model
data/processed/     app-ready tables, findings.md, figures
tests/              pytest suite
scripts/            mock data, keep-alive
docs/               team plan, hand-offs, submission text
```

## Team

`<Team name>`: `<Member 1>` (eBird data), `<Member 2>` (Earth Engine covariates), `<Member 3>` (statistics and modelling), `<Member 4>` (web app).

## AI assistance

AI tools (OpenAI Codex, Claude by Anthropic) helped with parts of the code and text. The idea, analysis choices, checks and final decisions are the team's own. Details in [`REFERENCES.md`](REFERENCES.md#ai-assistance).
