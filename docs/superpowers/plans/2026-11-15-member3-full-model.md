# Member 3 Full Model + Province Trends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the full night-light bird model on Member 2's covariates, produce `province_trends.parquet`, and close Member 3's open plan checks.

**Architecture:** Province trends become a small tested function in `src/province_trends.py` (wraps `trends.region_trends`, maps to the app's schema) plus a CLI entry that writes the parquet. Bird-model fixes stay inside `notebooks/03_member3_bird_model.ipynb`; the notebook is executed with a scratch runner (no Jupyter installed) that execs code cells in order and writes stream outputs back into the `.ipynb`.

**Tech Stack:** Python 3.14, pandas, numpy, statsmodels, libpysal/esda, pytest. Existing `src/trends.py`.

**Spec:** `docs/superpowers/specs/2026-11-15-member3-full-model-design.md`

## Global Constraints

- Water rule for main model: drop cells with `water_frac > 0.5` (approach A); robustness refit includes them.
- Collinearity rule: drop NDVI if |r(log_alan, ndvi)| > 0.7; `urban_frac` always out; `forest_frac` is the habitat term.
- Row dropping for missing covariates uses only the covariate terms kept in the model.
- `effect_curve.parquet` columns: `group, sensitive, alan, prob, ci_low, ci_high`.
- `province_trends.parquet` columns: `variable, adm2_code, province, n_months, tau, p_value, q_value, significant, slope_per_year, change_pct, direction`.
- Variables for province trends: `alan, ndvi, lst_day, rain_mm` (monthly, Seasonal MK) and `urban_frac, forest_frac` (yearly, Hamed-Rao); FDR per variable.
- `grid_monthly.parquet` lives in `data/processed/` and is git-ignored.
- Mock results are never reported; outputs are real-data only.

## Review Focus

- Province with an all-NaN variable (e.g. NDVI fully cloudy) → row present, `direction = "no significant trend"`, no crash. Test in Task 1.
- `adm2_code` dtype differs between monthly (int64) and landcover (int32) tables → output column is int64 for the app's GeoJSON join. Test in Task 1.
- Robustness variant that ends up with a constant term (residents-only `migrant`) → term dropped, no singular fit. Covered by existing guard; keep it in Task 2.
- Water-inclusive variant: NDVI/LST missing in water cells → only kept terms trigger dropping. Verified by row counts printed in Task 3.
- `findings.md` headline must parse in `app/load_data.findings()` (paragraph under `## Headline`, no leading `-`). Checked in Task 3.

---

### Task 1: Province trends module

**Files:**
- Create: `src/province_trends.py`
- Test: `tests/test_province_trends.py`

**Interfaces:**
- Consumes: `trends.region_trends(df, region_col, variables, ...)`.
- Produces: `build_province_trends(pm: pd.DataFrame, pl: pd.DataFrame) -> pd.DataFrame` (schema above); `main()` reads `data/processed/province_monthly.parquet` + `province_landcover.parquet`, writes `data/processed/province_trends.parquet`. Run as `python -m src.province_trends`.

- [ ] **Step 1: Write tests** — synthetic two provinces × 144 months (A: +1/yr trend + seasonality + noise; B: noise only, NDVI all NaN) and 12 yearly landcover rows each.
  - `test_schema`: columns exactly the schema list; 2 provinces × 6 variables = 12 rows; `adm2_code` dtype int64.
  - `test_trend_detected`: province A `alan` → `significant` True, `direction == "increasing"`, slope within 10% of 1.0.
  - `test_all_nan_variable`: province B `ndvi` row exists, `significant` False.
  - `test_n_months`: monthly `alan` with 144 valid months → `n_months == 144`; yearly `urban_frac` with 12 valid years → `n_months == 144` (valid years × 12, months covered; documented in the docstring).
- [ ] **Step 2: Run** `python -m pytest tests/test_province_trends.py -q` → FAIL (module missing).
- [ ] **Step 3: Implement** — call `region_trends` on `pm` (monthly vars, region `adm2_code`) and `pl` (yearly vars); concat; merge `province` from `pm`; `n_months` from non-null counts; select schema columns.
- [ ] **Step 4: Run** tests → PASS; full suite `python -m pytest tests -q` → all pass.
- [ ] **Step 5: Run** `python -m src.province_trends` → writes 85 × 6 = 510 rows; spot check Metro Manila ALAN direction.

### Task 2: Notebook fixes

**Files:** Modify `notebooks/03_member3_bird_model.ipynb` cells [8], [14], [18], [20].

- [ ] `add_covariates(c, terms, keep_water=False)`: merge as now; water filter unless `keep_water`; `dropna` on `terms` (+ `forest_frac`) only. Section 3 computes correlation/VIF on the merged-but-not-dropped water-filtered table, decides `COV_TERMS`, then drops.
- [ ] Section 3 prints the trait mapping table is already in [4]; keep VIF printed.
- [ ] Effect curve saved with `prob, ci_low, ci_high`.
- [ ] `model_coefficients.csv`: add `label` column; append derived rows `z_log_alan (tolerant)` and `z_log_alan (sensitive)` from `lincomb`.
- [ ] Robustness variants add `"incl. water-heavy cells"` (`keep_water=True`) and `"without LST"` (formula without `z_lst_day`).
- [ ] New raw cross-check: ALAN quartile × group reporting rate on the main sample; check passes if the sign of (Q4 − Q1) per group matches the sign of the effect curve's (p95 − p5) per group.
- [ ] Findings: Moran's I sentences for gaps (land-only) and effort, residual result, block-cluster p when present, cautious headline note if residuals are clustered.

### Task 3: Execute, review, finalise

- [ ] Move `data/grid_monthly.parquet` → `data/processed/`; add `data/processed/grid_monthly.parquet` to `.gitignore`.
- [ ] Execute notebook with scratch runner; all checks PASS; read headline, robustness, residual Moran's I.
- [ ] Verify `app.load_data.findings()`-style parsing of the headline; load `effect_curve.parquet` columns.
- [ ] Tick Member 3 boxes in `docs/TEAM_BUILD_PLAN.md`, update status line; update handoff note's remaining list.
- [ ] Commit (code, notebook, outputs, docs; not `grid_monthly.parquet`).
