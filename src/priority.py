"""Where to act: places where light-sensitive birds are still reported and night-time light has risen.

Descriptive only. It overlays observed eBird reporting rates (cell_rates) with the change in NASA Black Marble
night light between 2014-2016 and 2023-2025 (grid_annual). Nothing here is a significance test, and nothing
here is fed back into one.

Run from the project root:  python src/priority.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

EARLY, LATE = (2014, 2016), (2023, 2025)
OFFSET = 0.5          # nW/cm²/sr added before the ratio, so near-dark cells do not show huge ratios
MIN_RATIO = 1.5       # "priority" = night light at least 1.5x its 2014-2016 level
PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


def clean_locality(name) -> str:
    """Readable place name from an eBird locality: drop coordinates in brackets, 'PH--' prefixes and ', PH'."""
    if not isinstance(name, str):
        return ""
    if "Ã" in name:  # UTF-8 text that was read as Latin-1 somewhere upstream ("BaÃ±os" -> "Baños")
        try:
            name = name.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    s = re.sub(r"\s*\([^)]*\d[^)]*\)", "", name)
    s = re.sub(r"^ph--", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+PH-(\w[\w ]*)", r", \1", s)
    s = s.replace("--", ", ")
    s = re.sub(r",\s*PH$", "", s.strip())
    s = re.sub(r"\s*,\s*", ", ", re.sub(r"\s+", " ", s))
    return s.strip(" ,")


def build_priority(grid_annual: pd.DataFrame, cell_rates: pd.DataFrame, checklists: pd.DataFrame,
                   min_ratio: float = MIN_RATIO) -> pd.DataFrame:
    """One row per cell where a light-sensitive species was reported (cells with >= 5 checklists in a period).

    Columns: cell_id, lat, lon, locality, light_early, light_late, ratio, sensitive_rate, n_checklists, priority.
    Sorted by ratio, largest rise first; cells without light data have ratio NaN and are never priority.
    """
    sens = cell_rates[cell_rates["group"].astype(str).str.lower().str.contains("sensitive")]
    present = sens.groupby("cell_id").agg(lat=("lat", "first"), lon=("lon", "first"),
                                          sensitive_rate=("reporting_rate", "max"),
                                          n_checklists=("n_checklists", "sum"))
    present = present[present["sensitive_rate"] > 0]

    ga = grid_annual[["cell_id", "year", "alan"]]
    early = ga[ga["year"].between(*EARLY)].groupby("cell_id")["alan"].mean().rename("light_early")
    late = ga[ga["year"].between(*LATE)].groupby("cell_id")["alan"].mean().rename("light_late")
    out = present.join(early).join(late)
    out["ratio"] = (out["light_late"] + OFFSET) / (out["light_early"] + OFFSET)

    # Names: public eBird hotspots only (locality_type "H"). Personal locations can be private homes, so they
    # are never shown; a cell with no hotspot gets no name.
    ck = checklists.dropna(subset=["locality"])
    if "locality_type" in ck.columns:
        ck = ck[ck["locality_type"] == "H"]
    if "locality" in ck.columns and len(ck):
        loc = ck.groupby("cell_id")["locality"].agg(lambda v: v.value_counts().index[0])
        out = out.join(loc.map(clean_locality).rename("locality"))
        out["locality"] = out["locality"].astype(object).where(out["locality"].notna(), None)
    else:
        out["locality"] = None
    out["priority"] = (out["ratio"] >= min_ratio).fillna(False).astype(bool)
    out = out.reset_index().sort_values("ratio", ascending=False, na_position="last").reset_index(drop=True)
    return out[["cell_id", "lat", "lon", "locality", "light_early", "light_late", "ratio", "sensitive_rate",
                "n_checklists", "priority"]]


def main() -> pd.DataFrame:
    ga = pd.read_parquet(PROC / "grid_annual.parquet", columns=["cell_id", "year", "alan"])
    rates = pd.read_parquet(PROC / "cell_rates.parquet")
    ck = pd.read_parquet(PROC / "checklists.parquet", columns=["cell_id", "locality", "locality_type"])
    out = build_priority(ga, rates, ck)
    out["n_checklists"] = out["n_checklists"].astype("int64")
    out.to_parquet(PROC / "priority_areas.parquet", index=False)
    print(f"saved priority_areas.parquet: {len(out)} cells with light-sensitive birds, "
          f"{int(out['priority'].sum())} where night light rose at least {MIN_RATIO}x")
    return out


if __name__ == "__main__":
    main()
