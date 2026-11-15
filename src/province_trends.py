"""Province significance table for the app's "Where it changed" map (Member 3, part A step 3).

Runs trends.region_trends for every province x variable over 2014-2025, with Benjamini-Hochberg FDR
per variable, and writes data/processed/province_trends.parquet in the schema the app reads.

Run from the project root:  python src/province_trends.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trends  # noqa: E402

MONTHLY_VARS = ["alan", "ndvi", "lst_day", "rain_mm"]
YEARLY_VARS = ["urban_frac", "forest_frac"]
COLUMNS = ["variable", "adm2_code", "province", "n_months", "tau", "p_value", "q_value", "significant",
           "slope_per_year", "change_pct", "direction"]
PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


def build_province_trends(pm: pd.DataFrame, pl: pd.DataFrame) -> pd.DataFrame:
    """Trend results per province x variable.

    pm: province_monthly (adm2_code, province, year, month, monthly variables).
    pl: province_landcover (adm2_code, year, yearly land-cover shares).
    n_months = valid months used for monthly variables, valid years x 12 (months covered) for yearly ones.
    """
    pm = pm.assign(adm2_code=pm["adm2_code"].astype("int64"))
    pl = pl.assign(adm2_code=pl["adm2_code"].astype("int64"))
    monthly = trends.region_trends(pm, "adm2_code", MONTHLY_VARS)
    yearly = trends.region_trends(pl.drop(columns=["month"], errors="ignore"), "adm2_code", YEARLY_VARS)

    n_m = pm.groupby("adm2_code")[MONTHLY_VARS].count().stack().rename("n_months")
    n_y = (pl.groupby("adm2_code")[YEARLY_VARS].count() * 12).stack().rename("n_months")
    n = pd.concat([n_m, n_y]).rename_axis(["adm2_code", "variable"]).reset_index()

    names = pm.drop_duplicates("adm2_code")[["adm2_code", "province"]]
    out = (pd.concat([monthly, yearly], ignore_index=True)
             .merge(n, on=["adm2_code", "variable"], how="left")
             .merge(names, on="adm2_code", how="left"))
    out["adm2_code"] = out["adm2_code"].astype("int64")
    out["n_months"] = out["n_months"].fillna(0).astype("int64")
    out["significant"] = out["significant"].astype(bool)
    return out[COLUMNS].reset_index(drop=True)


def main() -> pd.DataFrame:
    pm = pd.read_parquet(PROC / "province_monthly.parquet")
    pl = pd.read_parquet(PROC / "province_landcover.parquet")
    out = build_province_trends(pm, pl)
    out.to_parquet(PROC / "province_trends.parquet", index=False)
    print(f"saved province_trends.parquet: {len(out):,} rows "
          f"({out['adm2_code'].nunique()} provinces x {out['variable'].nunique()} variables)")
    print(out.groupby("variable")["significant"].agg(["sum", "size"]).rename(
        columns={"sum": "significant", "size": "provinces"}).to_string())
    return out


if __name__ == "__main__":
    main()
