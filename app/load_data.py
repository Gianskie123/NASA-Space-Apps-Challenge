"""Single place where the app reads data. Every page goes through here.

Each file resolves to one of three states:

* "real"    data/processed/<name>, a team hand-off.
* "mock"    data/mock/<name> from scripts/make_mock_data.py, used only while the owning member has
            delivered nothing real yet (so the app runs end to end before hand-off).
* "pending" the owning member has delivered real files but not this one yet. No mock fallback: a mock
            model result next to real checklists would read as a finding.

AVITREND_DATA=mock forces mock files everywhere (for demos and tests).
File names are fixed constants below; nothing here takes a path from user input.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MOCK = ROOT / "data" / "mock"

# Which member owns which file (TEAM_BUILD_PLAN.md).
OWNERS = {
    "Member 1": ["checklists.parquet", "detections.parquet", "species.parquet", "effort_grid.parquet", "filter_log.csv"],
    "Member 2": ["province_monthly.parquet", "province_landcover.parquet", "grid_annual.parquet",
                 "grid_landcover.parquet", "provinces.geojson", "grid.geojson"],
    "Member 3": ["province_trends.parquet", "model_coefficients.csv", "model_coefficients_baseline.csv",
                 "effect_curve.parquet", "cell_rates.parquet", "findings.md", "spatial_checks.csv"],
}
OWNER_OF = {f: m for m, files in OWNERS.items() for f in files}


def _force_mock() -> bool:
    return os.environ.get("AVITREND_DATA") == "mock"


def member_live(member: str) -> bool:
    """True once a member has delivered at least one real file."""
    return not _force_mock() and any((PROCESSED / f).exists() for f in OWNERS[member])


def status(name: str) -> str:
    """'real', 'mock', 'pending' or 'missing' for one file."""
    if not _force_mock() and (PROCESSED / name).exists():
        return "real"
    owner = OWNER_OF.get(name)
    if owner and member_live(owner):
        return "pending"
    return "mock" if (MOCK / name).exists() else "missing"


def resolve(name: str) -> Path | None:
    st_ = status(name)
    if st_ == "real":
        return PROCESSED / name
    if st_ == "mock":
        return MOCK / name
    return None


def is_mock(name: str) -> bool:
    return status(name) == "mock"


def available(name: str) -> bool:
    return resolve(name) is not None


def member_status(member: str) -> str:
    """Summary for the sidebar: 'real', 'partial', 'mock' or 'missing'."""
    states = {status(f) for f in OWNERS[member] if f not in ("grid.geojson", "model_coefficients.csv")}
    if states == {"real"}:
        return "real"
    if "real" in states:
        return "partial"
    return "mock" if "mock" in states else "missing"


def _parquet(name: str, columns: list[str] | None = None) -> pd.DataFrame:
    p = resolve(name)
    if p is None:
        raise FileNotFoundError(f"{name} is not available yet.")  # no local path in the message
    return pd.read_parquet(p, columns=columns)


# ---- Member 2 -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def province_monthly(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    return _parquet("province_monthly.parquet", list(columns) if columns else None)


@st.cache_data(show_spinner=False)
def province_landcover() -> pd.DataFrame:
    return _parquet("province_landcover.parquet")


@st.cache_data(show_spinner=False)
def grid_annual(columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    return _parquet("grid_annual.parquet", list(columns) if columns else None)


@st.cache_data(show_spinner=False)
def provinces_geojson() -> dict:
    p = resolve("provinces.geojson")
    if p is None:
        raise FileNotFoundError("provinces.geojson is not available yet.")
    return json.loads(p.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def province_lookup() -> pd.DataFrame:
    """province, adm1, adm2_code from the boundaries file."""
    feats = provinces_geojson()["features"]
    return pd.DataFrame([f["properties"] for f in feats])[["province", "adm1", "adm2_code"]]


@st.cache_data(show_spinner=False)
def water_cells() -> frozenset[str] | None:
    """Cells that are mostly water (water_frac > 0.5), or None while Member 2's real grid is pending."""
    if status("grid_annual.parquet") != "real":
        return None
    g = _parquet("grid_annual.parquet", ["cell_id", "water_frac"]).drop_duplicates("cell_id")
    return frozenset(g.loc[g["water_frac"] > 0.5, "cell_id"])


# ---- Member 1 -------------------------------------------------------------
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


# ---- Member 3 -------------------------------------------------------------
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
        df = pd.read_csv(p).rename(columns={"or_ci_low": "ci_low", "or_ci_high": "ci_high"})
        needed = {"term", "odds_ratio", "ci_low", "ci_high", "p_value"}
        if needed <= set(df.columns):
            return df, kind
    return None


@st.cache_data(show_spinner=False)
def spatial_checks() -> pd.DataFrame | None:
    p = resolve("spatial_checks.csv")
    return pd.read_csv(p) if p is not None else None


@st.cache_data(show_spinner=False)
def findings() -> dict | None:
    """Parsed findings.md: data line, headline (or pending note), caveats. Plain text only."""
    p = resolve("findings.md")
    if p is None:
        return None
    text = p.read_text(encoding="utf-8")
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
