# hybridPorousInterFoam — changes, model and verification

What was changed in the solver, why (condensed evidence), what the modified model is, how it was verified and what
is still open. Last updated 2026-10-27. Companion file: `NOTES_cases.md` (the cases, setups, results).
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
| H fix | `0f6c6d4` | (with H) | — | library: processor patch values of the α modified by H refreshed (H was undone on processor boundaries, 2026-10-26) | porous/free faces on processor boundaries |
| J | `be1a3ab` | `waterOnlyPatches (<patches>)` | none | reservoir patches exchange water only: no air mobility on their porous faces, α flux = total flux, free faces closed next to air-rich cells (α < 0.5); water pressure from the p BC (`tools/pOpenAir`: hydrostatic, `reservoirWaterPressure` at `reservoirReferencePoint`) | reservoir (inlet) patches |

(No D: the inlet treatment was investigated, never a change; J is the inlet change of 2026-10-26.) Docs commits
`d1c688a`, `3234fbf`, `8b35cc4`, `1a79db9`, `f9d5e41`, `c3dbf48`.

- **Which keywords:** cases without free cells (1D, single yarn): `darcyFaceMaxDa 0.1` (A, C, E, F act; G–I change
  nothing, bit-identical). Porous + free fluid (2D bench, REV): additionally `porousFreeDarcyFaces on`,
  `activatePorousContactAngle 1`, `theta0`, `porousContactAngleWallLike 1`, `porousFreeFluxForce 1`,
  `porousFreeNoSlip 1` (G + H + F′ + I validated together, not meant separately) and free cells initialised as pure air.
  Reservoir patches: `waterOnlyPatches (inlet)` (J; REV since 2026-10-26; the 1D, single-yarn, bench and slit cases
  still use the old inlet). Bath pressure from the p BC: in the REV since 2026-10-27 the standard `totalPressure` 0
  with α 1 on all inlet faces (then p = water pressure on the yarn faces; `verification/standardOpenBC`); the coded
  `tools/pOpenAir` (`reservoirWaterPressure`/`reservoirReferencePoint`) only where the bath surface is away from the
  patch (e.g. a vertical bath face) or the inlet keeps α 0.99.
- **Installed (laptop, 2026-10-26, afternoon):** `hybridPorousInterFoam` = `be1a3ab` (A–J with the H fix), built from
  the tested sources, bit-identical to the tested scratch build (bench); `hybridPorousInterFoam_b525086` = A–I (with the
  shared library: H fix included). Not pushed (mini01 needs push, pull, rebuild). Morning step: `hybridPorousInterFoam` =
  `b525086` build (A–I) with the library
  `libporousInterfaceProperties` = `0f6c6d4` (H fix, library only); installed build bit-identical to the tested scratch
  build (bench serial and split runs), serial bench bit-identical to `b525086`. Backups of that step:
  `hybridPorousInterFoam_b525086` and the pre-fix library in `$FOAM_USER_LIBBIN/backup_b525086/` (exact `b525086`:
  `LD_LIBRARY_PATH=$FOAM_USER_LIBBIN/backup_b525086:$LD_LIBRARY_PATH`). Not pushed yet. Before (2026-10-13):
  `b525086` checked bit-identical to the tested build (keywords on) and to `1b007d8` (keywords off). Backups: `_1b007d8` (A–G), `_c3a2e6e` (A–C + E), `_b995db5` (A–C), `_be54696` (port).
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

One figure per change from the original runs (copies, scripts, limits of each piece of evidence):
`verification/solver_failures/` (2026-10-14).

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
- **Is B needed? (2026-10-07, `verification/bench_ddtCorr/`):** ddtCorr coefficient 1 / 0.1 / 0, removing
  inertia (`ddt steadyState`, crashes earlier), tight pressure tolerance (seed 3e-5 → 2.4e-9 but same growth rate
  ~6e5–1e6 1/s, saturation 0.05–0.2): none removes the mode; only B does (spread ≤ 1.3e-7). **B is needed**; mechanism
  beyond "the momentum flux in porous faces feeds it" not established (decided not to dig further).
- **Not a resolution effect (2026-10-15, `verification/bench_refinement/`):** same bench refined ×2 in every
  direction (10 × 344 × 6), original `be54696`: diverges at 1.2e-5 s (dt 1e-7) and 9.6e-6 s (dt 2.5e-8) vs 3.5e-5 s on
  the base mesh (rerun identical to the 10-07 log). Finer mesh → earlier divergence. Mode pattern on the fine mesh not
  inspected; A/A+B+C not rerun there.
- **Why the original diverges (2026-10-15, same folder, `README.md`):** the 1D profile breaks first (front inverts
  within 2–6 steps: row 9 above row 8, front frozen 6 µs), the transverse growth follows when the frozen front releases.
  A Python Darcy-limit model with the original stencils (no momentum equation) fails at the front in 1–3 steps at dt 1e-7
  and 1e-8; with A it is stable; dividing by the face α instead of the cell α does not help. Mechanism: the face flux is
  the average of cell velocities built from cell gradients, so a dry cell (pc ~ 1/Se) pulls water across its wet
  neighbour, and the dry cell's zero mobility blocks the flux into it: non-monotone, inverted front. **A removes the root
  cause in the transport; why the transverse pattern is amplified is not isolated.**
- **B failure not reproduced by the model (2026-10-15, same README):** the model extended with the momentum path
  (inertia, ddtCorr, viscous, convection, dev2, linearUpwind, 2 correctors) damps a front perturbation that grows ×300 in
  80 steps in the solver with A only. It shows that the momentum-path flux lags the capillary forcing (non-monotone 1D
  profile within ~2 µs, collapse at ~3.6e-5 s without convection, any dt), which the Darcy-limit flux avoids. **The
  mechanism of the A-only transverse mode remains unknown; whether B is the only fix is not established** (not tested:
  MULES settings, no viscous/convective terms in porous cells, in the real solver without `darcyFaceMaxDa`).
- **Without B the installed solver diverges (2026-10-15, `verification/bench_noB/`):** strip bench, `b525086` with and
  without `darcyFaceMaxDa` (= A + C vs A + B + C, only B differs): without B, spread 0.24 from 10 µs (transverse U 0.5 →
  5 → 300 m/s), uptake −2.4 → −5.7 %, α leaves [0, 1] and the run diverges at 1.28e-4 s; with B spread ≤ 3e-7 to 8.5e-4 s.
  A alone (no C, 10-07) stayed bounded to 2e-4 s: C makes the case without B worse. **B is needed; not a transient.**
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

### J — water-only reservoir (2026-10-26, `verification/waterOnlyReservoir/`)
The reservoir patch let air through: on porous faces the α flux is α_b·φ_b (`phirPore` is zero on non-coupled
patches), so the inflow at α_b 0.99 carries 1 % air and an outflow carries air in proportion to α of the cell; on free
faces an air-filled cell next to the reservoir vents air. Its two parts also disagreed on the water pressure (porous
faces air at 0 Pa with S 0.99, i.e. water at −pc(0.99) = −676 Pa; free faces water at total pressure 0): in the 2D
bench ~10 % of the gap inflow left again through the yarn inlet faces. REV smoke test (old inlet, 242k cells): the
dry yarns drained the gap water column within 0.1 ms, 112 of 290 free inlet cells turned to air, air entered through
the open top/bottom and left through the reservoir face (9e-8 m³/s at 0.1 ms), α went to −0.025 in air-filled free
inlet cells, dt collapsed to 1e-14 s and stopGuard ended the run at 0.21 ms. J (keyword `waterOnlyPatches`): no air
mobility on the porous faces of those patches, α flux = total flux on all their faces, free faces closed (zero
conductance and flux) while the cell is air-rich (α < 0.5); the p BC (`tools/pOpenAir`) sets the reservoir water
pressure, hydrostatic from a reference point, so the patch can face any direction (generic: no assumption on the
wicking direction; tested on a horizontal-wicking bench with a vertical bath face).
- 1D column (inlet water at −pc(0.99), the inflow p of the old BC): air in the inlet flux +1.00 % → 0; uptake vs the
  similarity solution −4.6 % → −3.4 %, front −1.6 % → −1.1 % (predicted −2.3 / −0.6 %: the air entry explains half of
  what the earlier `ABC_waterInlet` test suggested); same step count. Inlet water at 0 Pa (bath at the inlet level):
  +4.6 % / +3.1 % (another problem), air pressure in the first cell 1.3 kPa (air can no longer leave through the inlet).
- 2D bench (inlet water at 0 Pa): water enters through the yarn inlet faces at every write (short circuit gone), all
  `check.py` checks pass; wall front 1.15 → 1.17 mm, meniscus 0.79 mm, max |U| 1.20 m/s. Horizontal-wicking variant
  (gravity across the slit): all checks pass, meniscus +2.5 % (no gravity against the rise).
- REV smoke test (inlet water at 0 Pa): past 0.22 ms where the old inlet failed; at 0.2 ms α in [−6e-20, 1], max |U|
  0.98 m/s (old 2.85), water-filled cells 0.44 m/s (old 1.73), gap water 320 cell volumes (old 142), no air through the
  reservoir face (air leaves through top/bottom), water budget closed to 1e-13. To 0.5 ms: see `NOTES_cases.md`.

## Verification

### Against the paper and analytical solutions (`verification/`, 2026-10-05 to 10-09)
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

### Free-surface part and porous/free coupling (`verification/slit_freeSurface/`, runs in `meshing_strat_trial/slit_test/`, `2D_bench/`)
Tables and figure regenerated from the runs on 2026-10-15 (`slitVerification.py` → `summary.md`, `slit_verification.png`;
the earlier numbers here came from terminal output and were partly rounded).
- **Real-wall slit (S0) vs the analytical slit rise (Bosanquet):** +2.1 to +10.4 % at 1 and 2 ms (gaps 4/8/15 cells,
  θ 40/60/80°), always fast, largest for the 4-cell gap; total-pressure inlet. Stock interFoam on the same slit = our
  solver to 0.001 mm.
- **Impermeable porous walls (K 1e-20, G + H + F′ + I) vs real walls:** within 1.4 % at all widths and angles (2 ms, P / S0:
  gap 4: 1.322 / 1.316 mm; 8: 1.252 / 1.245; 15: 1.006 / 0.994; θ 40: 1.558 / 1.537; θ 80: 0.719 / 0.719), max |U| 0.50–2.17
  m/s (2.17 at θ 40°). P runs (scratch H build) = installed `b525086` bit-identical (V twins, α/U/p at 2 ms).
- **Permeable walls:** gap rise monotone in K (1.252 > 1.214 > 0.782 mm at 2 ms for K 1e-20 / 1e-14 / 1e-11); K 1e-11 walls
  fed sideways by the gap (wall front 1.15 vs 0.87 mm without gap). 10 µm vs 20 µm (K 1e-11): 20 µm faster, meniscus
  +7.5 → +3.7 %, wall front +9.3 → +5.0 % from 0.5 to 2 ms. Water budget ~1e-25.
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
- H fix `0f6c6d4`: 2D bench serial bit-identical to `b525086`; installed build = tested scratch build (serial and split
  runs) (2026-10-26, `verification/parallel_H/`).
- J `be1a3ab` without the keyword: 1D column 0.03 s bit-identical to the stored `verification/wicking1D/ABC`; 2D bench
  2 ms numbers identical (2026-10-26, `verification/waterOnlyReservoir/`); `tools/pOpenAir` without the keyword: same
  numbers.

## Planned: diagonal tensor K (decided with the user 2026-10-27, not implemented)

Yarn-aligned permeability K = Kperp·I + (Kpar − Kperp)·t t, as `build_fields.py --k-mode tensor` already writes it
(volTensorField `0/K`, Kpar/Kperp from Gebart with `VF_YARN`, `R_FIBRE`, `PACKING`). The REV studies it is for and
their estimates: `NOTES_cases.md`, REV case status. **Decisions:** K diagonal in the mesh axes only (`ORIENTATION
"axis"`: t = x or y exactly); **harmonic** face value of the normal components on all porous faces; one commit in the
solver repo with `CHANGES_of9-port.md` updated (letter to assign: "K" would clash with the permeability).

**Why diagonal is simple and exact here:** since A every porous flux is a two-point flux k0f·snGrad·|Sf|
(`phiWetting`/`phiNonWetting` in `alphaEqn.H`; `phiDarcyExplicit`, the p Laplacian with `rAUfD = Mf` and F's
reconstruct in `pEqn.H`), the gravity term is Lf·(g·Sf). On an axis-aligned Cartesian mesh with diagonal K the exact
face flux is (n·K·n)·snGrad·|Sf| and (K·g)·Sf = (n·K·n)(g·Sf): replacing k0f by the normal component of K is the whole
flux change; `alphaEqn.H` and `pEqn.H` stay as they are.

Where K enters (solver `c3dbf48`, installed `be1a3ab`; checked 2026-10-27) and what changes:
- `createPorousMediaFields.H:3` `volScalarField K` (read from the time folder, AUTO_WRITE), `:16` k0 = K, `:17` k0f =
  interpolate(k0) (linear: `default linear` in the cases). Read the field class: volScalarField → old code untouched
  (bit-identical); volTensorField → k0f = 1/(w/Knn_P + (1 − w)/Knn_N) with Knn = n·K·n of each cell, on internal and
  coupled faces. Free cells K_VOID·I; k0f on free/free faces acts only through the (negligible) drag.
- G's harmonic block (`createPorousMediaFields.H:163–205`, porous/free faces, internal and coupled): same formula
  with the normal components (the general rule above includes it).
- Darcy-face test `Daf = k0f·deltaCoeffs²` (`:221`, boundary factor 0.25): unchanged, now with the normal component
  (Kpar 4.2e-12 at 20 µm: Da 0.011 < `darcyFaceMaxDa` 0.1).
- `updateVariables.H`: face mobilities from k0f (`:41` on) unchanged; `MfLinear` (`:13`), `Dragf = 1/MfLinear`,
  `Drag = average(Dragf)·Solid` (`:49–50`) then average the inverse normal mobilities of the faces: no change needed.
  Cell mobilities M1, M2, M (k0·kr/μ) enter `PcCoeff` (`:64`) only as M1/M (K cancels): any scalar k0 (e.g. tr K/3).
- `updateDarcyVelocities.H` Uwetting/UnonWetting = Solid·M1·(…): (K & (…))·kr/μ. Used by Ur, `correctUBc.H` on
  patches with a fixed Uwetting, and the written fields.
- `UEqn.H:12` `fvm::Sp(Drag, U)` takes a scalar only: acceptable because with G every face of a porous cell is a
  Darcy face, U of Darcy cells is overwritten by reconstruct(φ), and the drag enters only through rAU/HbyA
  interpolated on porous/free faces (F′) and porous cells next to non-Darcy boundary faces. Estimate at the REV dt
  (1.25e-7 s): inertia ρ/(ε·dt) ≈ 1.6e10 vs μ/K ≈ 1e8 (water, 1e-11) and 1.1e9 (Kperp 9.2e-13).
- Guards (fatal errors with a tensor K): off-diagonal components above 1e-6 of the largest diagonal one; a face normal
  not along x, y or z; a porous face that is not a Darcy face (the momentum path would need a tensor drag).
- Libraries: no K (`porousModels`: kr and pc only; `porousInterfaceProperties`: none).
- Output: K is AUTO_WRITE, a tensor K is written at every write (9 components; REV ~10 MB per write, estimate):
  consider NO_WRITE for the tensor.

Outside the solver:
- `meshing_strat_trial/tools/coatsTimeStep` reads `lookupObject<volScalarField>("K")` (lines 46–47): fatal with a
  tensor K. Its capillary sum already uses the solver's `k0f` (then the normal component); the gravity part
  `K[i]·(ρa − ρb)·sumSfg[i]` (line 146) → `surfaceSum(k0f·|Sf·g|)` as in anisoImpesFoam's `CoatsNo.H`. Keep the old
  expression for a scalar K (bit-identical).
- `build_fields.py` sets Kpar/Kperp only through Gebart (`VF_YARN`, `R_FIBRE`): add `--k-par`/`--k-perp` for the REV
  study (a). `ORIENTATION "texgen"` gives off-diagonal terms (rejected by the guard). `Allpre` of `REV/` calls
  `--k-mode scalar --k-scalar 1e-11`.
- `pOpenAir`, `liquidBalance`, `waterBudget`, `stopGuard` and the Python scripts other than `build_fields.py` do not
  read K.

**Harmonic vs linear (decided: harmonic).** Same Knn on both sides (inside a yarn; the 3,221 warp/weft z-contacts of
the REV, Kperp on both sides): same value, except that the harmonic of two equal values can differ from K by an ulp
(apply it only where the two values differ to keep isotropic cases bit-identical). Different Knn: the 1,236 warp/weft
x/y contacts of the REV (Kpar | Kperp; Gebart: harmonic 1.5e-12, linear 2.6e-12); harmonic = resistances in series.
Now: linear on porous/porous faces (uniform K: the same), harmonic on porous/free faces (G). Face counts:
`NOTES_cases.md`, REV geometry.

**Full tensor (off-diagonal, `ORIENTATION "texgen"`, crimp-following): not planned.** OpenFOAM's tensor Laplacian
(`fvm::laplacian(-Mf, p)` in anisoImpesFoam) takes the normal part implicitly and the cross part with interpolated
cell gradients (`fvc::dotInterpolate(SfGammaCorr, fvc::grad(p))`, `gaussLaplacianScheme.C:117`), and anisoImpesFoam's
capillary flux is `interpolate(dpcdS·grad(Sb))` (`updateSbProperties.H:22`): the averaged-gradient stencil A removed.
The cross terms would also be needed consistently in phiWetting, phiNonWetting, phiDarcyExplicit and the p equation
(φ = φW + φNW for B), in the upwinded kr (C) and on G's porous/free faces (harmonic of a full tensor undefined); no
MPFA in OpenFOAM. With "axis" the crimp is a staircase in z whose steps pass z-faces at Kperp (penalty not
quantified, crimp angle not measured). Boubaker et al. 2026 used a diagonal Gebart tensor per tow; their data
availability statement offers data on request, nothing about the code.

Checks after the change (predictions written before the runs):
1. Scalar K file: bit-identical (1D column 0.03 s vs the stored `verification/wicking1D/ABC`; 2D bench 2 ms).
2. Tensor K = 1e-11·I: same as 1 (bit-identical with the harmonic applied only where the values differ).
3. 1D column with a diagonal K, column along x, y and z: front 18.04·√(K_axis/1e-11) mm/√s (the similarity solution
   scales with √K at fixed pc0); the transverse components have no effect.
4. 2D anisotropic spreading (inlet on part of an edge, K_xx ≠ K_yy) vs anisoImpesFoam: with a diagonal K its
   cross-term correction is exactly zero on axis faces (SfGammaCorr = 0), differences only from its interpolated
   capillary stencil; front aspect ratio → √(K_xx/K_yy) at late times.
5. K jump in series (two layers of different Knn along a water-filled column, steady pressure-driven flow,
   capillarity off; to design): flux = Δp/(μ·Σ L_i/K_i), exact with harmonic faces.
6. 2D bench with anisotropic walls (Kpar along the slit, Kperp across): `check.py` passes; split bench parallel =
   serial.

## Open issues

Solver behaviour:
- ~~H wrong on processor boundaries~~ (found and fixed 2026-10-26, `verification/parallel_H/`): `calculateK` sets α of the porous
  cells to the mean α of their free neighbours cell by cell but does not refresh the processor patch values, so a free
  cell next to a porous cell across a processor boundary sees the yarn saturation (H undone on those faces; cyclic
  patches read the internal field and are not affected). 2D bench split on the lower yarn surface, 2 ms: gap meniscus
  0.900 vs 0.790 mm serial (+14 %), max |U| 2.1 vs 1.0 m/s. Fix: `alpha1Smoothed.correctBoundaryConditions()` after the
  loop: parallel = serial within 9e-4 (ordinary parallel difference, split mid-gap: 1.3e-3), serial bit-identical.
  **Fixed by `0f6c6d4` (2026-10-26). Parallel runs with H on `b525086` or older are not valid where yarn surfaces
  lie on processor boundaries.** Same split, with and without the fix: one-time water loss of ~3e-3 cell volumes at the start
  (budget closed afterwards), not followed up.
- Gravity–capillarity equilibrium oscillation with A+B+C (counter-current, zero total flux): cause not isolated.
- I: why the exact coupling (2·μ_air next to wet walls) gives fast air currents (I bounded meanwhile).
- `Free_Flow_Cases/Capillary_Rise/porous_Boundary` tutorial: A and C change the free water by +0.40 / +0.11 % (mechanism
  not identified); not rerun with E, F, G, H–I. **Original vs E on this tutorial = the evidence of what E changes in
  published-type cases** (not done).
- Inlet: `+ 0.001` in the boundary relative flux (0.23 % deficit at a fixed-velocity inlet). The old reservoir inlet
  lets air through (1 % air on inflow, air vent at air-filled free inlet cells, water short circuit through the yarn
  inlet faces): **J** (opt-in) makes it water-only. With J: a drained free reservoir face does not refill (no meniscus
  on a boundary face); the 1D hybrid stays ~1.2 % below impesFoam in uptake (cause not isolated).
- Porous boundary faces (measured 2026-10-27, `verification/standardOpenBC`): the mixture-pressure two-point flux of
  `alphaEqn.H`/`pEqn.H` equals the water-pressure flux plus (α_b − α_c)(pc_b − pc_c) (discrete chain rule with face
  values = boundary values). At the bath the yarn faces sit almost in equilibrium (net drive 7–16 Pa REV, 25–30 Pa
  bench), so this term (0–80 Pa, depending on α_b and the first cell) moves the yarn-face inflow by 10–20 %; local,
  no measurable effect on fronts, saturation or uptake. Not changed.
- Not tested: non-uniform meshes (G, H, I), cyclic porous/free faces with H/F′/I (none in the REV), 3D processor faces
  (planar 2D test only, 2026-10-26), 3D edges/corners and staircased surfaces, `momentumPredictor` on, harmonic K set at
  start-up only (no dynamic meshes). Runs > 5 ms: the 2D bench to 20 ms is stable (2026-10-15, `NOTES_cases.md`).
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
  original vs E. **Planned in detail in `verification/PLAN.md`** (Studies 1, 2a, 2b, 3).
- Thesis: say the interface model changed (supervisor to be informed); cite Mosthaf et al. 2011.
