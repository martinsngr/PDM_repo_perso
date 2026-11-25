# Yarn parametrization: pc(S), K and kr from the yarn geometry

pc(S), K and kr of the yarn continuum computed from measurable inputs (fibre diameter, fibre volume fraction, contact angle,
surface tension), after Maier et al. 2025 (pore morphology with PoreSpy, Gebart, Mualem). Started 2026-11-20. Companion files:
`NOTES_experimental.md` (what the model needs from the tests), `NOTES_cases.md` (plan of the fabric-scale 1D model),
`NOTES_solver.md` (open issue: kr/pc models outside the solver). Facts from the papers and the code are kept apart from
estimates and assessments (marked as such).

## Status (2026-11-20)
- **User: no rush.** First read the PoreSpy documentation and understand what it does, then apply it to our yarn.
- **2026-11-23 (user): replicate Maier's pore-morphology pc(S) with PoreSpy and apply it to our yarn, discovering the tool and
  building it together.** PoreSpy 3.3.0 installed (`~/venvs/porespy`, PoreSpy section below), the open checks answered (curvature
  factor, local thickness, steps). Steps proposed: periodic fibre packing (dense one for V_f 0.5) → reproduce Maier f128 PEG (α
  0.000605, n 4.48, their Fig. 22) with fibres-per-sample and pixels-per-fibre convergence → our yarn (15 µm, V_f 0.5, water at
  θ 70–80°) → pc0, m against the setup values 5000 Pa / 0.5. **The user writes the code** (guided, small pieces); folder
  `parametrization/poreMorphology/` (first file: `check_slit.py`).
- **State at the end of 2026-11-23:**
  - `packing.py` (user): `place_fibres(n, radius, vf, seed, max_trials)` random sequential placement, periodic (minimum image);
    `relax_fibres(n, radius, vf, seed, max_iter, tol)` random start + pairwise push-apart sweeps, for dense packings (code given by
    Claude, tested: vf 0.7 with 32 fibres in 57–174 sweeps, 100 fibres in 241–359; leaves many touching pairs, ~1.1 contacts
    per fibre at vf 0.7, also 5–9 pairs at vf 0.16 where random placement has almost none); `fibre_image(centers, L, radius,
    px_per_radius)` → `h, im` (pixel centres at (m + 0.5)·h, h = L/N with N whole, fibres stamped with the minimum image, `True`
    = pore). All return `centers` as an (n, 2) array; lengths in µm. Random sequential placement jams at vf 0.525 with 32 fibres
    (24 of 32 placed, 200,000 tries; 2D limit 0.547): vf above ~0.5 needs `relax_fibres`.
  - Checks passed: no overlaps (smallest gap/2R ≥ 1 − 1e-6); porosity of the image 0.70007 at vf 0.3, 20 px per radius
    (0.70062 at 10, 0.70005 at 40); `np.tile(im, (3, 3))` identical to the same packing drawn directly in a 3L box (0 of 1.2
    million pixels differ): exactly periodic. PoreSpy's own drawing (`spheres_from_coords`, `insert_sphere`) rounds centres and
    radii to whole pixels and is not periodic, so the drawing stays in numpy.
  - `plot_packing.py` (user): circles with their 8 copies, view −L to 2L, dotted joins, the REV in red (`packing_3x3.png`).
  - `pore_morphology.py`: `pc_curve(im, h, sigma, theta_w)`, step 1 (written by Claude at the user's request, then rewritten by the user) (3×3 padding with
    `np.tile`, `capillary_transform` with `theta = 180 − theta_w`, `voxel_size = h·1e-6`, `spacing=np.inf`), returns the pressure
    map for now. Test (n 32, R 27.5 µm, vf 0.3, seed 42, 20 px per radius, water σ 0.072, θ 70° placeholder): pore pixels of the
    central copy 428.6 Pa (largest pore, 57.5 µm) to 17,904 Pa (= σcosθ/h).
  - Values in use: R 27.5 µm and target vf 0.7 (porosity 0.3, Fischer's values, user); tests at vf 0.3 with `place_fibres`. θ of
    water on the fibres still a placeholder.
  - **Next (as of 2026-11-23; steps 2–4 and the resolution check done 2026-11-24, below):** step 2 `ps.simulations.imbibition(im=padded, pc=pc, steps=<explicit list going below min pc>)` (no `inlets`/`outlets`:
    fibres parallel, water and air move along them, discussed with the user); step 3 crop the central copy of `im_pc`; step 4
    `ps.metrics.pc_map_to_pc_curve(..., mode='imbibition')`, S = 1 − snwp, plot. Then: 3×3 against the 2×2 window (Maier; expected
    equal, margin L/2 = 252 µm > ~2 × the largest pore radius); `relax_fibres` at vf 0.7; Maier f128 with `place_fibres`;
    resolution and fibres-per-REV convergence; ensemble + Van Genuchten fit; then the hexagonal lattice at the same vf and R
    (user, to compare with the random packing). Test outputs (`*.png`, `test.py`) in the folder are not for commits.
- **2026-11-24:**
  - `pore_morphology.py` (user): `pc_curve` now runs the imbibition (100 pressures, `np.geomspace` from 1.1 × the largest to
    0.9 × the smallest pc of the padded map) and returns PoreSpy's results; `rev_curve(centers, L, radius, px_per_radius,
    sigma, theta_w)` → `S, pc, im, res` (image → imbibition → central copy of `im_pc` → `pc_map_to_pc_curve(...,
    mode='imbibition')`, S = 1 − snwp; `res` returned on the user's proposal, for `plot_results`; an ensemble loop must not keep
    it, ~70 MB per f128 REV); `plot_results` (PoreSpy's three panels on the central copy), `plot_curve` (pc on a log scale against
    S). Test (n 32, R 27.5 µm, vf 0.3, seed 42, 20 px per radius, σ 0.072, θ 70°): 62 points, 17,346 Pa (S 0) to 418.6 Pa
    (S 1); S 0.035 / 0.147 / 0.526 / 0.884 at 2,000 / 1,000 / 600 / 450 Pa; every pore pixel filled. `im_seq` counts the
    distinct filling pressures (61), not the 100 steps (PoreSpy renumbers). The padded map's smallest pc is 331.6 Pa against
    428.6 Pa in the central copy: the outer border of the 3×3 sees the image edge as open (`get_edt`); only the central copy is
    used.
  - Figures go to `poreMorphology/figures/` (`FIG_DIR = Path(__file__).parent / "figures"` in each script), kept out of git for
    now (user; root `.gitignore`).
  - **Resolution check, `check_resolution.py` (user), one Maier f128 REV** (R 5.85 µm, vf 0.16, 25 fibres, seed 42, PEG σ
    0.0412 N/m, θ 36°; L 129.6 µm, 36 tries), same centres at 10 / 20 / 40 px per radius (N 222 / 443 / 886, h 0.584 / 0.293 /
    0.146 µm): porosity 0.83999 / 0.84004 / 0.84001; 57 / 64 / 68 points; pc at S 0.1 / 0.5 / 0.9: 3,484 / 2,111 / 1,681,
    3,488 / 2,091 / 1,657, 3,461 / 2,114 / 1,681 Pa, within 1.4 % of 40 px/R from S 0.05 to 1, below the ~4 % spacing of the
    pressure steps (100 steps over a factor 34–61). pc at S = 0 not converged (55 / 77 / 97 kPa): the narrowest gap between two
    fibres, 0.75 µm in this packing (2σcosθ/g = 89 kPa), carries no saturation. 46 s for the three, ~3.3 s per REV at 20 px/R.
    **20 px/R for the f128 ensemble; to redo at vf 0.7** (narrower pores relative to R).
  - Scaling (exact at fixed px per radius: the image does not depend on R, only h ∝ R): pc ∝ σcosθ/R, so the Van Genuchten n
    depends on vf and the packing only, α ∝ R/(σcosθ). One ensemble at vf 0.7 serves any θ. Maier's own f256 PEG and EG fits
    (σcosθ 1.2 % apart) differ by 4.5 % in α: their ensemble scatter, the tolerance for the f128 comparison.
  - **Idea (user): start the yarns at S 0.01 instead of 0.002** (as Maier's 1D model). Assessment, not tested: the moisture
    argument does not hold for PET (regain ~0.4 % by mass, absorbed in the polymer; at 65 % RH the Kelvin suction is 58 MPa,
    water menisci only in ~1 nm pores: the pores of a yarn in air are dry), so state it as a model choice (the curve below S_init
    is not used). The extreme dry-end pc comes mostly from the placeholder m 0.5: VG 5000 / 0.5 gives 2.5 MPa at S 0.002, 0.5 MPa
    at 0.01; Maier's f128 fit (1653 Pa, m 0.777) 9.9 / 6.2 kPa; the f128 PoreSpy REV 20–23 / 11 kPa. Open: effect on the front
    (`verification/maier1D/richards1D.py`, 0.002 against 0.01), whether 0.5 MPa still triggers study 2f's dry-start failure; a
    set-up change of the REV cases (`initFields.py`), to decide once the computed curve exists.
  - **Ensemble and fit (2026-11-24):** `ensemble.py` (user): one `results/<config_name>/rev_<seed>.npz` per REV (S, pc, porosity,
    L and the seven inputs), seed = REV number, skips existing files (resumable); `results/` out of git (user). f128 run stopped by
    the user at 258 REVs (~3.5 s each). Maier's fit (their text, p. 945): `curve_fit` of eq. 9 "in logarithmic space" and data
    "sampled with pandas" for a balanced saturation range. Replica (Claude, scratch): S = 0 and S = 1 points removed (log pc
    infinite), 10 equal S bins, the same number of raw points drawn from each (the sparsest bin's count), `curve_fit` of log10 pc
    against S, 10 draws. Raw points are very uneven (67 % at S < 0.1; none above S ≈ 0.92: each REV jumps from S 0.84–0.86,
    median, to S = 1 in its last step, when its largest inscribed disc, ~11 % of the pore area, disappears), so the Van Genuchten
    wet end (S > 0.9) is an extrapolation of the fit, in Maier's work too; fit variants on the same data give pc0 1,720–2,040 Pa,
    n 3.5–4.7 (raw points in log pc / in S, interpolated grid): the balancing matters.
  - **Replica against Table 4:** f256 PEG (R 4.25 µm, φ 0.86, 40 REVs): pc0 2,471 ± 73 Pa against 2,457, n 4.03 ± 0.37 against
    4.32; data within 2–5 % of their curve at S 0.1–0.7 (+14 % at 0.9, the extrapolated end): **the method reproduces f256, the
    material whose data they show (Fig. 11).** f128 PEG at Table 1's φ 0.84 (258 REVs): pc0 1,999 ± 16, n 3.97 ± 0.11 against
    1,653 / 4.48; data 15–33 % above their curve (S 0.1–0.9).
  - **Inconsistencies in Maier et al. 2025 (checked 2026-11-24 with the PDF):** (1) Table 4's f128 values (α 0.000605, n 4.48)
    equal the converged values of their REV-size study (Fig. 15: α ≈ 0.0006, n ≈ 4.45 at 25–40 fibres), which was run at φ 0.856
    and d 11.7 µm, not at Table 1's 0.84 (Table 4's footnote says Table 1). Test: f128 at φ 0.856 (80 REVs) gives pc0 1,839 ± 43,
    n 4.11 ± 0.36, data at S 0.5 +5 % above their curve: closes about half of the pc0 gap (+21 % → +11 %). (2) f256: the fineness
    (180 dtex, 256 filaments, ρ 1380) gives d 8.05 µm, Table 1 says 8.5 (f48 18.6 and f128 11.7 check exactly); their porosity
    footnote gives 0.836 with 8.5 µm, 0.852 with 8.05 µm, Table 1 says 0.86 (f48: 0.852 against 0.86). Our f256 match with
    8.5 µm / 0.86 suggests those were the pore-morphology inputs. (3) The footnote formula φ = 1 − n_y·n_f·R_f²/d_cap² is exact
    only with R_f = the diameter (also in eq. 11, Gebart: K 4× if the diameter went in; known). (4) θ PEG: Table 2 36°, Fig. 2
    34° (cos ratio 1.025). Remaining f128 gap and our n 7–11 % below theirs in every case (f128 and f256): fit details the text
    does not give (bins, points per bin, the S = 1 points), pc0 and n trade off in the fit. Data and code: "on reasonable request"
    from the corresponding author. The `verification/maier1D` replica used Table 4 as published: not affected.
  - **Reference shared by the user (2026-11-24): Fibers 13 (2025) 48, hierarchical pore model of single-jersey knits** (DFG
    453311482; authors given by initials in the text, L.M. among them, probably Maier's group). The same PET twist-texturized
    yarns, 186 dtex, f48 / f128 / f256 and a twisted f128Z (200 TPM): resin-embedded at 0.5 cN, ground, microscope cross-sections
    (their Fig. 2), fibre centres by OpenCV, fibre diameter from the smallest of 10 fibre areas (flattened filaments), yarn radius
    from the fibre positions; PoreSpy local thickness on 20 sections per yarn (Fig. 4, Table 3); fabrics by CT at 3.5 µm. Their
    yarn-pore model (Gebart hydraulic radius r = φ/(1 − φ)·r_F with a log-normal spread) deviates 3–63 % from the measured medians.
    **For us:** a pixel histogram of local thickness is the pore-morphology curve without access limit (S(pc) = share of pore
    pixels with local thickness < σcosθ/pc), so their measured histograms are pc–S curves of the real cross-sections of Maier's
    yarns: the test of the random packing that Maier's paper lacks. Tables 2–3 not in the pasted text (asked): their measured
    f256 diameter may be Maier's 8.5 µm (fineness 8.05). Route for our yarn: a cross-section from the woven fabric, fibre centres
    into `rev_curve` (a non-periodic window: a real section has a yarn boundary). Caveats: the text swaps intra/inter-yarn in
    several places; eq. 11 calls r_F a diameter (as Maier's eq. 11); single free yarns, porosity of the free yarn, not Maier's
    bundles in the capillary. Data on request. **For the solver (discussed 2026-11-24): no change** (frozen; their dual scale is a
    static pore-size model, ours resolves the gaps and treats the yarn as a continuum). Two limits it makes concrete: the yarn's
    pc(S) is defined over a window of ~25 fibres (66 µm at 15 µm fibres and V_f 0.5, 130 µm for f128), while a REV yarn is ~120
    µm thick on 20 µm cells: one to two such windows across the thickness, so the continuum is at its limit across a yarn (fine
    along it); their loose texturized yarns have intra-yarn pore medians of 39–126 µm diameter, near the REV's narrow gaps (p10
    ~120 µm), so the separation of scales depends on how compressed the yarn is in the fabric (to read from the cross-section).
    Their yarns are more compact at the crossings (Fig. 7): V_f varying along the yarn would enter as K per cell (`0/K`, already
    possible); pc per cell not checked in the library or `coatsTimeStep`.
  - **State at the end of 2026-11-24:** ensembles of 500 REVs, PEG, 20 px/R, seeds 0–499, run by Claude in the
    background with the logic of `ensemble.py`, both complete (500 files each, ~35 min each): `results/f256_px20/` (R 4.25 µm,
    vf 0.14) and `results/f128_phi0856_px20/` (R 5.85 µm, vf 0.144); `results/f128_px20/` (user, vf 0.16) 258 REVs. Fit script
    `fit_vg.py` (user) not started: stages D1–D4 (load, check that all files share the inputs, grey cloud of curves), then
    Maier's fit (S = 0 and 1 removed, equal S bins, the same number of raw points drawn per bin, `curve_fit` of log10 pc against
    S, several draws; bins, points per bin and S = 1 handling as inputs), then the one-fit-for-both test (f256 at 0.86 and f128 at
    0.856 against Table 4 with one fit setting). Email to the authors drafted with the user (not sent, the user decides): (1)
    eq. 8 printed without the ∂ on k_rel, which form their code uses (with dk_rel/dS their curves need gravity ~3× weaker than
    Tables 2 and 4 give; with k_rel as printed Figs. 17–19 fit with K within ~20 % of eq. 11, per material); (2) the inputs of
    Table 4 and Figs. 16–19 (K from eq. 11 with Table 1, R_f radius or diameter; f128 Table 4 = Fig. 15 at φ 0.856; f256 8.05
    against 8.5 µm); request for the scripts or data, and the fibre positions or local-thickness histograms of the Fibers 2025
    cross-sections. Supervisor to be told first.
  - **Next (to decide with the user):** f256 PEG as the validation case of the tool (a full ensemble with `ensemble.py`), f128
    recorded as an input discrepancy of the paper; then the fit script (user), then our yarn at vf 0.7.
- **2026-11-25 (start here next session): `fit_vg.py` (user), stages D and E written and checked on `results/f256_px20/`.**
  - Functions: `load_files` (checks that radius, vf, n, sigma, theta_w, px_per_radius are the same in every file, `raise`
    otherwise; 500 files, 33,421 points), `plot_clouds` (grey line per REV, `figures/ensemble_<config>.png`), `vg_log_pc(S, pc0, n)`
    (log10 of pc = pc0·(S^(−1/m) − 1)^(1/n), m = 1 − 1/n: the solver's `pcVanGenuchten` form, checked against Table 4's f256
    curve), `make_table` (pandas table, S = 0 and S = 1 rows removed: 32,421 points, S quartiles 0.004 / 0.021 / 0.164, max
    0.930), `balanced_sample(df, n_bins, seed)` (`pd.cut` into equal S bins, `groupby(observed=True).sample(n=k)` with k the
    smallest bin count: 10 bins give k 54, limited by the 0.9–1 bin, 540 points), `fit_vg` (`curve_fit`, p0 (2000, 4), bounds pc0
    100–1e5 Pa, n 1.01–20).
  - S = Se here: the imbibition starts with every pore pixel air and ends with every pixel water (no inlets, no trapping), so
    S_r = 0 and S_max = 1. In the solver Se = (S − `alpha.wettingminpc`)/(`maxpc` − `minpc`): 0 / 1 to use the fit as it is (REV
    cases 0.999, 0.1 %); with measured trapped air, `maxpc` = S_max (open point on pc and kr, `NOTES_cases.md`). No S_r fit
    parameter (the data have no residual by construction).
  - **Result, f256, 10 bins:** pc0 2,472 Pa, n 3.97 (seed 42; seed 0: 2,475 / 3.95) against Table 4's 2,457 / 4.32: pc0 +0.6 %, n
    −8 %; pc against Table 4's curve +9 / +5 / +2.5 / +0.4 / −2.6 % at S 0.1 / 0.3 / 0.5 / 0.7 / 0.9. **n depends on the fit
    choices the paper does not give** (20 seeds each, measured with the user's functions): 5 / 10 / 20 / 50 bins n 3.75 / 3.98 /
    4.05 / 4.41 ± 0.18 (pc0 2,365–2,466); points below S 0.01 dropped 4.67 (pc0 2,534); fit to the median curve of the 500 REVs
    4.50 (2,451); all points without balanced sampling 3.52 (2,078). So n is fixed only within ±10 % by the method as described,
    Table 4's 4.32 inside that range; pc0 robust (2,370–2,530 Pa for every balanced setting): the replica's validation rests on
    pc0. Forcing pc = 0 at S = 1 changes nothing (VG has it for every pc0, n); the data reach S = 1 at a finite pc (the largest
    pore, 1.3–2 kPa), which VG cannot follow, hence the S = 1 points are dropped. To look at: the fit gives 2,750 Pa at S 0.5,
    the REV median 2,556 Pa (shape of VG or pull of the dry points).
  - **Next:** `plot_clouds` extended (user's choice) with optional `sample` (the sampled points) and `fits` (list of (label, pc0,
    n), curves from `10**vg_log_pc` on S 0.001–0.999, legend, saved as `fit_<config>.png`), with our fit and Table 4's; then
    stage F (many seeds, spread of pc0 and n, bin count as an input), the same on `f128_phi0856_px20` (one setting for both
    against Table 4), then our yarn at vf 0.7.
- **Route (discussed 2026-11-20):** pc(S) from pore morphology at the yarn's fibre fraction and diameter, K from Gebart (already in
  `build_fields.py`), kr Mualem (the same Van Genuchten m), checked against a yarn test with water before use. It fits the aim of a
  blind first prediction from measured inputs (`NOTES_cases.md`, plan item 7).

## Why the solver stays (discussion 2026-11-20)
- **The yarn equations are Richards plus an air phase.** In porous cells the solver solves two-phase Darcy (IMPES: p implicit, α
  explicit). `p` = p_air − α·pc; `phiWetting` = M1f·(−∇p_water + ρ_w·g)·Sf and `phiNonWetting` = M2f·(−∇p_air + ρ_a·g)·Sf
  (`alphaEqn.H`); their sum is the total flux of the Darcy faces (`pEqn.H`: `rAUfD = Mf`, `phiDarcyExplicit`); α is moved by the
  water flux. Richards (Maier eq. 4–6) is the limit ∇p_air = 0 (μ_air → 0): the same water flux, no air equation.
- **Already compared with Richards:** `verification/analyseWicking1D.py` solves ε·∂S/∂t = ∂x(D(S)·∂xS), D = K·kr_w·|dpc/dS|/μ_w
  (Maier eq. 6 without gravity). Hybrid (ABC): front −1.6 %, uptake −4.6 % = ~2 % air let in by the old inlet + ~2.5 % air
  back-pressure + ≤ 0.3 % numerics; with μ_air ÷ 100 within 0.3 % (`NOTES_solver.md`, Verification). The air matters more for
  water (μ_w/μ_air = 57) than for Maier's liquids (EG 900, PEG 5,300).
- **Free cells solve interFoam's equations:** ε = 1 and `Drag = fvc::average(Dragf)*Solid` = 0 there (`updateVariables.H:86`);
  real-wall slit: this solver = stock interFoam to 0.001 mm.
- **Set aside (Claude's assessment, nothing tried):**
  - Richards in the yarns inside the solver: a new pressure formulation (yarn rows parabolic and nonlinear, Picard/Newton in mixed
    form, α of yarn cells from p_water), B, C, F, F′, G (air part), J, L and `coatsTimeStep` rewritten, verification redone. Gain:
    dt ≤ ×12 at K 1e-11 (Coats 1.25e-7 s in job 3051, against the gaps' capillary-wave limit 1.5e-6 s), ×2–3 with the Gebart K
    (`tensorB` 5.4–6.5e-7 s), ×1 in the horizontal runs (already 1.49e-6 s); no air across yarn/gap faces (no air pump, no crest
    venting) but no trapped air either; the yarn uptake moves by a few %. Months of work, after the freeze.
  - interFoam in the gaps + Richards yarns as two mesh regions: the exchange becomes boundary conditions that switch with the gap
    cell's α (water: pressure continuity and Darcy flux; air: seepage face; partly filled: a meniscus on a permeable wall) plus a
    coupling loop between the regions. The current solver does this in one pressure matrix, C's upwinded kr switching smoothly
    with α; partly filled cells stay the hard case either way; OF9 has no two-phase multi-region solver to start from.
- **Explicit Richards gains nothing:** stable for dt ≲ ε·Δx²/D, which is the Coats capillary limit with λ_air → ∞, and stricter
  near saturation (Van Genuchten |dpc/dS| → ∞, while the two-phase factor λ_a·λ_w/(λ_a + λ_w) is held down by the air mobility).
  Richards solvers are implicit (Maier: LSODA/BDF; `groundwaterFoam`: Picard + Newton). Several saturation steps per pressure solve
  (multirate, "improved IMPES") would need a solver change: `nAlphaSubCycles` exists, but kr and pc are refreshed only after the α
  loop (`updateVariables.H` comes after `alphaEqnSubCycle.H`, `hybridPorousInterFoam.C:142–146`) and the Coats limit applies to the
  whole step.
- **Assessment (Claude, 2026-11-20): keep the frozen solver.** The yarn part is checked against Richards, the gaps are interFoam,
  the gaps carry a large share of the uptake (horizB: 56–67 % of the through-thickness uptake at 10 ms; N2 runs: 17–20 % of the
  fabric water at 30 ms), and any alternative needs the same yarn/gap coupling. Not settled by that: the coupling is only checked
  for plausibility; known artefacts (air pump at low pc; face-to-face sign flips of the exchange next to water-filled gaps, −2 to
  −8 % of the net yarn uptake; θ fixed on wet yarn surfaces; bath leak 5.7 % of the inflow by 30 ms); mesh at 15 µm not run. Use
  the REV mainly for relative results; put the effort into the inputs (this file) and the validation tests.

## Reference: Maier et al. 2025 (shared by the user 2026-11-20)
Maier, Pauly, Gostick, Gresser, Nieken, "Spontaneous imbibition in thin anisotropic fibrous media: Experiments and numerical
modeling", Textile Research Journal 95(9–10), 937–955 (online 2024), DOI 10.1177/00405175241268794. Code not published (data
available on request from the corresponding author, L. Maier, Stuttgart; nothing found on GitHub or Zenodo, 2026-11-20). Gostick
(PoreSpy's lead developer) is a co-author.
- **Samples:** three PET drawn textured yarns of 180–190 dtex: f48 (filament diameter 18.6 µm), f128 (11.7 µm), f256 (8.5 µm);
  diameters from the fineness, assuming round filaments and ρ 1380 kg/m³. 20 yarns drawn into a glass capillary of 1.5 mm inner
  diameter, silanised so that the glass does not wet: porosity 0.86 / 0.84 / 0.86 (loose bundles; our yarns in the fabric ~0.5).
  20 yarns for scale separation: single yarns wick by pore-filling jumps (Fischer et al., Parada).
- **Liquids:** PEG 400 (μ 0.0948 Pa·s, ρ 1120 kg/m³, σ 0.0412 N/m, θ 36 ± 3°) and ethylene glycol (0.01661 Pa·s, 1140 kg/m³,
  0.0434 N/m, θ 39 ± 3°), chosen partly for their low vapour pressure (no evaporation over cm heights); θ from droplets on single
  filaments (light microscope); blue dye for contrast.
- **Measurement:** backlight imaging (camera, LED panel, yellow foil), one image every 5 s, runs of 600–3000 s; grey value → S
  linear between the dry image and the first square of the last image (assumed S = 1), on 1.5 mm squares; a logarithmic
  (Lambert–Beer) scaling changes little. 4 experiments per material, 2 samples per run. Fronts of several cm (their figures).
- **Model:** 1D Richards in diffusion form (their eq. 6–8), air at 0 Pa, gravity kept, no dynamic capillary pressure; Van
  Genuchten pc (eq. 9), Mualem kr (eq. 10), Gebart K along the fibres (eq. 11, c = 57, called hexagonal in their text: see "To check" below). Domain 0.15 m, Δx 0.5 mm (grid
  study), finite volumes with linear face interpolation, `scipy.integrate.solve_ivp` (LSODA); S(0) = 0.99, S(0.15 m) = 0.01,
  initial S 0.01.
- **Pore morphology:** parallel fibres, so 2D: non-overlapping circles placed at random in a square sized by the porosity, the
  diameter and the fibre count; distance transform → local thickness; at each pressure step, discs of radius r = σcosθ/pc
  (their eq. 12) are placed wherever they fit (air), the rest counts as wetting liquid; no connectivity to the reservoir (wetting
  films assumed to reach everywhere); θ only through cosθ (Schulz et al.). Periodic: 3×3 copies, a 2×2 window for the local
  thickness, the centre REV cut out. 25 fibres per REV (R² and the parameters converge from 20; fewer fibres give jumps at high
  S); 500 (methods section) or 1000 (results section) REVs per material; Van Genuchten fitted to all points with `curve_fit` in
  log space, resampled to balance the saturation range. Implemented with PoreSpy.
- **Fitted Van Genuchten (their Table 4) and the solver's keywords:**

  | | f48 PEG | f128 PEG | f256 PEG | f256 EG |
  |---|---|---|---|---|
  | α (1/Pa) | 0.00123 | 0.000605 | 0.000407 | 0.000385 |
  | n | 4.41 | 4.48 | 4.32 | 4.33 |
  | pc0 = 1/α (Pa) | 813 | 1,653 | 2,457 | 2,597 |
  | m = 1 − 1/n | 0.773 | 0.777 | 0.769 | 0.769 |

- **Validation (their Figs. 16–19):** f128 (PEG) and f256 (PEG, EG) predicted well. f48: the experiment slows down earlier (pc
  overestimated; the filaments are flattened to a near-hexagonal section by texturing, a larger area-to-perimeter ratio). In all
  cases the early rise is too fast (no dynamic contact angle in the model); f256: the experiment is more diffuse at low S late.
  Smaller filaments wick slower but higher (higher pc, more viscous resistance).
- **Same laws as the solver library:** `pcVanGenuchten.H:109` pc = pc0·(Se^(−1/m) − 1)^(1/n) with n = 1/(1 − m)
  (`pcVanGenuchten.C:96`) is their eq. 9 with pc0 = 1/α; `krVanGenuchten.H:132` krb = Se^0.5·(1 − (1 − Se^(1/m))^m)² is their
  eq. 10 (air kr at line 131; the kr m is read separately, in `krVanGenuchtenCoeffs`). Their parameters go in by keywords. Mualem
  kr needs `tools/coatsTimeStep` adapted first (it assumes Brooks–Corey kr; a case tool, not the frozen binary; check the dt after
  the change).
- **To check before reusing their numbers:** R_f is called "filament diameter" in eq. 11 and Table 1, and the porosity footnote
  gives 0.84 only with the diameter; Gebart's formula takes the radius. If the diameter went into eq. 11, their K is 4× Gebart's
  (front ×2); this cannot be settled from the paper. Their text gives c = 57 for a hexagonal and 53 for a square lattice and
  uses 57; in Gebart (1992) 57 is the quadratic constant and 53 the hexagonal one (as in `build_fields.py`, `gebart()`; checked
  2026-11-20 against a secondary source). So with 57 they used the square-packing K: 53/57 = 0.93 × the hexagonal K (front −3.6 %),
  small next to the R_f question. Their pore-morphology packings are random, neither lattice. Their bundles are loose (ε 0.85) and their liquids wet strongly: water on
  PET (θ 70–80°, a guess) at ε ~0.5 needs its own computation. K only along the fibres (Kperp: Gebart's transverse formula, as in
  `build_fields.py`).
- **Cross-check (Claude's arithmetic, 2026-11-20):** the fibre-bundle estimate (4/d_f)·V_f/(1 − V_f)·σcosθ (Ahn, Seferis & Berg
  1991; `NOTES_cases.md`) gives 1,166 / 2,169 / 2,552 / 2,584 Pa for the four cases, i.e. 1.43 / 1.31 / 1.04 / 1.00 × their pc0.
  pc0 sets the scale only: pc(Se 0.5) = 1.09·pc0 at m 0.77 against 1.73·pc0 at m 0.5 (our setup value): their curves are flatter
  in the middle and steeper at both ends.

## PoreSpy (documentation of v3.3.0 read on 2026-11-20 through a web fetch; nothing run)
- **Version:** 3.3.0, released 8 Nov 2026, needs Python ≥ 3.11 and < 3.16 (PyPI). The repo `.venv` and the system have Python
  3.10.12, where pip offers PoreSpy up to 3.0.2 (`pip index versions porespy`, 2026-11-20); Ubuntu 22.04 has python3.11 only as
  3.11.0~rc1 and no 3.12.
- **Environment (2026-11-23, decided with the user):** Python 3.12.16 from the deadsnakes PPA (`/usr/bin/python3.12`, installed
  by the user with apt), venv `~/venvs/porespy` outside the repo (`/usr/bin/python3.12 -m venv ~/venvs/porespy`, then `pip install
  porespy matplotlib ipykernel`): porespy 3.3.0, numpy 2.5.5, scipy 1.18.1, scikit-image 0.26.0, edt 3.0.0, matplotlib 3.11.2.
  Separate from the meshing `.venv` (numpy 2.2.6, scipy 1.15.3, trimesh 5.1.0, embreex).
- **Documented workflow (reference pages and tutorials; calls as written there):**
  - `ps.filters.capillary_transform(im, dt=None, sigma=1.0, theta=180, g=0.0, rho_wp=0.0, rho_nwp=0.0, voxel_size=1.0,
    spacing=None)`: a pc map from the distance transform ("Washburn equation"). `theta` is the contact angle measured through the
    non-wetting phase, between 90° and 180°: water at θ_w on PET → `theta = 180 − θ_w`. `voxel_size` in m per voxel side;
    `spacing` for 2D images only. The formula itself is not printed on the page.
  - `ps.simulations.imbibition(im=im, pc=pc, inlets=..., outlets=..., residual=..., steps=...)`: without `inlets`, no access limit
    (the wetting phase enters wherever it is favourable: Maier's assumption); `outlets` → trapping (trapped air −1 in the sequence
    and saturation maps, −inf in the pc map); `residual` = phase already in place. `ps.simulations.drainage(im=im, pc=pc,
    inlets=inlets, steps=10)` (default inlets: all faces). Results carry `im_seq`, `im_snwp`, `im_pc`.
  - `ps.metrics.pc_map_to_pc_curve(im=im, pc=res.im_pc, mode='imbibition')` → `.pc` and `.snwp` (water saturation S = 1 − snwp).
  - 2D images work ("2D for visualization purposes, but everything discussed here applies to 3D as well"). Generators used in the
    tutorials: `random_spheres`, `blobs`; nothing for a fibre packing at V_f 0.5.
- **Checked in the 3.3.0 source and on a slit (2026-11-23; `parametrization/poreMorphology/check_slit.py`):**
  - Curvature factor: `capillary_transform` on a 2D image with `spacing=None` (the default) uses pc = −2σcos(theta)/r (sphere),
    **2× too high for parallel fibres**; `spacing=np.inf` gives −σcos(theta)·(1/r + 2/spacing) = σcosθ_w/r (Maier eq. 12).
    `imbibition(pc=None)` also defaults to 2/dt. r = edt (distance from the pore pixel centre to the nearest solid pixel centre)
    × `voxel_size`. `theta` = 180° − θ_w (water at 70° → 110), pc > 0.
  - `imbibition` without `inlets`: at each pressure P (descending) every pore pixel c with pc(c) ≤ P (dt(c) ≥ r(P)) gets a disc of
    radius dt(c); the union of those discs is air, the rest water. That union is {local thickness ≥ r}, the opening with discs of
    radius r: Maier's method, no access limit, so no hysteresis (drainage without inlets gives the same curve). `im_pc` = pressure
    at which each pixel turns wet; `pc_map_to_pc_curve` → `.pc`, `.snwp`.
  - `steps=None` takes the unique pc values of the map down to its minimum, where the largest discs still fit: the image never
    fills and `pc_map_to_pc_curve` fails (IndexError). Pass an explicit pressure list that goes below the minimum.
  - Slit of w pixels (expected pc = 2σcosθ/w, σ 0.072, θ_w 70°, 0.5 µm pixels): `spacing=np.inf` 0.999 × expected for w 10 / 20 /
    40, 0.916 for w 11, 0.954 for w 21 (edt overestimates the radius by half a pixel for odd widths); `spacing=None` 1.996 / 1.83 /
    1.91. Pixels per pore radius need a convergence check.
  - `local_thickness` (filters) rounds radii to integers (`sizes`), `imbibition` keeps the float dt: compare them on a packing.
  - Generators: `random_spheres` is random sequential placement in pixel units, not periodic; a periodic fibre packing (Maier's
    3×3 tiling) is to write.

## What a script for our yarn needs (not written)
- A dense packing at V_f ≈ 0.5 with periodic boundaries (Maier's tiling). Random sequential placement saturates near that fraction
  in 2D (Maier worked at 0.15), so a packing that compresses or relaxes the fibres is needed; the packing shapes the pore sizes:
  compare two packings.
- An ensemble of REVs, the Van Genuchten fit in log space, the conversion to keywords (pc0 = 1/α, m = 1 − 1/n).
- Convergence on fibres per REV and pixels per fibre diameter, mainly for S ≥ 0.9: that end decides the gap–yarn exchange in the
  REV (gap suction 0.2–0.7 kPa) and is where pore morphology has the fewest pores (Maier's jumps at high S).
- Inputs to pin down first: θ of water on PET (cos 70° / cos 80° = 2.0); V_f of the yarn inside the fabric (Gebart K ×1.66 between
  ε 0.50 and 0.45, the bundle-estimate pc ×1.22); fibre diameter and cross-section shape (Maier's f48).
- Limits to state: quasi-static (no hysteresis, no dynamic contact angle); straight parallel fibres (no twist, texture, crimp);
  the Van Genuchten fit still diverges at S → 0 (the dry-end problem of study 2f).
- Validation of the computed curve: a yarn-bundle wicking test with water (Maier's set-up; check evaporation over the test time),
  the weighing for S_max (`NOTES_experimental.md`), liquid porosimetry for the wet end if a lab has it (Miller & Tyomkin 1994,
  from memory).

## The solver on Maier's 1D case (`verification/maier1D/`, set up and run 2026-11-20)
- **Decided with the user (2026-11-20):** f128 PEG first; their inlet (S(0) = 0.99: water at −pc(0.99)); reference curves
  digitised from their figures (user); `coatsTimeStep` made to take other kr models. Built: case `f128_PEG` (mesh checked),
  `richards1D.py` (their model from the paper, checked against the similarity solution without gravity), predictions P1–P4 and
  the table of readings A–D (as stated, K × 4, no gravity, bath inlet) in the study README. `coatsTimeStep` extended to the
  Mualem kr (checks in the study README); inlet α `fixedValue 0.99` (an `inletOutlet` inlet never lets water into a dry
  column); run launched on the laptop the same day.
- **Result (2026-11-20, study README):** the solver with their inputs reproduces the Richards replica with the same face flux
  (gravity on): uptake within 0.3–1.7 %, S 0.5 front within 1 %, S 0.1 front +3.1 / +2.5 % at 50 / 100 s (under one cell),
  budget closed, 1.07 million steps in 88 min. **Their published curves (Figs. 16–19, fronts traced in the PDF images by
  `readFronts.py`, ±0.3 mm; the first readings by eye were off by up to 2.3 mm, all fits redone the same evening) are not what
  the paper's equations give with the paper's inputs** (RMS 1.9–8.4 mm; f128 at 3000 s 82 against 65 mm). **A fit with two
  factors per case (`fitFigures.py`) reproduces all four within the reading precision with one common gravity factor 0.35**
  (RMS 0.35–0.48 mm, whole profiles on their curves) and K × 0.73–1.21 per case: their code solves the same equations, but
  gravity is ~1/3 as strong relative to capillarity as the stated inputs give (equivalently pc ~2.9× higher with K ~2.9×
  lower), in every case. A systematic difference in their code or inputs, not per-case tuning; not attributable further
  without the authors (data on request). The g = 0 run reproduces the replica without gravity within 1.8 % in uptake (study
  README): the solver's porous path verified with and without gravity.
- **Likely cause (2026-11-20, study README, hypothesis):** their eq. 8 is printed with k_rel instead of ∂k_rel/∂S; coded that
  way (gravity term 4–7× too weak) their eq. 6 reproduces f128, f256 PEG and f256 EG within the reading precision with full
  gravity and no gravity factor (RMS 0.2–0.4 mm), K adjusted per case (0.79–1.12); not f48 (1.4 mm, against 0.48 mm with a
  uniform factor 0.35). The correct term fails for any K. Not checkable without their code (corresponding author: L. Maier,
  Stuttgart).
- **Their experiments with the correct gravity term (2026-11-20 evening, asked by the user via the mean-saturation panels;
  study README):** the normalised mean-saturation panels do not test gravity on the measured side: the measured S_av of f128,
  f256 PEG and f256 EG grows faster than √t at the start (local exponent 0.61–0.70, impossible for any Richards solution)
  because the measured profiles begin ~3.5 mm above the bath (first 1.5 mm square) and fill in behind the front (f128 first
  square S 0.84 → 0.92); their simulated S_av panels confirm the gravity × 0.35 (RMS ≤ 0.006). The measured fronts, fitted
  with the correct gravity term and free K and pc scales: f128 ~1 mm at pc × 1.3–2 Table 4's, f256 EG 0.7–1.0 mm at × 2–2.9,
  f256 PEG 0.9 mm at × 2.9–5 (flat), Table 4's pc 1.7–2.8 mm; f48 fitted by no scale (2.9 mm at best, at Table 4's pc; its
  measured front stays sharp while it slows, which a Richards profile with this flat pc(S) cannot do). With the paper's inputs
  the model misses the measured fronts at the last time by −21 / −9 / −3 / +12 mm (S 0.1). **Reading (hypothesis): the
  published agreement of the finer yarns rests on two differences that partly cancel: the gravity slip (× 0.35 ≡ pc × 2.9) and
  an effective pc too low for those yarns; f48 goes the other way. For this route: their experiments do not validate the
  pore-morphology pc as published; the "pc scale" is effective (it also absorbs pc(S) shape, Gebart's K for a random bundle,
  the filling-in).**
- **Audit of the reading (2026-11-20, study README):** every value and unit of Tables 1–4 and eqs. 4–11 checked on the rendered
  pages; the paper never says it fitted the model to the wicking curves (it claims the opposite). For f128 the inputs that set
  gravity against capillarity are confirmed inside the paper (ρ in Table 2; Table 4's pc on their own Fig. 22), so the gravity
  reduction is not a reading error. **For the parametrization route:** their own Table 4 and pc figures disagree by ~10 %
  (f48) and ~20 % (f256 PEG), and Table 1's porosities and f256 diameter do not follow their own formulas: use their method,
  not their numbers.
  Note: their whole simulation is that 1D Richards model (~100 lines); the pore-morphology pc curve is an input to it.
- **Idea (user):** run the solver with Maier's inputs on their 1D column and compare with their simulated and measured profiles.
- **Cost (Claude's estimate, scratch script):** the explicit step is set by the Coats limit, dt ≈ 0.5·ε·Δx²/(4·D_max) with
  D = K·|dpc/dS|·λ_a·λ_w/(λ_a + λ_w) (largest at S ≈ 0.97–0.99), not by the physical time. Gebart K with the radius, their grid
  (Δx 0.5 mm, 300 cells over 0.15 m): D_max 0.7–2.3e-5 m²/s, dt 1.2–3.9e-3 s, 0.5–1.3 million steps to 3000 s (PEG) or 600 s
  (EG); ×4 at Δx 0.25 mm, ×4 if their K used the diameter. At the per-step cost of the 1D twins on the laptop (172 cells: hybrid
  3.3 ms, impesFoam 0.9 ms): about 30–70 min (hybrid), 10–20 min (impesFoam). Out of reach only at our 20 µm cells (3–8 × 10⁸
  steps).
- **What it would test:** the Van Genuchten/Mualem path of the library (not used in our runs); long times with gravity (fronts
  near pc/ρg); a code-to-code comparison with their Richards model (the air is negligible for PEG, μ ratio 5,300); a first
  comparison with measured profiles, through their parameters; the R_f question (K or 4K: front ×2).
- **Needs:** `tools/coatsTimeStep` hard-codes Brooks–Corey kr (lines 144–147), so with Mualem kr the hybrid's dt is wrong
  without a message; impesFoam's `CoatsNo.H` takes kr and dpc/dS from the selected models (lines 6, 18) and runs it as is. The
  hybrid needs `coatsTimeStep` adapted (this repo, not the solver) or a fixed `maxDeltaT` below the estimate. Their curves
  digitised from the figures (data on request). A new case under `verification/` (not `trialWicking/`): 0.15 m, gravity, bath
  S 0.99 at the bottom, open top, initial S 0.01, μ and ρ of PEG or EG (σ unused without free cells). A 0.5 mm cell is fine
  there: Da = K/Δx² ~1e-3 (all Darcy faces) and no free cells (the 10–20 µm window is for the yarn/gap coupling).
- **Cells:** their model is 1D, each cell a 0.5 mm slice of the whole bundle (grid study 2 / 1 / 0.5 / 0.25 mm, converged at
  ≤ 0.5 mm in their scheme); their measured profiles are 1.5 mm squares, i.e. one value per 3 model cells. Ours: one row of cells
  with empty sides, only Δx along the column matters (the column of `verification/wicking1D/ABC` is 20 µm along, 0.55 × 0.237 mm
  across; empty patches add no faces to the Coats sum). Our scheme differs (upwinded kr, explicit Euler, first order): run 0.5 and
  0.25 mm and compare.
- **Inlet (user, 2026-11-20): the bath of the reference `N2c_full`** (`REV_pipeline/cases/vertical`): J off, p `totalPressure` 0
  (bath at rest at 0 Pa), U `pressureInletOutletVelocity`, α `fixedValue` 1, phase velocities zeroGradient. On porous boundary faces
  the upwinded kr takes the boundary value (OpenFOAM interpolation of non-coupled patches), so the air kr there is that of α 1
  (≈ 0): no air leaves through the inlet, as with J. **This is not Maier's condition:** their S(0) = 0.99 is water at −pc(0.99)
  (627 Pa for f128 PEG, 955 Pa for f256 EG); the N2c bath gives water at 0 Pa. Richards similarity solution without gravity
  (Claude, scratch script, Philip's method as `verification/analyseWicking1D.py`, Se clipped at 1 − 1e-4 as the solver): S 1
  against 0.99 at the inlet gives front (S 0.1) +23 %, uptake +31 % for both cases (f128 PEG 82 → 101 mm at 3000 s, f256 EG 93 →
  115 mm at 600 s). So against their simulated curves the inlet dominates any solver difference; against their experiments (a
  real bath, saturation normalised to 1 at the bottom) the N2c inlet is the closer one. Option for the code-to-code part: one
  more run with their inlet (template `verification/waterOnlyReservoir/1D_waterOnly`: J, coded inlet p with air at 0 Pa and α
  0.99, reads pc0 and m from `transportProperties`). Open top (their S(0.15 m) = 0.01 is never reached by 3000 s). Their S runs from 0 to 1 with no residual:
  `alpha.wettingmin/max` and `...minpc/maxpc` 0 / 1 (our cases use 0.999). Air (not in their model): μ 1.8e-5 Pa·s, ρ 1.2 kg/m³.
- **Coats with Mualem kr:** the kr derivative in the hybrid library is wrong, `krVanGenuchten.H:140` `pow(Se_,1/m_-1/2)` (integer
  1/2 = 0: exponent 1/m instead of 1/m − 1/2); porousMultiphaseFoam's copy has `1/m_-0.5` (`krVanGenuchten.C:146`). The hybrid
  solver never uses dkr/dS (only kr), so its results are not affected; impesFoam uses the porousMultiphaseFoam library. Do not copy
  the derivative from the hybrid library into `coatsTimeStep`. Options: a case-local copy of `coatsTimeStep` with a Mualem branch
  (`tools/` untouched), checked against a run at a fixed small dt; or no Coats and a fixed `maxDeltaT` below the estimate.
- **Reference curves (done 2026-11-20):** fronts of Figs. 16–19 traced (`readFronts.py`), normalised mean saturation read by
  colour (`meanSaturation.py`); the authors could still answer the R_f, c and eq. 8 questions. PDF in the user's Zotero storage.
- **Side result:** with m ≈ 0.77 the dry end is mild: pc(S 0.002) = 5–17 kPa for their four curves, against 2.5 MPa at our
  m 0.5 (the divergence that seeded study 2f's failure).

## Literature found 2026-11-20 (Consensus search on the model choice; abstracts only)
- Rybak, Magiera et al. 2015, Comput. Geosci., DOI 10.1007/s10596-015-9469-8: Stokes free flow + Richards in the porous medium,
  coupled at a sharp interface, multirate time stepping (the two parts have different time scales).
- Casulli 2017, Int. J. Numer. Methods Fluids, DOI 10.1002/fld.4389: hydrostatic surface flow + Richards in one pressure system,
  semi-implicit, nested Newton.
- Li, Huang et al. 2022, J. Compos. Mater., DOI 10.1177/00219983221111495: Cahn–Hilliard + Navier–Stokes in the channels,
  two-phase Darcy in the tows, BJS condition (resin infusion): the structure closest to ours.
- Boubaker, Cantarel, Debenest 2026, Mater. Sci. Forum, DOI 10.4028/p-vmx8fd: hybridPorousInterFoam with isoAdvector on a µCT
  plain weave (resin impregnation).
- Pacquaut, Bruchon et al. 2011, Int. J. Numer. Methods Fluids, DOI 10.1002/fld.2569: Stokes–Darcy on one mesh, a level set for
  the fluid/porous interface and the resin front.
- He, Liu, Wu 2021, Polymers, DOI 10.3390/polym13162689: Stokes–Brinkman with a capillary pressure drop, level-set front
  (injection moulding).
- Geoffre, Moulin et al. 2023, Transp. Porous Media, DOI 10.1007/s11242-023-01912-w: the front spread in their fibrous media is
  small enough to justify sharp-front models at the upper scale.
- None does spontaneous wicking with Richards yarns and VOF gaps (consistent with `NOTES_cases.md`, Literature, 2026-10-12). From
  memory, not checked: RichardsFoam (Orgogozo et al. 2014, Comput. Phys. Commun.), improved IMPES (Chen, Huan & Li 2004, Transp.
  Porous Media). In the porousMultiphaseFoam fork: `groundwaterFoam` (Richards, Picard + Newton, adaptive dt, seepage, isotropic
  K only; not built on the laptop).

## Sources (PoreSpy)
- Tutorials index: https://porespy.org/_examples/simulations/tutorials.html
- Two-phase flow overview, part 1 (drainage): https://porespy.org/examples/simulations/tutorials/overview_of_two_phase_flow_part1.html
- Part 2 (imbibition): https://porespy.org/examples/simulations/tutorials/overview_of_two_phase_flow_part2.html
- Reference pages: https://porespy.org/examples/simulations/reference/imbibition.html,
  https://porespy.org/examples/simulations/reference/drainage.html,
  https://porespy.org/examples/filters/reference/capillary_transform.html,
  https://porespy.org/examples/metrics/reference/pc_map_to_pc_curve.html
- PyPI: https://pypi.org/project/porespy/
