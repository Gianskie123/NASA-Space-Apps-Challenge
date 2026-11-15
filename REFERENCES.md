# References

Every dataset, library, method and tool used in AviTrend PH.

## NASA and other Earth observation data

All satellite products were processed with the Google Earth Engine Python API.

- **NASA Black Marble VNP46A2**: VIIRS Lunar Gap-Filled BRDF Nighttime Lights Daily L3 Global 500m. Google Earth Engine Data Catalog, `NASA/VIIRS/002/VNP46A2`. https://developers.google.com/earth-engine/datasets/catalog/NASA_VIIRS_002_VNP46A2
- **MOD13A1.061** Terra Vegetation Indices 16-Day Global 500m. Google Earth Engine Data Catalog, `MODIS/061/MOD13A1`. https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13A1
- **MOD11A2.061** Terra Land Surface Temperature and Emissivity 8-Day Global 1km. Google Earth Engine Data Catalog, `MODIS/061/MOD11A2`. https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A2
- **GPM IMERG Release 07** (NASA and JAXA), half-hourly, summed to monthly. Google Earth Engine Data Catalog, `NASA/GPM_L3/IMERG_V07`. https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07
- **MCD12Q1.061** MODIS Land Cover Type Yearly Global 500m (`LC_Type1`). Google Earth Engine Data Catalog, `MODIS/061/MCD12Q1`. https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1
- **JRC Global Surface Water Mapping Layers, v1.4**. Google Earth Engine Data Catalog, `JRC/GSW1_4/GlobalSurfaceWater`. https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
- **FAO GAUL 2025**: Global Administrative Unit Layers, second-level administrative units. Google Earth Engine Data Catalog, `FAO/GAUL/2025/level2`. https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2025_level2
- Google Earth Engine Python API. Google for Developers. https://developers.google.com/earth-engine/guides/python_install

**Data substitutions:** GAUL 2025 replaced the deprecated GAUL 2015; half-hourly IMERG V07 replaced the monthly collection, which did not cover December 2025 at extraction time; MCD12Q1's latest map is 2024, so the 2025 rows repeat the 2024 shares (`lc_year_used = 2024`).

## Bird data

- **eBird Basic Dataset**, Philippines, 2014–2025. Cornell Lab of Ornithology, Ithaca, New York. https://science.ebird.org/en/use-ebird-data/download-ebird-data-products
- **Species traits** (light tolerance, migratory status): species masterlist from the team's earlier AviLight project.

## Methods

- Hirsch, R. M., Slack, J. R. & Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research*, 18(1), 107–121. (Seasonal Mann–Kendall test.)
- Hamed, K. H. & Rao, A. R. (1998). A modified Mann–Kendall trend test for autocorrelated data. *Journal of Hydrology*, 204, 182–196.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63, 1379–1389.
- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B*, 57, 289–300.
- Moran, P. A. P. (1950). Notes on continuous stochastic phenomena. *Biometrika*, 37, 17–23.
- Strimas-Mackey, M. et al. Best Practices for Using eBird Data. Cornell Lab of Ornithology. https://ebird.github.io/ebird-best-practices/

## Software

Web app (versions in `requirements.txt`):

- Streamlit. https://streamlit.io
- Plotly (Python). https://plotly.com/python/
- pandas. https://pandas.pydata.org
- NumPy. https://numpy.org
- SciPy. https://scipy.org
- PyArrow (Apache Arrow). https://arrow.apache.org

Analysis notebooks and tests:

- statsmodels. https://www.statsmodels.org
- libpysal and esda (PySAL). https://pysal.org
- pymannkendall (used to cross-check `src/trends.py`). https://github.com/mmhs013/pyMannKendall
- pytest. https://pytest.org

Maps and design:

- Basemap: CARTO Positron, map data © OpenStreetMap contributors. https://carto.com/attributions
- Hallmark design guidelines (MIT licence), used as design guidance for the web app's interface. https://github.com/Nutlope/hallmark

## AI assistance

AI tools helped with parts of the code and text. The idea, the analysis choices, the checks and the final decisions are the team's own.

- **OpenAI Codex** (Member 2): Earth Engine Python code, export debugging, pandas merge and validation code, and drafting the hand-off notes.
- **Claude, Anthropic** (Member 4): the web app's code, interface design, text and security review.
- Members 1 and 3: add or confirm your entries here.
