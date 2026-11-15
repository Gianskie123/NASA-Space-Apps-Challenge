# Member 2 Handoff - Earth Engine Covariates

## Status

All Member 2 core data products are complete and ready for Members 3 and 4.

## Deliverables

Place these files in `data/processed/`:

- `province_monthly.parquet` - monthly province-level ALAN, NDVI, daytime LST, and rainfall (2014-2025)
- `grid_monthly.parquet` - monthly Greater Manila 1 km grid covariates (2014-2025)
- `grid_annual.parquet` - annual Greater Manila grid summaries for the app
- `province_landcover.parquet` - yearly province land-cover shares
- `grid_landcover.parquet` - yearly Greater Manila grid land-cover shares
- `provinces.geojson` - simplified province boundaries for the Trend Explorer
- `grid.geojson` - Greater Manila grid boundaries with water flags

## Coverage and keys

- Province geography: 85 GAUL 2025 level-2 features x 144 months = 12,240 rows.
- Greater Manila grid: 17,835 cells x 144 months = 2,568,240 rows.
- Annual grid: 17,835 cells x 12 years = 214,020 rows.
- Shared grid ID check: the UP Diliman cell is `072_062`.
- Water-heavy grid cells: 4,556. These remain in the tables and are flagged with `is_water` / `water_frac`; exclude cells where `water_frac > 0.5` from bird analysis.

## Dataset and processing decisions

- Province boundaries use `FAO/GAUL/2025/level2`, replacing deprecated GAUL 2015. Fields are `GAUL1_NAME`, `GAUL2_NAME`, and `GAUL2_CODE`.
- ALAN: `NASA/VIIRS/002/VNP46A2`, `DNB_BRDF_Corrected_NTL`; days with `Mandatory_Quality_Flag <= 1`; monthly median.
- NDVI: `MODIS/061/MOD13A1`, `NDVI`; `SummaryQA <= 1`; scaled by `0.0001`; monthly mean.
- Daytime LST: `MODIS/061/MOD11A2`, `LST_Day_1km`; `QC_Day & 3 <= 1`; converted with `raw * 0.02 - 273.15`; monthly mean in degrees C.
- Rainfall: `NASA/GPM_L3/IMERG_V07` half-hourly data aggregated to monthly `mm/month`. This was used instead of the monthly collection to retain coverage through December 2025.
- Land cover: `MODIS/061/MCD12Q1`, `LC_Type1`; exported as yearly class shares rather than averaged categorical codes. The 2025 analysis rows use the 2024 source map and record `lc_year_used = 2024`.
- Land-cover groups are `urban_frac`, `forest_frac`, `cropland_frac`, `grass_shrub_frac`, `wetland_frac`, and `water_lc_frac`.

## Missing-data rule

For each monthly satellite variable, values are set to missing when the corresponding `*_valid` share is below 0.3. Missing values are not filled.

Grid missingness after this rule:

- ALAN: 0.92%
- NDVI: 37.97%
- Daytime LST: 24.10%
- Rainfall: 0.00%

Province missingness after this rule:

- ALAN: 0.08%
- NDVI: 2.61%
- Daytime LST: 0.29%
- Rainfall: 0.00%

## Quality notes

- Rainfall seasonality is sensible: the wettest average months are July, August, September, and October.
- Land-cell covariate ranges are broadly plausible. A total of 1,112 LST rows (0.058% of land cell-months) are below 15 C, including a small number of negative values. These are retained as residual MODIS QA=1 artifacts under the agreed quality rule; they were not silently removed.
- Land-cover share sums average 0.988 across land cells. Lower sums occur in a small number of coastal, rare, or ungrouped land-cover classes; shares were not forced to sum to one.
- `provinces.geojson` is 0.54 MB. `grid.geojson` is 4.68 MB.

## For Member 3

- Join `grid_monthly.parquet` to checklists on `cell_id`, `year`, and `month`.
- Drop bird-model rows where `water_frac > 0.5` or a required covariate is missing.
- Join `grid_landcover.parquet` on `cell_id` and `year`.
- Use `forest_frac` as the habitat term; assess collinearity before including `urban_frac` because it is likely correlated with ALAN.

## For Member 4

- Use `province_monthly.parquet` and `provinces.geojson` for the Trend Explorer.
- Use `grid_annual.parquet`, `grid.geojson`, and water flags for the Birds & Light map.
- Keep observation gaps separate from water cells and from zero bird reporting rates.

## References reminder

Add all data products above, the GAUL 2025 substitution, the IMERG substitution, and AI assistance to `REFERENCES.md` and the app's About page.
