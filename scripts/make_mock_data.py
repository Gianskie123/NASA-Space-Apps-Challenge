"""Write fake versions of every processed file the app reads (Member 4).

Mock files go to data/mock/, never data/processed/, so they can't be mistaken
for (or overwrite) the real hand-offs from Members 1-3. The app reads
data/processed/<file> when it exists and falls back to data/mock/<file>.

Column names follow docs/TEAM_BUILD_PLAN.md exactly. Where the plan does not
fix the columns (Member 3's model outputs), the assumed columns are listed in
ASSUMED_CONTRACT below: confirm them with Member 3 before the real-data swap.

Run:  python scripts/make_mock_data.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mock"
RNG = np.random.default_rng(42)

YEARS = range(2014, 2026)
MONTHS = [(y, m) for y in YEARS for m in range(1, 13)]  # 144 months

# Assumed columns for files whose layout the build plan leaves open.
ASSUMED_CONTRACT = {
    "province_trends.parquet": "variable, adm2_code, province, n_months, tau, p_value, q_value, "
    "significant, slope_per_year, change_pct, direction",
    "model_coefficients.csv": "term, label, odds_ratio, ci_low, ci_high, p_value",
    "effect_curve.parquet": "group, alan, prob, ci_low, ci_high",
    "cell_rates.parquet": "cell_id, lat, lon, period, group, sensitive, n_checklists, reporting_rate (real schema, Member 3)",
    "grid_annual.parquet": "cell_id, year, alan, ndvi, lst_day, rain_mm, water_frac",
    "findings.md": "'## Headline' section (Member 3's format); '## Caveats' bullets are listed on the Birds page",
}

# ---------------------------------------------------------------- provinces
# (province, adm1, adm2_code, lat0, lat1, lon0, lon1, alan_base, alan_growth/yr, ndvi_base)
PROVINCES = [
    ("Metropolitan Manila", "National Capital Region", 1001, 14.40, 14.78, 120.93, 121.13, 40.0, 0.010, 0.30),
    ("Bulacan", "Region III", 1002, 14.78, 15.20, 120.75, 121.30, 8.0, 0.060, 0.55),
    ("Pampanga", "Region III", 1003, 14.85, 15.30, 120.45, 120.75, 7.0, 0.050, 0.55),
    ("Cavite", "Region IV-A", 1004, 14.10, 14.40, 120.60, 121.05, 9.0, 0.065, 0.55),
    ("Laguna", "Region IV-A", 1005, 14.05, 14.40, 121.05, 121.60, 6.0, 0.055, 0.60),
    ("Rizal", "Region IV-A", 1006, 14.40, 14.78, 121.13, 121.45, 7.0, 0.060, 0.62),
    ("Cebu", "Region VII", 1007, 9.40, 11.30, 123.30, 124.05, 5.0, 0.030, 0.55),
    ("Davao del Sur", "Region XI", 1008, 6.40, 7.40, 125.00, 125.60, 4.0, 0.030, 0.65),
    ("Palawan", "MIMAROPA", 1009, 8.40, 11.40, 117.20, 119.80, 0.5, 0.000, 0.72),
]

# Greater Manila bird focus area and the shared cell formula.
LAT0, LON0, STEP = 14.00, 120.50, 0.009


def cell_id(row: int, col: int) -> str:
    return f"{row:03d}_{col:03d}"


def seasonal(month: np.ndarray, peak: int, amp: float) -> np.ndarray:
    return amp * np.cos(2 * np.pi * (month - peak) / 12)


def rain_cycle(month: np.ndarray, mindanao: bool) -> np.ndarray:
    # Southwest monsoon: peak Jun-Sep, low Jan-Apr. Mindanao is flatter.
    if mindanao:
        return 180 + seasonal(month, 7, 40)
    wet = np.isin(month, [6, 7, 8, 9])
    shoulder = np.isin(month, [5, 10, 11])
    return np.where(wet, 420, np.where(shoulder, 180, 30)).astype(float)


def province_monthly() -> pd.DataFrame:
    rows = []
    ym = pd.DataFrame(MONTHS, columns=["year", "month"])
    t = (ym["year"] - 2014) + (ym["month"] - 1) / 12
    m = ym["month"].to_numpy()
    covid = ((ym["year"] == 2020) & ym["month"].isin([4, 5])).to_numpy()
    for prov, adm1, code, *_box, alan0, growth, ndvi0 in PROVINCES:
        n = len(ym)
        alan = alan0 * np.exp(growth * t) * (1 + RNG.normal(0, 0.04, n))
        alan = np.where(covid, alan * 0.85, alan).clip(0)
        ndvi = (ndvi0 - 0.004 * growth * 100 * t / 10 + seasonal(m, 9, 0.05) + RNG.normal(0, 0.02, n)).clip(-0.2, 1)
        lst = 31 + (2 if alan0 > 20 else 0) + seasonal(m, 4.5, 3.0) + 0.05 * t + RNG.normal(0, 0.8, n)
        rain = (rain_cycle(m, code == 1008) * RNG.lognormal(0, 0.3, n)).clip(0, 1500)
        monsoon = np.isin(m, [6, 7, 8, 9])
        alan_valid = RNG.uniform(0.6, 1.0, n)
        ndvi_valid = np.where(monsoon, RNG.uniform(0.1, 0.8, n), RNG.uniform(0.5, 1.0, n))
        lst_valid = np.where(monsoon, RNG.uniform(0.05, 0.7, n), RNG.uniform(0.4, 1.0, n))
        df = ym.copy()
        df.insert(0, "adm2_code", code)
        df.insert(0, "province", prov)
        df.insert(0, "adm1", adm1)
        df["alan"] = np.where(alan_valid < 0.3, np.nan, alan)
        df["ndvi"] = np.where(ndvi_valid < 0.3, np.nan, ndvi)
        df["lst_day"] = np.where(lst_valid < 0.3, np.nan, lst)
        df["rain_mm"] = rain
        df["alan_valid"], df["ndvi_valid"], df["lst_valid"] = alan_valid, ndvi_valid, lst_valid
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


LC_COLS = ["urban_frac", "forest_frac", "cropland_frac", "grass_shrub_frac", "wetland_frac", "water_lc_frac"]


def landcover_shares(urban: float, forest: float, n_years: int, urban_growth: float) -> pd.DataFrame:
    out = []
    for i, year in enumerate(YEARS):
        u = min(0.97, urban + urban_growth * i)
        f = max(0.0, forest - urban_growth * i * 0.4)
        rest = max(0.0, 1 - u - f)
        shares = np.array([u, f, rest * 0.5, rest * 0.3, rest * 0.12, rest * 0.08])
        shares = shares / shares.sum()
        out.append([year, *shares, min(year, 2024)])  # pretend product ends in 2024
    return pd.DataFrame(out, columns=["year", *LC_COLS, "lc_year_used"])


def province_landcover() -> pd.DataFrame:
    rows = []
    for _prov, _adm1, code, *_box, alan0, growth, ndvi0 in PROVINCES:
        urban = min(0.9, alan0 / 45)
        df = landcover_shares(urban, ndvi0 * 0.6, len(YEARS), growth * 0.08)
        df.insert(0, "adm2_code", code)
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def box_polygon(lat0: float, lat1: float, lon0: float, lon1: float) -> list:
    r = lambda v: round(v, 4)  # noqa: E731
    return [[[r(lon0), r(lat0)], [r(lon1), r(lat0)], [r(lon1), r(lat1)], [r(lon0), r(lat1)], [r(lon0), r(lat0)]]]


def provinces_geojson() -> dict:
    feats = []
    for prov, adm1, code, lat0, lat1, lon0, lon1, *_ in PROVINCES:
        feats.append({
            "type": "Feature",
            "properties": {"province": prov, "adm1": adm1, "adm2_code": code},
            "geometry": {"type": "Polygon", "coordinates": box_polygon(lat0, lat1, lon0, lon1)},
        })
    return {"type": "FeatureCollection", "features": feats}


# ---------------------------------------------------------------- focus grid
# A small window of the real 145 x 123 grid around Metro Manila keeps mock files tiny.
GRID_ROWS = range(50, 101)  # 14.45 - 14.91 N
GRID_COLS = range(40, 91)   # 120.86 - 121.32 E
HOTSPOTS = [  # (lat, lon, weight): La Mesa / UP Diliman, Rizal Park, Las Pinas-Paranaque wetlands
    (14.655, 121.065, 1.0),
    (14.583, 120.979, 0.6),
    (14.485, 120.985, 0.7),
]


def grid_cells() -> pd.DataFrame:
    recs = []
    for r in GRID_ROWS:
        for c in GRID_COLS:
            lat = LAT0 + (r + 0.5) * STEP
            lon = LON0 + (c + 0.5) * STEP
            # Mock Manila Bay: west of ~120.95 E between 14.45 and 14.80 N.
            water = 0.9 if (lon < 120.95 + (lat - 14.45) * 0.1 and lat < 14.80) else max(0.0, RNG.normal(0.02, 0.02))
            d_core = math.hypot(lat - 14.60, lon - 121.00)
            recs.append((cell_id(r, c), r, c, lat, lon, round(min(1.0, water), 3), d_core))
    return pd.DataFrame(recs, columns=["cell_id", "row", "col", "lat", "lon", "water_frac", "d_core"])


def grid_geojson(cells: pd.DataFrame) -> dict:
    feats = []
    for rec in cells.itertuples():
        lat0, lon0 = LAT0 + rec.row * STEP, LON0 + rec.col * STEP
        feats.append({
            "type": "Feature",
            "properties": {"cell_id": rec.cell_id, "water_frac": rec.water_frac},
            "geometry": {"type": "Polygon", "coordinates": box_polygon(lat0, lat0 + STEP, lon0, lon0 + STEP)},
        })
    return {"type": "FeatureCollection", "features": feats}


def grid_annual(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in YEARS:
        t = year - 2014
        bright = 55 * np.exp(-cells["d_core"] / 0.12)
        growth = 0.07 * np.clip(cells["d_core"] / 0.25, 0, 1)  # edges brighten faster
        alan = (bright * np.exp(growth * t) + 2 * np.exp(0.06 * t) + RNG.normal(0, 0.5, len(cells))).clip(0)
        ndvi = (0.25 + 0.45 * np.clip(cells["d_core"] / 0.3, 0, 1) - 0.004 * t + RNG.normal(0, 0.03, len(cells))).clip(-0.2, 1)
        lst = 30 + 5 * np.exp(-cells["d_core"] / 0.15) + 0.05 * t + RNG.normal(0, 0.5, len(cells))
        rain = 2300 + RNG.normal(0, 150, len(cells))
        df = pd.DataFrame({
            "cell_id": cells["cell_id"], "year": year, "alan": alan, "ndvi": ndvi,
            "lst_day": lst, "rain_mm": rain, "water_frac": cells["water_frac"],
        })
        rows.append(df)
    out = pd.concat(rows, ignore_index=True)
    water = out["water_frac"] > 0.5
    out.loc[water, ["alan", "ndvi", "lst_day"]] = np.nan
    return out


def grid_landcover(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in YEARS:
        t = year - 2014
        u = np.clip(0.95 * np.exp(-cells["d_core"] / 0.15) + 0.01 * t * np.clip(cells["d_core"] / 0.25, 0, 1), 0, 0.97)
        f = np.clip(0.5 * np.clip(cells["d_core"] / 0.3, 0, 1) - 0.004 * t, 0, 1 - u)
        rest = 1 - u - f
        df = pd.DataFrame({
            "cell_id": cells["cell_id"], "year": year, "urban_frac": u, "forest_frac": f,
            "cropland_frac": rest * 0.5, "grass_shrub_frac": rest * 0.3, "wetland_frac": rest * 0.12,
            "water_lc_frac": rest * 0.08, "lc_year_used": min(year, 2024),
        })
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- eBird (Member 1)
SPECIES = [  # (common, scientific, light_tolerance, migratory_status, base detection prob)
    ("Eurasian Tree Sparrow", "Passer montanus", "Tolerant", "Resident", 0.80),
    ("Yellow-vented Bulbul", "Pycnonotus goiavier", "Tolerant", "Resident", 0.70),
    ("Zebra Dove", "Geopelia striata", "Tolerant", "Resident", 0.60),
    ("Pied Fantail", "Rhipidura nigritorquis", "Tolerant", "Resident", 0.40),
    ("Collared Kingfisher", "Todiramphus chloris", "Sensitive", "Resident", 0.35),
    ("Philippine Coucal", "Centropus viridis", "Sensitive", "Resident", 0.20),
    ("Black-crowned Night Heron", "Nycticorax nycticorax", "Sensitive", "Resident", 0.25),
    ("Brown Shrike", "Lanius cristatus", "Sensitive", "Migrant", 0.30),
]
N_CHECKLISTS = 3000


def ebird(cells: pd.DataFrame, annual: pd.DataFrame):
    land = cells[cells["water_frac"] <= 0.5].reset_index(drop=True)
    w = np.zeros(len(land))
    for lat, lon, wt in HOTSPOTS:
        d = np.hypot(land["lat"] - lat, land["lon"] - lon)
        w += wt * np.exp(-d / 0.01)
    w += 0.0005  # a few scattered checklists elsewhere
    w /= w.sum()
    idx = RNG.choice(len(land), size=N_CHECKLISTS, p=w)
    years = RNG.choice(list(YEARS), size=N_CHECKLISTS, p=np.linspace(0.4, 1.6, 12) / np.linspace(0.4, 1.6, 12).sum())
    months = RNG.integers(1, 13, N_CHECKLISTS)
    days = RNG.integers(1, 29, N_CHECKLISTS)
    dates = pd.to_datetime(pd.DataFrame({"year": years, "month": months, "day": days}))
    protocol = RNG.choice(["Stationary", "Traveling"], N_CHECKLISTS, p=[0.4, 0.6])
    distance = np.where(protocol == "Stationary", 0.0, RNG.uniform(0.1, 5.0, N_CHECKLISTS)).round(2)
    chk = pd.DataFrame({
        "checklist_id": [f"S{100000000 + i}" for i in range(N_CHECKLISTS)],
        "date": dates,
        "year": years,
        "month": months,
        "week": dates.dt.isocalendar().week.astype(int).to_numpy(),
        "hour_started": RNG.uniform(5.5, 18, N_CHECKLISTS).round(2),
        "protocol": protocol,
        "duration_min": RNG.integers(5, 301, N_CHECKLISTS),
        "distance_km": distance,
        "n_observers": RNG.integers(1, 6, N_CHECKLISTS),
        "lat": land.loc[idx, "lat"].to_numpy() + RNG.uniform(-0.004, 0.004, N_CHECKLISTS),
        "lon": land.loc[idx, "lon"].to_numpy() + RNG.uniform(-0.004, 0.004, N_CHECKLISTS),
        "cell_id": land.loc[idx, "cell_id"].to_numpy(),
        "locality": "Mock locality",
    })

    alan = annual.set_index(["cell_id", "year"])["alan"]
    z = np.log1p(alan.reindex(list(zip(chk["cell_id"], chk["year"]))).to_numpy())
    z = (z - np.nanmean(z)) / np.nanstd(z)
    det_rows = []
    for name, _sci, tol, _mig, p0 in SPECIES:
        beta = -0.6 if tol == "Sensitive" else 0.1
        logit = np.log(p0 / (1 - p0)) + beta * np.nan_to_num(z) + 0.3 * np.log(chk["duration_min"] / 60)
        detected = (RNG.uniform(size=N_CHECKLISTS) < 1 / (1 + np.exp(-logit))).astype(int)
        count = np.where(detected == 1, RNG.integers(1, 20, N_CHECKLISTS), np.nan)
        det_rows.append(pd.DataFrame({"checklist_id": chk["checklist_id"], "species": name, "detected": detected, "count": count}))
    det = pd.concat(det_rows, ignore_index=True)

    n_det = det.groupby("species")["detected"].sum()
    species = pd.DataFrame([
        {"species": n, "scientific_name": s, "n_detections": int(n_det[n]), "reporting_rate": n_det[n] / N_CHECKLISTS,
         "light_tolerance": t, "migratory_status": mg, "focus": True}
        for n, s, t, mg, _ in SPECIES
    ])

    # Effort grid: every cell x year x month, including empty ones.
    hours = chk.assign(h=chk["duration_min"] / 60).groupby(["cell_id", "year", "month"]).agg(
        n_checklists=("checklist_id", "size"), total_hours=("h", "sum"))
    full = pd.MultiIndex.from_product([cells["cell_id"], list(YEARS), range(1, 13)], names=["cell_id", "year", "month"])
    eg = hours.reindex(full, fill_value=0).reset_index()
    eg["n_checklists"] = eg["n_checklists"].astype(int)
    eg["is_gap"] = eg["n_checklists"] == 0
    totals = eg.groupby("cell_id")["n_checklists"].transform("sum")
    eg["low_data"] = (totals >= 1) & (totals < 5)  # Member 1's rule: 1-4 checklists over the period
    rc = eg["cell_id"].str.split("_", expand=True).astype(int)
    eg.insert(0, "cell_col", rc[1]); eg.insert(0, "cell_row", rc[0])

    filter_log = pd.DataFrame({
        "step": ["raw", "in_focus_box", "complete_only", "protocol", "duration", "distance", "observers", "date", "group_collapse"],
        "checklists_remaining": [9800, 7600, 6100, 5600, 5200, 4700, 4650, 4600, N_CHECKLISTS],
    })
    return chk, det, species, eg, filter_log


# ---------------------------------------------------------------- Member 3 outputs
def province_trends(pm: pd.DataFrame, pl: pd.DataFrame) -> pd.DataFrame:
    """Fake trend table (Member 3 computes the real one with trends.py + FDR)."""
    recs = []
    for _prov, _adm1, code, *_box, alan0, growth, _ndvi0 in PROVINCES:
        prov = _prov
        for var, slope, pct in [
            ("alan", alan0 * growth, growth * 1200),
            ("ndvi", -0.003 * growth * 10, -growth * 50),
            ("lst_day", 0.05, 1.8),
            ("rain_mm", RNG.normal(0, 2), RNG.normal(0, 3)),
            ("urban_frac", growth * 0.08, growth * 100),
            ("forest_frac", -growth * 0.03, -growth * 60),
        ]:
            p = float(np.clip(0.0005 + (0 if abs(pct) > 5 else RNG.uniform(0.05, 0.9)), 0, 1))
            q = min(1.0, p * 3)
            recs.append({
                "variable": var, "adm2_code": code, "province": prov, "n_months": 144,
                "tau": float(np.sign(slope) * min(0.9, abs(pct) / 50)), "p_value": p, "q_value": q,
                "significant": q < 0.05, "slope_per_year": float(slope), "change_pct": float(pct),
                "direction": ("increasing" if slope > 0 else "decreasing") if q < 0.05 else "no significant trend",
            })
    return pd.DataFrame(recs)


def model_outputs(chk: pd.DataFrame, det: pd.DataFrame, species: pd.DataFrame):
    coefs = pd.DataFrame([
        ("z_alan:sensitive", "Extra night-light effect for sensitive species (interaction)", 0.68, 0.55, 0.84, 0.0004),
        ("z_alan (sensitive)", "Per 1 SD more night light, sensitive species", 0.72, 0.61, 0.85, 0.0002),
        ("z_alan (tolerant)", "Per 1 SD more night light, tolerant species", 1.06, 0.95, 1.18, 0.29),
        ("z_ndvi", "Per 1 SD more vegetation", 1.12, 1.01, 1.24, 0.03),
        ("z_lst", "Per 1 SD hotter land surface", 0.97, 0.88, 1.07, 0.55),
        ("z_rain", "Per 1 SD more rain", 0.95, 0.89, 1.02, 0.16),
        ("log_duration", "Per log-minute longer checklist", 1.45, 1.36, 1.55, 1e-6),
        ("migrant", "Migrant vs resident species", 0.81, 0.66, 0.99, 0.04),
    ], columns=["term", "label", "odds_ratio", "ci_low", "ci_high", "p_value"])

    alan = np.geomspace(0.5, 60, 40)
    z = (np.log1p(alan) - np.log1p(alan).mean()) / np.log1p(alan).std()
    curves = []
    for group, b0, b in [("Sensitive", -0.9, -0.33), ("Tolerant", 0.6, 0.06)]:
        lin = b0 + b * z
        prob = 1 / (1 + np.exp(-lin))
        se = 0.12 + 0.03 * np.abs(z)
        curves.append(pd.DataFrame({
            "group": group, "alan": alan, "prob": prob,
            "ci_low": 1 / (1 + np.exp(-(lin - 1.96 * se))), "ci_high": 1 / (1 + np.exp(-(lin + 1.96 * se))),
        }))
    effect = pd.concat(curves, ignore_index=True)

    # Observed reporting rates per cell x group x period (>= 5 checklists only).
    d = det.merge(species[["species", "light_tolerance"]], on="species").merge(chk[["checklist_id", "cell_id", "year"]], on="checklist_id")
    # Same layout as Member 3's real file: balanced periods, "Light-..." group names, share of detections.
    d = d[d["year"] >= 2018].copy()
    d["group"] = "Light-" + d["light_tolerance"].str.lower()
    d["sensitive"] = (d["light_tolerance"] == "Sensitive").astype(int)
    d["period"] = np.where(d["year"] <= 2021, "2018-2021", "2022-2025")
    rates = d.groupby(["cell_id", "period", "group", "sensitive"]).agg(
        n_checklists=("checklist_id", "nunique"), reporting_rate=("detected", "mean")).reset_index()
    rates = rates[rates["n_checklists"] >= 5].copy()
    rc = rates["cell_id"].str.split("_", expand=True).astype(int)
    rates.insert(1, "lat", (LAT0 + (rc[0] + 0.5) * STEP).round(4)); rates.insert(2, "lon", (LON0 + (rc[1] + 0.5) * STEP).round(4))
    return coefs, effect, rates


FINDINGS_MD = """# Findings (backup sample)

Data: sample values standing in until the results file loads.

## Headline

The night-light finding appears here once the results file loads.

## Caveats

- These are sample values, not results.
- Association, not causation.
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pm = province_monthly()
    pl = province_landcover()
    cells = grid_cells()
    ga = grid_annual(cells)
    gl = grid_landcover(cells)
    chk, det, species, eg, flog = ebird(cells, ga)
    pt = province_trends(pm, pl)
    coefs, effect, rates = model_outputs(chk, det, species)

    pm.to_parquet(OUT / "province_monthly.parquet", index=False)
    pl.to_parquet(OUT / "province_landcover.parquet", index=False)
    ga.to_parquet(OUT / "grid_annual.parquet", index=False)
    gl.to_parquet(OUT / "grid_landcover.parquet", index=False)
    chk.to_parquet(OUT / "checklists.parquet", index=False)
    det.to_parquet(OUT / "detections.parquet", index=False)
    species.to_parquet(OUT / "species.parquet", index=False)
    eg.to_parquet(OUT / "effort_grid.parquet", index=False)
    flog.to_csv(OUT / "filter_log.csv", index=False)
    pt.to_parquet(OUT / "province_trends.parquet", index=False)
    coefs.to_csv(OUT / "model_coefficients.csv", index=False)
    effect.to_parquet(OUT / "effect_curve.parquet", index=False)
    rates.to_parquet(OUT / "cell_rates.parquet", index=False)
    (OUT / "provinces.geojson").write_text(json.dumps(provinces_geojson(), separators=(",", ":")))
    (OUT / "grid.geojson").write_text(json.dumps(grid_geojson(cells), separators=(",", ":")))
    (OUT / "findings.md").write_text(FINDINGS_MD)

    print(f"Wrote mock data to {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:28s} {f.stat().st_size / 1024:8.1f} KB")
    print("\nAssumed columns to confirm with Member 3 / Member 2:")
    for k, v in ASSUMED_CONTRACT.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
