# Findings (Member 3)

Data: 15,890 eBird checklists (≤ 2 km, thinned) in 1,364 cells of Greater Manila, 2014–2025; 143 focus species (61 light-sensitive, 82 light-tolerant).

## Headline

_Pending: needs Member 2's covariates (grid_monthly, grid_landcover)._

## Data checks (baseline model)

- PASS: log_duration coefficient is positive (longer checklists detect more)
- PASS: model converged, no NaN coefficients
- PASS: migrants reported more in Oct-Mar

- Effort-corrected detection trend per year: tolerant ×1.020 (1.006–1.034), sensitive ×1.023 (1.002–1.043). 2014–2016 data are sparse.

## Spatial checks (Moran's I, 999 permutations)

- gaps: I = 0.308, p ≤ 0.001 (17,835 cells, all cells (provisional: includes water))
- effort: I = 0.226, p ≤ 0.001 (1,459 cells, observed cells)
- residuals (baseline model): I = 0.525, p ≤ 0.001 (394 cells, cells with >= 5 checklists)

## Caveats

- Association, not causation.
- eBird detection is not abundance; effort (duration, distance, observers, time of day) is modelled.
- Results cover Greater Manila only. 88% of checklists are from 2020–2025.
- Nocturnal species, potentially the most affected by light, are under-sampled by daytime birding and mostly fall below the focus threshold, so effects are likely underestimated.
- Observation gaps are never filled; statistics use real checklists only.