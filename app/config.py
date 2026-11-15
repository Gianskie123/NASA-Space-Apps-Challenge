"""Shared constants for the app: variables, plain labels, colours, focus area."""

APP_NAME = "AviTrend PH"  # placeholder name, see TEAM_BUILD_PLAN.md
TAGLINE = "NASA satellite data on how the Philippines is changing, and what it means for birds"
GITHUB_URL = "https://github.com/Gianskie123/NASA-Space-Apps-Challenge"

# key -> settings, in the order shown to users. "plain" is what non-specialists read; "label" + "unit" are the
# technical names shown in the scientist panels. up/down colours give each map a meaning (amber = brighter,
# green = greener, red = hotter...). "table" says which file the variable comes from.
VARIABLES = {
    "alan": {
        "plain": "Night-time light", "about": "how bright the ground looks from space at night",
        "label": "Night-time light (ALAN)", "unit": "nW/cm²/sr", "plain_unit": "brightness (satellite units)", "table": "monthly",
        "up": "#d98e04", "down": "#3d5a98", "colorscale": "Cividis",
        "source": "NASA Black Marble VNP46A2 (VIIRS)",
    },
    "ndvi": {
        "plain": "Greenery", "about": "how much living vegetation covers the ground (NDVI)",
        "label": "Vegetation (NDVI)", "unit": "NDVI (unitless)", "plain_unit": "greenness index (0 to 1)", "table": "monthly",
        "up": "#2f8a4c", "down": "#9a5b2e", "colorscale": "Greens",
        "source": "MODIS MOD13A1.061 (NASA, Terra)",
    },
    "rain_mm": {
        "plain": "Rainfall", "about": "how much rain falls each month",
        "label": "Rain", "unit": "mm/month", "plain_unit": "mm of rain per month", "table": "monthly",
        "up": "#2b6cb0", "down": "#a8761d", "colorscale": "Blues",
        "source": "GPM IMERG V07 (NASA/JAXA), half-hourly summed to monthly",
    },
    "urban_frac": {
        "plain": "Built-up land", "about": "the share of land covered by buildings and roads",
        "label": "Land cover: % urban", "unit": "share of area", "plain_unit": "% of the land", "table": "landcover",
        "up": "#7b3fa0", "down": "#2f8a4c", "colorscale": "Purples",
        "source": "MODIS MCD12Q1.061 land cover (NASA), LC_Type1",
    },
    "forest_frac": {
        "plain": "Forest cover", "about": "the share of land covered by forest",
        "label": "Land cover: % forest", "unit": "share of area", "plain_unit": "% of the land", "table": "landcover",
        "up": "#2f8a4c", "down": "#9a5b2e", "colorscale": "Greens",
        "source": "MODIS MCD12Q1.061 land cover (NASA), LC_Type1",
    },
    "lst_day": {
        "plain": "Daytime ground temperature", "about": "how hot the ground surface gets by day (not air temperature)",
        "label": "Land surface temperature (day)", "unit": "°C", "plain_unit": "ground temperature, °C", "table": "monthly",
        "up": "#c8463d", "down": "#3d7fd1", "colorscale": "YlOrRd",
        "source": "MODIS MOD11A2.061 (NASA, Terra)",
    },
}

# Grid covariates available on the bird data explorer map (from grid_annual).
GRID_VARIABLES = ["alan", "ndvi", "lst_day", "rain_mm"]

FOCUS_AREA_LABEL = "Greater Manila (bird study area)"
# Provinces inside the bird focus box (14.00-15.30 N, 120.50-121.60 E); the app averages them for the
# focus-area series. GAUL 2025 names Metro Manila "National Capital Region"; the backup file uses the old name.
FOCUS_PROVINCES = [
    "National Capital Region", "Metropolitan Manila", "Bulacan", "Pampanga", "Cavite", "Laguna", "Rizal", "Bataan",
]
METRO_MANILA = ("National Capital Region", "Metropolitan Manila")
FOCUS_CENTER = {"lat": 14.65, "lon": 121.05}
PH_CENTER, PH_ZOOM = {"lat": 12.0, "lon": 122.4}, 4.6

MAP_STYLE = "carto-positron"  # free basemap, no token
GAP_COLOR = "#b9bcc2"
GAP_LABEL = "Nobody birdwatched here (not the same as no birds)"
LOW_DATA_LABEL = "Fewer than 5 birdwatching checklists"

FIRST_YEAR, LAST_YEAR = 2014, 2025
MISSING_WARN_SHARE = 0.30
