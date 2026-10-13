# hybridPorousInterFoam — changes, model and verification

What was changed in the solver, why (condensed evidence), what the modified model is, how it was verified and what
is still open. Last updated 2026-10-13. Companion file: `NOTES_cases.md` (the cases, setups, results).
Precise per-change specification (code, keywords, checks): `CHANGES_of9-port.md` in the solver repo; the code of each
change: `git show <commit>` there (patch files: `git format-patch be54696..of9-port`); face-flux debug tooling
`meshing_strat_trial/2D_bench_strip/debug_faceDump/`. (Before 2026-10-13 this content was spread over
`trialWicking/NOTES.md`, `meshing_strat_trial/NOTES.md` and `trialWicking/hybridSolverChanges/` (README, patches
0001–0011): see git history for the day-by-day record.)

## Versions, binaries, keywords

Repo `~/OpenFOAM/martin_sng-9/run/hybridPorousInterFoam`, branch `of9-port` (fork of Franjcf/hybridPorousInterFoam
`c0b8f74`, pushed to `martinsngr/hybridporousinterfoamperso`; remote `upstream` = the original). Tag
`of9-port-before-porous-fixes` = `be54696` = OpenFOAM 9 port only (API renames, physics of upstream).

| Change | Commit | Keyword (`constant/transportProperties`) | Default | What it does | Acts on |
|---|---|---|---|---|---|
| A | `b0c0f67` | — | on | phase relative flux from two-point face Darcy fluxes (`alphaEqn.H`) | porous faces |
| B | `cf95c59`, fix `c0c1b4e` | `darcyFaceMaxDa 0.1` | off | Darcy total flux in porous faces with K/Δx² below the value; Darcy cells take U = reconstruct(φ) (`pEqn.H`) | porous faces |
| C | `b93e429`, fix `b995db5` | — | on | kr upwinded by each phase's flux; drag keeps linear mobility | porous faces |
| E | `c3a2e6e` | — | on | bug fix: `Solidf` stays 0/1 every step and on coupled patches (`binarySolidf.H`) | porous/free faces |
| F | `febfcae` | — | on (only with B) | U of cells with Darcy and non-Darcy faces from each face's own mobility | mixed cells |
| G | `1b007d8` | `porousFreeDarcyFaces on` | off | porous/free faces = two-phase Darcy faces: pc = 0 in free cells, harmonic K, water Darcy flux as α flux (capillary jump at the yarn surface) | porous/free faces |
| H | `1588863` | `porousContactAngleWallLike 1` (+ `activatePorousContactAngle 1`, `theta0`) | off | contact angle applied on porous/free faces only, as a wall; interface normal ignores the porous saturation (library `porousInterfaceProperties.C`) | free interface at porous surfaces |
| F′ | `3aded21` | `porousFreeFluxForce 1` | off | U of free cells next to porous/free Darcy faces carries the face flux | free cells next to yarns |
| I | `b525086` | `porousFreeNoSlip 1` | off | no-slip at porous/free Darcy faces (2·μ_free, half-cell distance; never below the old coupling) | free cells next to yarns |

(No D: the inlet treatment was investigated, never a change.) Docs commits `d1c688a`, `3234fbf`, `8b35cc4`, `1a79db9`.

- **Which keywords:** cases without free cells (1D, single yarn): `darcyFaceMaxDa 0.1` (A, C, E, F act; G–I change
  nothing, bit-identical). Porous + free fluid (2D bench, REV): additionally `porousFreeDarcyFaces on`,
  `activatePorousContactAngle 1`, `theta0`, `porousContactAngleWallLike 1`, `porousFreeFluxForce 1`,
  `porousFreeNoSlip 1` (G + H + F′ + I validated together, not meant separately) and free cells initialised as pure air.
- **Installed (laptop):** `hybridPorousInterFoam` = `b525086` (A–I), checked bit-identical to the tested build (keywords on)
  and to `1b007d8` (keywords off). Backups: `_1b007d8` (A–G), `_c3a2e6e` (A–C + E), `_b995db5` (A–C), `_be54696` (port).
  The libraries are shared by all binaries (H keeps the class layout and is inactive without its keyword).
  `hybridPorousInterFoamH` + libraries `...H` = obsolete scratch build, can be deleted.
- **Build:** `wmake libso` in `OpenFoamV8/libraries/porousInterfaceProperties` (H), `wmake` in
  `OpenFoamV8/solvers/hybridPorousInterFoam`. Every machine rebuilds after a pull (**mini01: pull, then both**).
  Keep the old binary first: `cp $FOAM_USER_APPBIN/hybridPorousInterFoam $FOAM_USER_APPBIN/hybridPorousInterFoam_<hash>`.
  Older state: `git worktree add /tmp/hpif_<commit> <commit>`, new `EXE` in `Make/files`, `wmake`.
- **Compare with the original:** `git log --oneline of9-port-before-porous-fixes..of9-port`,
  `git diff of9-port-before-porous-fixes of9-port -- OpenFoamV8`, `git show <commit>`.

## The model as it is now

The paper's solver (Carrillo, Bourg & Soulaine 2020) is a micro-continuum (Darcy–Brinkman–Stokes) model: one momentum
equation everywhere, porous drag, a smeared `Solid` transition, no capillary term on porous/free faces. With B + G + H
+ F′ + I it becomes a **sharp-interface coupling of two-phase Darcy flow (yarns) and VOF Navier–Stokes (gaps)**, on one
mesh with one pressure equation and one α field:
- inside the yarns (B): two-phase Darcy flux (impesFoam-like), no Brinkman momentum;
- at the yarn surface: mass = Darcy flux with harmonic K; normal stress = continuity of the phase pressures (G, Mosthaf
  et al. 2011 type); tangential = no-slip relative to the porous velocity (I, Beavers–Joseph slip neglected); wetting =
  contact angle as a wall condition (H); velocity of the adjacent gap cells consistent with the face flux (F′);
- in the gaps: VOF with surface tension, as in the paper.
**It must be presented as our model, not the paper's**, and the paper's validation does not carry over.

Assumptions and their limits:
- √K ≪ Δx (no Brinkman layer to resolve; Darcy faces need Da = K/Δx² < `darcyFaceMaxDa`) and Δx ≳ fibre scale (the yarn
  continuum ε, K, pc(S), kr(S) needs several fibres per cell; polyester fibre ~10–15 µm). **Mesh window 10–20 µm**
  (10 µm needs `darcyFaceMaxDa 0.5`); below ~5 µm the Darcy faces revert to the momentum path and the coupling is
  inconsistent. A finer description means fibre-resolved pore-scale VOF (~1 µm), feasible only on small pieces.
- Inertial relaxation in the yarns fast (ρK/(με) 2e-5 s water, 1e-6 s air ≪ wicking time).
- Slip: length ≈ √K/α_BJ ≤ √K ≈ 3 µm vs 20 µm cells and 160–300 µm gaps → a few % at most on the gap flow.
- pc = 0 in free cells: the yarn's pc at its surface saturation acts as a jump across the surface (menisci in the
  surface pores); the gap meniscus curvature is the VOF part.
- One contact angle θ, independent of the yarn's saturation (wrong on wet yarn surfaces, see open issues).
- Uniform meshes: G (phase-pressure differences) and H, I use 0.5 interpolation weights.

## Why each change (condensed evidence)

### A, B — instability of the yarn in 2D/3D (2026-10-01)
With yarn properties (K 1e-11, VG pc0 5000 Pa m 0.5, dry 0.002) the original solver diverged in 2D/3D within a few
hundred steps (a transverse α mode growing ×1.25–1.5 per step from round-off; the 1-cell-wide 1D column survived) and
gave a staircase 1D profile. Bench: the 1D column widened to NX cells (symmetry sides).
- **Part 1 → A:** `phirPore` interpolated cell velocities built with `fvc::grad`; an averaged gradient is blind to
  odd-even patterns (two alternating cells give zero gradient on their common face). Face fluxes with `snGrad` (same
  operators as `phiPc`) give a smooth 1D profile and the NX = 5 bench runs to 0.2 ms.
- **Part 2 → B:** with A, a transverse mode still grew: the momentum-equation cell velocity alternated between rows
  (0.08–0.30 m/s, face flux uniform) and fed back through `HbyA`. B (Darcy flux on Darcy faces) keeps the spread at
  round-off (1e-9 NX = 2, 8e-8 NX = 5), same mean α for NX = 1, 2, 5, ~5× fewer steps. 5 ms: spread ≤ 4e-7.
- **Is B needed? (2026-10-07, `trialWicking/verification/bench_ddtCorr/`):** ddtCorr coefficient 1 / 0.1 / 0, removing
  inertia (`ddt steadyState`, crashes earlier), tight pressure tolerance (seed 3e-5 → 2.4e-9 but same growth rate
  ~6e5–1e6 1/s, saturation 0.05–0.2): none removes the mode; only B does (spread ≤ 1.3e-7). **B is needed**; mechanism
  beyond "the momentum flux in porous faces feeds it" not established (decided not to dig further).
- **B fix:** boundary Da used half a cell (4× too large): on 10 µm the inlet/outlet fell out of the Darcy set, GAMG
  stalled. Boundary Da now uses the cell size.
- **Open lateral wall of the single yarn is ill-posed** (independent of A/B): on a patch with `Uwetting` fixed and `U`
  not fixed, `correctUBc.H` replaces the face flux by (Uwetting_b + UnonWetting_b)·Sf, i.e. the cell's air velocity
  projected on the tilted wall normals (|U| ≈ 700 m/s after one step). The yarn cases close the lateral wall.
- **Fixed-velocity inlets with B:** a fixed U with zeroGradient p gives no inflow on a Darcy face (flow-driven
  Buckley–Leverett): use p `fixedFluxPressure`. The wicking cases fix p: not affected.

### C — upwinded kr
Linear kr halves the water mobility of the face between a wet and a dry cell: slower front and a spurious foot ahead
of it (bench 0.2 ms leading edge 0.134/0.076 → 0.184/0.130 mm, impesFoam 0.208/0.146; 1D tail ahead of the front
2.0 → 5.8 µm original vs ≤ 0.5 µm with C). Fix: the drag keeps the linear mobility, so C does not change the momentum
equation of porous cells next to free fluid.

### E — `Solidf` bug (2026-10-12)
First 2D-bench run with free cells (strip between free layers): the wet porous cells next to the free cells emptied in
one step, then p ±1e15, dt collapse. Face-flux dump of step 1: `updateDarcyVelocities.H` recomputes `Solidf =
interpolate(Solid)` every step **without** the start-up clipping, so porous/free faces had `Solidf` = 0.5: half-active
porous fluxes with K interpolated to 0.5 m² (K_VOID 1) and the free cell's VG pc (2.5 MPa when dry): relative flux 1.6e4
vs 1e-26 on porous/porous faces. σ, contact angle and BCs had no effect. Upstream history (`git log -S`): first commit
`0a12b0b` unclipped (0.5), `cd088db` (2019-10-28) clipped to 0/1 = **no porous capillary term on porous/free faces by
design**, `98e48b9` (2020-09-11, dynamic mesh) brought 0.5 back by accident. **E restores `cd088db` but changes current
upstream behaviour for cases with porous/free faces** (results obtained with upstream code since 2020-09, possibly
published ones, used the half term). Checks: bit-identical without free cells (1D 0.1 s, all-porous bench); first-step
failure gone; a processor boundary on the porous/free faces failed with internal-only clipping and matches serial with E.

### F, G — no capillary jump at the yarn surface (2026-10-12)
With E the strip bench failed later (1.8e-5 s): the yarn drained instead of wicking. Evidence: p is the mixture pressure
p_air − α·pc in porous cells and the fluid pressure in free cells; on porous/free faces (no capillary term by design) p
was continuous, so the yarn's air pressure exceeded the gap air by α·pc (4–5 kPa, ≈ pc0 even when dry for m = 0.5). A
causality build (all porous cells U = reconstruct(φ)) ran but drained (mean yarn saturation 0.101 → 0.048 instead of
0.197). Inlet BC variants failed earlier, PLIC changed nothing: the failure sits at interior yarn/gap faces. Physical
condition: air pressure continuous next to an air-filled gap, water pressure next to a water-filled one (Mosthaf et
al. 2011). Boubaker et al. 2026 don't see it (pressure-driven 50 kPa, α·pc ~10 Pa).
- **F:** B's mixed cells rebuilt U with `pEqn.flux()/rAUf`, Mf/rAUf too large on Darcy faces (U drifted m/s per step:
  39–72 m/s at step 10 on the bench, 2.3e4 m/s in single-yarn wall cells). F uses each face's own mobility. α, p, φ
  unchanged where tested (single yarn 225 steps bit-identical; only the written U changes, 2.3e4 → 18.9 m/s). **U written
  by older binaries near walls or porous/free faces is not meaningful.**
- **G:** see the table above. Referees (strip bench, all patches closed, 0.2 ms): R1 static wet yarn + air gaps: yarn
  water 99.9999 % kept; R2 dry yarn next to a water-filled gap: imbibes (37.8 cell volumes, E: 0.04); R3 closed ramp:
  yarn water lost −0.04 % (E −42 %), profile within 0.0005 of the no-gap reference from 0.1 ms. 5 ms: R1 −0.0004 %, R3
  profile ≤ 4e-5; yarn + air gaps wicks like the no-gap reference +2–5 % (lateral air escape). Parallel and cyclic
  porous/free faces: no systematic error (differences at solver-tolerance level). A first version with the drift-form
  α flux on porous/free faces leaked (R3 −8.3 %): those faces carry `phiWetting` itself.
- **Setup rule from G:** free cells must start as pure air (α 0; at 0.002 surface-tension currents grew and a run
  collapsed at 2.58 ms).

### H, F′, I — free flow next to porous walls (2026-10-13)
Thick-wall slit (porous walls 8 cells, gap 8, 20 µm, θ 60°, 2 ms; cases in `meshing_strat_trial/slit_test/`) with G but
the original porous contact-angle model: K 1e-20 (impermeable) walls 24–68 m/s and water droplets ahead of the
meniscus; K 1e-17 rose faster than K 1e-20 (unphysical); films of α 0.1–0.4 ahead along the walls; with 4-cell walls the
rise was −35 % to +60 % off the real-wall rise depending on width and angle.
- **H:** `correctContactAngleDB` (1) computed the interface normal from α including porous cells (a saturation: water
  next to a dry wall looks like an interface parallel to it, a wet wall next to a dry gap cell like a film), (2) imposed θ
  on a band 2–3 cells deep on both sides of the surface (most of a 4–8-cell gap). Alone, H fixed K 1e-11 walls (1.4 m/s)
  but not K 1e-20 (14–49 m/s). A ghost-α variant (as `constantAlphaContactAngle`) changed nothing, not kept.
- **F′:** F's force on Darcy faces is φ/Mf, ill-conditioned when Mf → 0: the near-wall gap cells had a wall-normal
  velocity larger than the tangential one (0.87 vs 0.52 m/s at K 1e-20). With H + F′: 0.8–1.1 m/s everywhere, no
  droplets, ordering in K physical. F′ also removed the unexplained gap air jet of the strip bench (8.6 → 0.10 m/s, yarn
  unchanged to 3–4 digits).
- **I:** the gap cell was coupled to the porous cell centre (Δx) with μ interpolated with the (air-filled) porous cell:
  about a quarter of a wall's shear; near-wall/mean velocity 0.78 (real wall 0.41), rise 12–28 % too fast. I gives
  2·μ_free; bounded below by the old coupling because the exact value (2·μ_air next to a wet wall) produced 10–60 m/s air
  currents along wet walls (not understood).
- Development sequence on the 8-cell slit (an informal ablation): G only 25–68 m/s + droplets → + H 14–49 m/s → + F′
  ~1 m/s but 12–28 % too fast → + I within 2 %.

## Verification

### Against the paper and analytical solutions (`trialWicking/verification/`, 2026-10-05 to 10-09)
- **OF9 port physics-neutral** (API renames only; porous libraries unchanged; OF8 not rebuilt for a bitwise check).
- **Gravity-driven Buckley–Leverett (paper 4.1.2):** original port and A+B+C both: plateau −0.1 %, front −0.11 to −0.16 %,
  same water deficit 0.24 % from the inlet treatment (`alphaEqn.H` divides the boundary relative flux by εα_b + 0.001;
  with + 1e-8 the deficit disappears: not changed). With p `fixedFluxPressure` + U fixed at the inlet (paper's
  setup): interior flux exact, front −0.15 %.
- **Flow-driven Buckley–Leverett (4.1.1), p `fixedFluxPressure` (needed with B):** front −0.12 % original, −0.07 % A+B+C.
- **Gravity–capillarity equilibrium (4.1.3, Brooks–Corey, 30,000 s):** original approaches the static profile (not
  fully converged); **A+B+C fails with a cell-to-cell oscillation** (roughness 0.29 → 0.89) in this counter-current, zero
  total flux case. **Open, cause not isolated.** Not present in the co-current wicking runs (local-extremum scan of every
  1D and single-yarn field: same level as the impesFoam twins).
- **1D capillary wicking vs similarity solution** (front 18.04 mm/√s, uptake 6.105 mm/√s from the inputs; 20 µm):
  impesFoam front −0.5 %, hybrid original −0.8 %, modified −1.6 %; uptake −2.2 / −4.4 / −4.6 %. Split of the hybrid's
  −4.6 %: ~2 % from the 1 % air its inlet BC lets in, ~2.5 % physical air back-pressure (the similarity solution assumes
  uniform air pressure: with μ_air/100 both solvers are within 0.3 %), ≤ 0.3 % numerics (one mesh). The modified solver
  removes the original's spurious foot ahead of the front. `1D_vertical_hybrid` 0.1 s vs impesFoam: mean α −1.1 to −4.8 %.
- **Single yarn (3D):** original diverged within 10 steps; modified runs to 0.1 s (mini03, 11.9 h, mean α 0.899 vs
  impesFoam 0.904).

### Free-surface part and porous/free coupling (`meshing_strat_trial/slit_test/`, `2D_bench/`)
- **Real-wall slit (S0) vs the analytical slit rise (Bosanquet):** 2–11 % (gaps 4/8/15 cells, θ 40/60/80°) with the
  total-pressure inlet; stock interFoam on the same slit = our solver to 0.01 mm.
- **Impermeable porous walls (K 1e-20, G + H + F′ + I) vs real walls:** within 2 % at all widths and angles (gap 4: 1.33 /
  1.32 mm; 8: 1.27 / 1.25; 15: 1.01 / 0.99; θ 40: 1.57 / 1.54; θ 80: 0.73 / 0.72), max |U| 0.45–1.2 m/s.
- **Permeable walls:** gap rise monotone in K (1.27 > 1.23 > 0.79 mm for K 1e-20 / 1e-14 / 1e-11); K 1e-11 walls fed sideways
  by the gap (wall front 1.15 vs 0.87 mm without gap). 10 µm vs 20 µm: 20 µm 3–4 % fast. Water budget ~1e-25.
- **`2D_bench/check.py`:** run/conservation checks plus ordering checks (meniscus below the impermeable rise, wall front
  ahead of the walls-alone estimate, front uniform across the wall). Plausibility, not quantitative validation.
- **Meniscus:** depth resolved only 1–2 cells at 8–15 cells across; the rise is right because the contact angle sets
  the normal at the wall. One pressure-jump measurement during the rise (8 cells, θ 60°): 340–410 Pa vs 2σcosθ/w = 450.
- **Not validated quantitatively: the coupled physics** (how much water the yarn takes from the gap, the interface
  pressure jump). Needs a fibre-resolved reference or an experiment.

### Regressions (bit-identical)
- Without free cells, every change since C: 1D 0.1 s and single yarn (225 steps / 1e-5 s) for E, F, G, H–I builds
  (last check 2026-10-13 with `b525086` vs stored results and vs `1b007d8`).
- Keywords off: `b525086` = `1b007d8` on the slit; G off/on without porous/free faces: identical.

## Open issues

Solver behaviour:
- Gravity–capillarity equilibrium oscillation with A+B+C (counter-current, zero total flux): cause not isolated.
- I: why the exact coupling (2·μ_air next to wet walls) gives fast air currents (I bounded meanwhile).
- `Free_Flow_Cases/Capillary_Rise/porous_Boundary` tutorial: A and C change the free water by +0.40 / +0.11 % (mechanism
  not identified); not rerun with E, F, G, H–I. **Original vs E on this tutorial = the evidence of what E changes in
  published-type cases** (not done).
- Inlet: `+ 0.001` in the boundary relative flux (0.23 % deficit at a fixed-velocity inlet); the hybrid reservoir inlet
  lets in 1 % air; a water-only reservoir inlet BC does not exist yet.
- Not tested: non-uniform meshes (G, H, I), parallel/cyclic porous/free faces with H/F′/I, 3D edges/corners and
  staircased surfaces, `momentumPredictor` on, harmonic K set at start-up only (no dynamic meshes), runs > 5 ms.
- Porous faces on an open (fixed-p) boundary are unstable: close such boundaries or pad them with free cells.
- `createPorousMediaFields.H` interpolates kr2 with the `"kr1"` scheme name (harmless with linear).

Model questions (raised by an independent review, 2026-10-13; answers so far in brackets):
- Counter-current flow across yarn/gap faces (air out, water in): check for sign-flipping face fluxes or alternating
  saturation along the yarn surface [not checked; R2 is counter-current and stable].
- kr on yarn/gap faces when water flows gap → yarn is taken from the gap cell's VOF α through Brooks–Corey [code
  behaviour, no physical argument; alternative: kr = 1 for the phase filling the gap cell, or yarn-side kr; to test].
- H: which θ (apparent angle on an absorbing surface ≠ Young angle; 60° is the validated test value, polyester ~70–80°
  is a guess); H imposes θ on wet yarn surfaces where physically there is no contact line (biases the gap rise low);
  possible double counting of G (imbibition) and H (wetting) [not ruled out].
- I: state the slip assumption with its bound (above).
- Verification still missing: static meniscus at 4/8/15 cells (Δp vs 2σcosθ/w, no flow); ablation of G, H, F′, I one at
  a time on the 15-cell slit (K 1e-11 and 1e-20, plus H with θ 90°); kr variant on yarn/gap faces; porous_Boundary
  original vs E. Planned in this order (see `NOTES_cases.md`, Next steps).
- Thesis: say the interface model changed (supervisor to be informed); cite Mosthaf et al. 2011.
