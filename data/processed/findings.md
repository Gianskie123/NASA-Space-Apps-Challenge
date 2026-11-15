# Findings (Member 3)

Data: 12,953 eBird checklists (≤ 2 km, thinned) in 1,136 cells of Greater Manila, 2014–2025; 143 focus species (61 light-sensitive, 82 light-tolerant).

## Headline

Per 1 SD more night-time light (about 3× brighter), the odds of detecting a light-sensitive species change by ×0.53 (95% CI 0.47–0.59), versus ×0.88 (0.82–0.95) for light-tolerant species. Difference between groups: p ≤ 0.001 (CIs and p-values clustered by cell). The difference comes from resident species: ×0.35 for resident light-sensitive vs ×0.89 for resident light-tolerant species (p ≤ 0.001), while migratory light-sensitive and light-tolerant species respond alike (×0.74 vs ×0.77, p = 0.700). Model residuals are spatially clustered, so with larger 5×5-cell block clusters the difference has p ≤ 0.001; this is the cautious figure to quote.

## Sample

- 15,890 thinned checklists → 14,059 after dropping cells more than 50% water → 12,953 with every model covariate.
- Model covariates: log_alan, forest_frac, lst_day, rain_mm. NDVI left out if |r| with night light > 0.7; urban share left out (duplicates night light); forest share is the habitat term.

## Robustness

```
                variant  interaction_coef  interaction_or p_value  n_checklists
main (<= 2 km, thinned)           -0.5094          0.6009 1.8e-23         12953
            no thinning           -0.5313          0.5878 3.9e-28         17425
         residents only           -0.9195          0.3987 3.0e-17         12953
                <= 5 km           -0.4991          0.6071 3.6e-25         14831
incl. water-heavy cells           -0.4990          0.6071 5.2e-26         13679
            without LST           -0.5086          0.6014 1.5e-23         12953
```

## Data checks

- PASS: log_duration coefficient is positive (longer checklists detect more)
- PASS: model converged, no NaN coefficients
- PASS: migrants reported more in Oct-Mar
- PASS: full model converged, no NaN coefficients
- PASS: raw ALAN-quartile rates point the same way as the effect curve (both groups)
- PASS: key term keeps its sign in every robustness variant

- Effort-corrected detection trend per year (baseline model): tolerant ×1.017 (1.002–1.032), sensitive ×1.002 (0.977–1.027). 2014–2016 data are sparse.

## Spatial checks (Moran's I, 999 permutations)

- gaps: I = 0.285, p ≤ 0.001 (13,279 cells, land cells only)
- effort: I = 0.231, p ≤ 0.001 (1,268 cells, observed cells)
- residuals (full model): I = 0.215, p ≤ 0.001 (321 cells, cells with >= 5 checklists)
- residuals (baseline model): I = 0.307, p ≤ 0.001 (321 cells, cells with >= 5 checklists)

For the app and slides:

- Unobserved cells are spatially clustered (Moran's I = 0.29, p ≤ 0.001, land cells only), so missing data is not random; we keep them as observation gaps rather than filling them.
- Birdwatching effort is also clustered (Moran's I = 0.23, p ≤ 0.001), which is why we thin hotspot checklists and cluster standard errors by cell.

## Caveats

- Association, not causation.
- eBird detection is not abundance; effort (duration, distance, observers, time of day) is modelled.
- Results cover Greater Manila only. 88% of checklists are from 2020–2025.
- Cells more than 50% water are left out of the main model (their satellite values describe the bay); this removes the main wetland and mudflat hotspots. A refit that keeps water-heavy cells only partly restores them (many lack land-temperature values) and gives the same result (robustness table).
- Daytime land temperature (MODIS Terra) falls after 2020 almost everywhere; this most likely reflects Terra's drifting, earlier overpass time rather than real cooling, so LST trends after 2020 should be read with care. A refit without LST is in the robustness table.
- Nocturnal species, potentially the most affected by light, are under-sampled by daytime birding and mostly fall below the focus threshold, so effects are likely underestimated.
- Observation gaps are never filled; statistics use real checklists only.