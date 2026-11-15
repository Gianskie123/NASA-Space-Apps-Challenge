"""Single place where the app reads data. Every page goes through here.

Each file is read from data/processed/<name> (the team's real data). If that file is missing or cannot be read,
the app falls back to data/mock/<name>, a backup sample from scripts/make_mock_data.py, so a page still works.
The sidebar shows a green dot when a data group is fully real and a yellow dot when any backup file is in use.

AVITREND_DATA=mock forces the backup files everywhere (for tests).
File names are fixed constants below; nothing here takes a path from user input.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MOCK = ROOT / "data" / "mock"

# Data groups shown in the sidebar status (core files only).
GROUPS = {
    "Bird checklists": ["checklists.parquet", "species.parquet", "effort_grid.parquet"],
    "NASA satellite data": ["province_monthly.parquet", "province_landcover.parquet", "grid_annual.parquet",
                            "provinces.geojson"],
    "Trends and bird model": ["province_trends.parquet", "model_coefficients.csv", "effect_curve.parquet",
                              "cell_rates.parquet", "findings.md"],
}
_FAILED: set[str] = set()  # real files that exist but could not be read; their backup is used instead


def _force_mock() -> bool:
    return os.environ.get("AVITREND_DATA") == "mock"


def status(name: str) -> str:
    """'real' (data/processed), 'backup' (data/mock) or 'missing' for one file."""
    if not _force_mock() and (PROCESSED / name).exists() and name not in _FAILED:
        return "real"
    return "backup" if (MOCK / name).exists() else "missing"


def resolve(name: str) -> Path | None:
    s = status(name)
    return PROCESSED / name if s == "real" else (MOCK / name if s == "backup" else None)


def is_backup(name: str) -> bool:
    return status(name) == "backup"


def available(name: str) -> bool:
    return resolve(name) is not None


def group_status(group: str) -> str:
    """'real' when every core file of the group is real, otherwise 'backup'."""
    return "real" if all(status(f) == "real" for f in GROUPS[group]) else "backup"


def _read(name: str, reader: Callable[[Path], object]):
    """Read the real file; if it is missing or unreadable, read the backup instead."""
    p = resolve(name)
    if p is None:
        raise FileNotFoundError(f"{name} is not available.")  # no local path in the message
    try:
        return reader(p)
    except Exception:
        if p.parent == PROCESSED and (MOCK / name).exists():
            log.exception("Could not read %s; using the backup file", name)
            _FAILED.add(name)
            return reader(MOCK / name)
        raise


def _parquet(name: str, columns: list[str] | None = None) -> pd.DataFrame:
    return _read(name, lambda p: pd.read_parquet(p, columns=columns))


# ---- satellite data -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def province_monthly(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    return _parquet("province_monthly.parquet", list(columns) if columns else None)


@st.cache_data(show_spinner=False)
def province_landcover() -> pd.DataFrame:
    return _parquet("province_landcover.parquet")


@st.cache_data(show_spinner=False)
def grid_annual(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    return _parquet("grid_annual.parquet", list(columns) if columns else None)


def _polygons_only(geom: dict) -> dict | None:
    """Plotly choropleths draw Polygon and MultiPolygon only. GAUL 2025 exports some provinces as
    GeometryCollections that mix polygons with stray boundary lines; keep the polygons, drop the lines."""
    t = geom.get("type")
    if t in ("Polygon", "MultiPolygon"):
        return geom
    if t == "GeometryCollection":
        rings = []
        for g in geom.get("geometries", []):
            if g.get("type") == "Polygon":
                rings.append(g["coordinates"])
            elif g.get("type") == "MultiPolygon":
                rings.extend(g["coordinates"])
        return {"type": "MultiPolygon", "coordinates": rings} if rings else None
    return None


@st.cache_data(show_spinner=False)
def provinces_geojson() -> dict:
    """Province boundaries, normalised so every feature is a Polygon or MultiPolygon (display only;
    the hand-off file itself is not changed)."""
    p = resolve("provinces.geojson")
    if p is None:
        raise FileNotFoundError("provinces.geojson is not available yet.")
    gj = _read("provinces.geojson", lambda q: json.loads(q.read_text(encoding="utf-8")))
    feats = []
    for f in gj.get("features", []):
        g = _polygons_only(f.get("geometry") or {})
        if g is not None:
            feats.append({**f, "geometry": g})
    return {"type": "FeatureCollection", "features": feats}


@st.cache_data(show_spinner=False)
def province_lookup() -> pd.DataFrame:
    """province, adm1, adm2_code from the boundaries file."""
    feats = provinces_geojson()["features"]
    return pd.DataFrame([f["properties"] for f in feats])[["province", "adm1", "adm2_code"]]


@st.cache_data(show_spinner=False)
def water_cells() -> frozenset[str] | None:
    """Cells that are mostly water (water_frac > 0.5), or None when only the backup grid is available."""
    if status("grid_annual.parquet") != "real":
        return None
    g = _parquet("grid_annual.parquet", ["cell_id", "water_frac"]).drop_duplicates("cell_id")
    return frozenset(g.loc[g["water_frac"] > 0.5, "cell_id"])


# ---- bird checklists -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _effort() -> pd.DataFrame:
    eg = _parquet("effort_grid.parquet", ["cell_id", "year", "n_checklists", "low_data"])
    eg["cell_id"] = eg["cell_id"].astype("category")
    return eg


@st.cache_data(show_spinner=False)
def effort_by_cell(years: tuple[int, int] | None = None) -> pd.DataFrame:
    """Checklists per cell over an inclusive year range (or the whole period), every cell of the grid.

    is_gap = no complete checklist in that range (an observation gap, never a zero).
    low_data = the whole-period flag from Member 1 (1-4 checklists over 2014-2025).
    """
    eg = _effort()
    if years is not None:
        eg = eg[(eg["year"] >= years[0]) & (eg["year"] <= years[1])]
    out = eg.groupby("cell_id", observed=False).agg(n_checklists=("n_checklists", "sum"),
                                                    low_data=("low_data", "max")).reset_index()
    out["cell_id"] = out["cell_id"].astype(str)
    out["is_gap"] = out["n_checklists"] == 0
    return out


@st.cache_data(show_spinner=False)
def species() -> pd.DataFrame:
    return _parquet("species.parquet")


@st.cache_data(show_spinner=False)
def n_checklists() -> int:
    return len(_parquet("checklists.parquet", ["checklist_id"]))


# ---- trends and bird model -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def province_trends() -> pd.DataFrame:
    return _parquet("province_trends.parquet")


@st.cache_data(show_spinner=False)
def effect_curve() -> pd.DataFrame:
    return _parquet("effect_curve.parquet")


@st.cache_data(show_spinner=False)
def cell_rates() -> pd.DataFrame:
    """Observed reporting rates per cell x group x period. Group names normalised to 'Sensitive'/'Tolerant'."""
    df = _parquet("cell_rates.parquet").copy()
    g = df["group"].astype(str).str.lower()
    df["group"] = g.map(lambda x: "Sensitive" if "sensitive" in x else ("Tolerant" if "tolerant" in x else x))
    df["period"] = df["period"].astype(str)
    return df


@st.cache_data(show_spinner=False)
def model_coefficients() -> tuple[pd.DataFrame, str] | None:
    """(table, kind) with columns term, odds_ratio, ci_low, ci_high, p_value.

    kind is 'full' (the light model, model_coefficients.csv) or 'baseline' (before satellite covariates).
    """
    for name, kind in (("model_coefficients.csv", "full"), ("model_coefficients_baseline.csv", "baseline")):
        p = resolve(name)
        if p is None:
            continue
        df = _read(name, pd.read_csv).rename(columns={"or_ci_low": "ci_low", "or_ci_high": "ci_high"})
        needed = {"term", "odds_ratio", "ci_low", "ci_high", "p_value"}
        if needed <= set(df.columns):
            return df, kind
    return None


@st.cache_data(show_spinner=False)
def robustness() -> pd.DataFrame | None:
    return _read("robustness.csv", pd.read_csv) if available("robustness.csv") else None


@st.cache_data(show_spinner=False)
def spatial_checks() -> pd.DataFrame | None:
    return _read("spatial_checks.csv", pd.read_csv) if available("spatial_checks.csv") else None


@st.cache_data(show_spinner=False)
def findings() -> dict | None:
    """Parsed findings.md: data line, headline (or pending note), caveats. Plain text only."""
    p = resolve("findings.md")
    if p is None:
        return None
    text = _read("findings.md", lambda q: q.read_text(encoding="utf-8"))
    sections: dict[str, list[str]] = {"_top": []}
    current = "_top"
    for line in text.splitlines():
        h = re.match(r"^#{2,3}\s+(.*)$", line)
        if h:
            current = h.group(1).strip().lower()
            sections[current] = []
        elif not line.startswith("# "):
            sections[current].append(line)

    def para(lines: list[str]) -> str:
        return " ".join(x.strip() for x in lines if x.strip() and not x.strip().startswith("-")).strip()

    def bullets(lines: list[str]) -> list[str]:
        return [x.strip()[1:].strip() for x in lines if x.strip().startswith("-")]

    head = para(sections.get("headline", []))
    # Old mock format: a single "Headline: ..." line.
    if not head:
        for line in text.splitlines():
            if line.lower().startswith("headline:"):
                head = line.split(":", 1)[1].strip()
    pending = (not head) or head.strip("_* ").lower().startswith("pending")
    return {
        "data": para(sections["_top"]).replace("Data:", "").strip() or None,
        "headline": head.strip("_* ") or None,
        "pending": pending,
        "caveats": bullets(sections.get("caveats", [])),
    }


# ---- grid cell geometry (shared formula, no file needed) -----------------
def cell_centers(cell_ids: pd.Series) -> pd.DataFrame:
    rc = cell_ids.astype(str).str.split("_", expand=True).astype(int)
    return pd.DataFrame({
        "cell_id": cell_ids.astype(str).to_numpy(),
        "lat": 14.00 + (rc[0].to_numpy() + 0.5) * 0.009,
        "lon": 120.50 + (rc[1].to_numpy() + 0.5) * 0.009,
    })
