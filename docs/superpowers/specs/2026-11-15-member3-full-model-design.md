# Member 3 — full light model and province trends (short design)

Date: 2026-11-15 · Status: approved in conversation

## Intent
Finish Member 3's remaining work now that Member 2's covariates exist: run the full night-light bird model,
produce `province_trends.parquet` for the app's "Where it changed" map, complete the plan's open checks,
and finalise `findings.md`. Deadline: Nov 15, 11:59 p.m.

## Goals
- Full model (`z_log_alan * sensitive`) runs on real covariates; headline, effect curve, robustness, residual Moran's I.
- `province_trends.parquet` in the schema the app already reads (variable, adm2_code, province, n_months, tau,
  p_value, q_value, significant, slope_per_year, change_pct, direction).
- Plan checks: ALAN-quartile raw cross-check, VIF + trait tables, land-only gaps Moran's I with sentence.

## Non-goals
App changes (Member 4), add-ons, new data products.

## Approaches (water-cell rule)
The plan drops cells with `water_frac > 0.5`; that removes 2,447 checklists (10%), all at wetland/mudflat hotspots
(LPP Wetland Park, Tanza, Paombong, Balanga) where cell covariates mostly describe the bay.
- **A (picked):** keep the plan rule for the main model; add a robustness refit that includes water-heavy cells.
- B: relax threshold to 0.9 — keeps hotspots but with bay-dominated covariates.
- C: keep all cells, add `water_frac` as a covariate — no loss, harder to explain.

## Fixes found during review
1. `grid_monthly.parquet` moves from `data/` to `data/processed/`; kept out of git (35 MB, app doesn't use it).
2. Covariate dropna happened before the collinearity decision, so 45%-missing NDVI dropped rows even though NDVI
   is excluded (|r| = 0.77 with ALAN). Decide terms first, then drop rows missing only the terms kept.
3. `effect_curve.parquet` columns renamed to what the app reads: `prob, ci_low, ci_high`.
4. LST has r = 0.69 with ALAN (just under the 0.7 rule) — kept, plus a "without LST" robustness refit.

## Left to the builder
Exact wording of findings sentences; derived OR rows (tolerant/sensitive) added to `model_coefficients.csv`
with a `label` column for the app table.
