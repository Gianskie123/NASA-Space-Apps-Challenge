"""Shared constants for the app: variables, units, colours, focus area."""

APP_NAME = "AviTrend PH"  # placeholder name, see TEAM_BUILD_PLAN.md

# key -> settings. "table" says which file the variable comes from.
VARIABLES = {
    "alan": {
        "label": "Night-time light (ALAN)", "unit": "nW/cm²/sr", "table": "monthly",
        "colorscale": "Cividis", "source": "NASA Black Marble VNP46A2",
    },
    "ndvi": {
        "label": "Vegetation (NDVI)", "unit": "NDVI (unitless)", "table": "monthly",
        "colorscale": "Greens", "source": "MODIS MOD13A1",
    },
    "lst_day": {
        "label": "Land surface temperature (day)", "unit": "°C", "table": "monthly",
        "colorscale": "YlOrRd", "source": "MODIS MOD11A2",
    },
    "rain_mm": {
        "label": "Rain", "unit": "mm/month", "table": "monthly",
        "colorscale": "Blues", "source": "GPM IMERG V07",
    },
    "urban_frac": {
        "label": "Land cover: % urban", "unit": "share of area", "table": "landcover",
        "colorscale": "Purples", "source": "Land cover (product TBC by Member 2)",
    },
    "forest_frac": {
        "label": "Land cover: % forest", "unit": "share of area", "table": "landcover",
        "colorscale": "Greens", "source": "Land cover (product TBC by Member 2)",
    },
}

# Grid covariates available on the Birds & Light focus map (from grid_annual).
GRID_VARIABLES = ["alan", "ndvi", "lst_day", "rain_mm"]

FOCUS_AREA_LABEL = "Greater Manila focus area"
# Provinces inside the bird focus box (14.00-15.30 N, 120.50-121.60 E).
# Until Member 2 provides a dedicated focus-area series, the app averages these.
FOCUS_PROVINCES = [
    "Metropolitan Manila", "Bulacan", "Pampanga", "Cavite", "Laguna", "Rizal", "Bataan",
]
FOCUS_CENTER = {"lat": 14.65, "lon": 121.05}

MAP_STYLE = "carto-positron"  # free basemap, no token
GAP_COLOR = "#c8c8c8"
GAP_LABEL = "No observer (observation gap)"
LOW_DATA_LABEL = "Low-data cell (< 5 checklists)"

FIRST_YEAR, LAST_YEAR = 2014, 2025
MISSING_WARN_SHARE = 0.30
