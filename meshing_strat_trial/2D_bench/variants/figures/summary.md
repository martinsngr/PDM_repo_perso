# 2D bench with change G: summary

Installed solver (of9-port 1b007d8), `porousFreeDarcyFaces on`, free cells initialised as pure air, 5 ms, writes every 0.1 ms.

| Check | Result | Criterion | Pass |
|---|---|---|---|
| yarn alone (no gaps): reference: reaches 5 ms | ended at 5 ms | 5 ms | yes |
| yarn + air gaps: reaches 5 ms | ended at 5 ms | 5 ms | yes |
| yarn + gaps, reservoir water also in the gaps: reaches 5 ms | ended at 0.565148 ms | 5 ms | NO |
| front slope, yarn alone (no gaps): reference | 17.49 mm/√s (fit 0.5–2.2 ms, offset +0.078 mm) | ≈ 18.04 (1D similarity; gaps: slightly faster expected) | yes |
| front slope, yarn + air gaps | 17.88 mm/√s (fit 0.5–2 ms, offset +0.083 mm) | ≈ 18.04 (1D similarity; gaps: slightly faster expected) | yes |
| water budget, yarn alone (no gaps): reference | stored 1.997e-12 m³, entered 1.997e-12 m³, max imbalance 9.1e-27 m³ (4.6e-15 rel.) | imbalance ≪ stored | yes |
| water budget, yarn + air gaps | stored 1.212e-12 m³, entered 1.212e-12 m³, max imbalance 1.0e-26 m³ (8.5e-15 rel.) | imbalance ≪ stored | yes |
| water budget, yarn + gaps, reservoir water also in the gaps | stored 3.757e-12 m³, entered 3.757e-12 m³, max imbalance 4.8e-27 m³ (1.3e-15 rel.) | imbalance ≪ stored | yes |
| yarn profile, air gaps vs alone | max diff 0.5 ms: 0.039, 1 ms: 0.038, 2 ms: 0.037, 3 ms: 0.118 | small (air escape speeds the gap case up) | see figure |
| air pressure across the yarn surface (G's condition) | max 479 Pa without the inlet column (median ≤ 17 Pa); inlet column up to 868 Pa (air back-pressure next to the reservoir, physical); α·pc 3435–4995 Pa (difference without G) | ≪ α·pc away from the inlet | check |
| R1 static: yarn water change / max gap velocity | -0.0005 % / 2.0e-03 m/s | ~0 / small | yes |
| R2 dry yarn next to water: yarn water | 0.40 → 47.03 (capacity 200) | increases | yes |
| R3 closed ramp: profile vs no-gap reference / yarn water | max 6.2e-04, at 5 ms 4.2e-05 / min -0.0001 %, end +0.0000 % | ≪ 0.01 / ~0 | yes |
