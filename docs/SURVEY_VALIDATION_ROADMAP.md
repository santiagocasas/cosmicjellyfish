# Survey validation roadmap: DESI, Rubin/LSST, SKAO and Planck

**Status:** in progress
**Owner:** core maintainers
**Related:** [`docs/KNOWN_ISSUES.md`](KNOWN_ISSUES.md), [`docs/source/comprehensive_guide.md`](source/comprehensive_guide.md),
[`paper/paper.md`](../paper/paper.md), Casas et al. 2023 ([arXiv:2210.05705](https://arxiv.org/abs/2210.05705))

This is the living plan for validating the non-Euclid survey configurations that the
code advertises but does not currently ship or test: **DESI** (spectroscopic), **Rubin /
Vera C. Rubin Observatory / LSST** (photometric), **SKAO** (HI galaxy clustering,
intensity mapping and the photometric variant) and **Planck** (CMB). It also covers the
historical SKAO radio x optical forecast from Casas et al. 2023, restricted to its
**GR-only** content.

The roadmap is a working document. Update the status tables and the progress log at the
bottom of this file as work lands. A polished, user-facing summary will be added under
`docs/source/` once the validation results exist; this file stays as the engineering
tracker.

---

## 1. Objective and scope

**Objective.** Show that every survey configuration the package claims to support can be
configured, run end-to-end, and that its observables and Fisher matrices agree with the
historical reference implementation (the `cosmicfish_reloaded_skaproject` checkout) and
with the published SKAO forecast where a like-for-like comparison is physically
well-defined.

**In scope**

- Migrate the historical DESI, Rubin and SKAO survey inputs into the current
  `specifications` YAML schema under the packaged survey directories.
- Run photo (GCph, WL, 3x2pt) and spectro (GCsp) forecasts for each survey and compare
  them against the corresponding Euclid run.
- Validate individual observables (number densities, bias, volume, `P_gg(k, mu, z)`,
  HI brightness temperature, beam and noise) against the original project **before**
  trusting any Fisher number.
- Reproduce the **GR-only** parts of Casas et al. 2023 (Fig. 1 spectra, per-probe
  constraints, probe combinations, IM x DESI cross-correlation).
- Ship CLI scripts, one tutorial notebook, a docs page, and a compact figure + text for
  the JOSS paper.

**Out of scope**

- Modified-gravity forecasts (`mu`, `eta`, `Sigma`, `E11`, `E22`). The historical runs
  used external MGCAMB tables that are not part of this package. The SKAO paper's
  headline numbers (mu 2.7 %, Sigma 1.8 %, etc.) are MG constraints and are **not** valid
  targets for a GR-only run.
- Reproducing the historical numbers digit-for-digit. The old runs used a different
  backend (`code: 'external'` with MGCAMB), an MG fiducial and, in places, a different
  binning. The goal is to explain every difference, not to hide it.
- Full-shape / bispectrum analyses; all forecasts stay in the Gaussian Fisher
  approximation used by the rest of the package.

**Definition of done.** A reader can follow the docs page, pick a shipped survey, run a
quick forecast with one command, and see a results table that separates
(a) historical MG references, (b) matched historical observables, and (c) new GR
forecasts, with the caveats stated explicitly.

---

## 2. Current state (starting point)

Verified against `main` before this workstream:

| Area | State |
| --- | --- |
| DESI | Survey-name branch exists in `config.py`. Paper-era `DESI-BGS-SKAOPaper` and `DESI-ELG-SKAOPaper` files are now shipped, opt-in via `survey_name_spectro`. |
| Rubin / LSST | Paper-era `Rubin-Photometric-SKAOPaper` is now shipped, opt-in via `survey_name_photo`. |
| SKAO photometric | `SKAO-Photometric-Redbook.yaml` shipped; paper-era cuts (`lmax_GCph` 1500, `lmax_WL` 5000) live in `SKAO-Photometric-SKAOPaper.yaml`. |
| SKAO spectroscopic | `SKAO-Spectroscopic-Redbook.yaml` shipped; the missing `Ps_5` key is fixed, and `SKAO-Spectroscopic-SKAOPaper.yaml` holds the paper-era transcription. |
| SKAO intensity mapping | `SKAO-IM-Redbook.yaml` shipped; `SKAO-IM-Redbook-DESI-ELG.yaml` adds the DESI-ELG-aligned bins. The dual `area_survey_IM`/`fsky_IM` values remain and are documented (issue 3). |
| Planck | `Planck.yaml` shipped and selectable by `surveyName`; CMB path documented in `docs/source/cmb_benchmarks.md`. |
| Cross-spectra | `observables=['GCsp','IM']` selects the **IM x GCsp cross-spectrum only**, not auto + cross. Must be stated in the docs. |
| Historical inputs | Present only in the read-only `cosmicfish_reloaded_skaproject` checkout (`.dat` tables, old YAMLs, saved Fisher matrices, `data-for-fig1.dat`). |
| Notebooks | Old workflows survive only in `notebooks/archive/old/` (`Example_Fishers-Various_Surveys-DESI-Rubin-Euclid.ipynb`, `SKAO_presentation.ipynb`). |

---

## 3. Phases

Each phase has an explicit exit criterion. Do not start a later phase on top of an
unvalidated earlier one: the Fisher numbers are only meaningful if the inputs and the
observables already agree.

### Phase 0 - Provenance map and assumptions table

**Goal.** Before touching a single number, know exactly where every historical input lives
and what it means.

Tasks

- [x] Inventory every historical file and map it to the current schema element
      (source path, notebook/cell, survey value, units, current equivalent).
- [ ] Trace which `vfinal/` Fisher matrices and which plot data correspond to which
      figure/table in Casas et al. 2023. (Started; `vfinal/` inventory recorded in
      section 5, per-figure mapping still open.)
- [x] Compare old vs new formulas for: number density `n(z)`, linear bias, photo-z
      parameters, shot noise, HI beam, system noise, survey volume.
- [x] Establish what the old `dn3` column means in the old volume calculation before
      mapping it to `dndOmegadz`. Result: `dn3` is `dN/dz` per deg^2, and the old volume
      formula is algebraically identical to the current one.
- [x] Record the old derived conventions: `z0 = zm / sqrt(2)`, `z0_p = 1.0` for
      non-Euclid (cancels in normalization), `binrange = range(1, len(z_bins))`,
      `ngalbin` from `ngal_sqarmin`.
- [x] Keep the original data **read-only**; never modify the historical checkout.

Deliverable: the assumptions table in [section 6](#6-provenance-and-assumptions-table)
filled in, with every row marked *matched*, *different by design* or
*requires investigation*.

**Exit criterion.** Every input file has an owner row in the table and no row is left
"requires investigation" without a follow-up task.

### Phase 1 - Migrate survey configurations

**Goal.** Ship DESI, Rubin, SKAO paper-era and Planck inputs in the current schema, with
names that make the provenance obvious.

Naming convention: append `-SKAOPaper` to configurations transcribed from the historical
project so nobody confuses them with current-official specs. Keep the already-shipped
current names untouched.

Planned files (final names may shift once Phase 0 confirms the inputs):

| New file | Source | Contents |
| --- | --- | --- |
| `DESI-BGS-SKAOPaper.yaml` | `DESI_BGS_GCsp.dat`, `DESI-Optimistic.yaml` | 5 z-bins 0.0-0.5, `dndOmegadz` 1165/3074/1909/732/120, bias 1.364..1.454, area 14000 |
| `DESI-ELG-SKAOPaper.yaml` | `DESI_ELG_GCsp.dat` | z-bins 0.6-1.6+, densities and bias from the `.dat` table, area 14000 |
| `Rubin-Photometric-SKAOPaper.yaml` | `Rubin-Optimistic.yaml` | 10-bin `z_bins` 0.001-2.50, `zm` 0.156, `ngamma` 0.68, `ngal_sqarmin` 27, `lmax_GCph` 1500, `lmax_WL` 5000, fsky 0.33/0.35 |
| `SKAO-Photometric-SKAOPaper.yaml` | `SKA1-Redbook-Optimistic.yaml` | same 10-bin edges, `zm` 1.1, `lmax_GCph` 1500, `lmax_WL` 5000, fsky 0.1166 |
| `SKAO-Spectroscopic-SKAOPaper.yaml` | `SKA1_GCsp_MDB2_Redbook.dat` | 5 bins 0.0-0.5, densities 2714.82..154.353, bias 0.648..0.973, area 5000 |
| `SKAO-IM-Redbook-DESI-ELG.yaml` | `SKA1_IM_MDB1_Redbook-new-DESI_E.dat` | IM bins aligned to DESI ELG for the cross-correlation |
| `Planck.yaml` (existing) | shipped | verify, do not duplicate |

> **Open decision (Phase 1):** should the paper-era DESI/Rubin/SKAO files live in
> `default_survey_specifications/` or `other_survey_specifications/`? Proposed: the
> historical variants go to `other_survey_specifications/` (opt-in), while a minimal
> *current-best* DESI and Rubin file may be promoted to `default_survey_specifications/`
> so `surveyName="DESI"` stops failing. Confirm before writing files.

Tasks

- [x] Transcribe bin edges, densities, fiducial bias and every nuisance parameter
      (`Ps_*`, `sigmap_*`, `sigmav_*` where relevant) for each new YAML.
- [x] Check that per-bin arrays are complete and that every bin has a matching key
      (this is exactly the `Ps_1..Ps_4` vs 5-bin bug in the shipped SKAO spectro file).
- [x] Confirm each YAML loads by name from an **installed** package (package data, not
      just the source tree).
- [ ] Confirm `surveyName="DESI"` and the Rubin branch resolve to a real file without an
      explicit `survey_name_*` option. (Currently they still need the option; see the
      Phase 1 decision below.)
- [x] Update `docs/source/comprehensive_guide.md` and `docs/KNOWN_ISSUES.md`.

**Decision taken:** historical variants live in `other_survey_specifications/` and stay
opt-in. The `DESI`/`Rubin` branches keep loading whatever `survey_name_photo` /
`survey_name_spectro` names, so the docs show the explicit option form. Promoting a
*current-best* DESI/Rubin file to the defaults is deferred until an up-to-date
specification is agreed.

**Exit criterion.** Every new YAML loads, produces a config, and passes a schema check;
`docs/source/comprehensive_guide.md` and `docs/KNOWN_ISSUES.md` are updated to reflect
what is now shipped. **Met:** `tests/survey_specs_test.py` covers parsing and
per-bin consistency; `FisherMatrix` construction was verified for DESI BGS, DESI ELG,
Rubin, SKAO photometric, SKAO spectroscopic and the IM x DESI-ELG cross.

### Phase 2 - Validate individual observables

**Goal.** Agree with the historical implementation *before* running any forecast.

Tasks

- [ ] **Photo (deferred):** compare `n(z)` and bin populations for Rubin and SKAO
      photometric, with matched photo-z, bias and scale cuts. Done: `dN/dz` shape and the
      per-bin galaxy counts. Not done: a direct comparison of the angular kernels and
      spectra against the historical project; those paths are exercised by the existing
      photometric observable tests, so this harness does not claim a spectra validation.
- [x] **GCsp:** compare bin density, bias, survey volume and `P_gg(k, mu, z)` for DESI
      BGS, DESI ELG and SKAO HI galaxies.
- [x] **IM:** compare `b_HI(z)`, `Omega_HI(z)`, `Tbar_b(z)`, the beam and the noise
      power for the SKAO IM configuration.
- [x] **Fig. 1 diagnostic:** recompute the Cai/Casas-style `P_gg`, `P_II`, `P_Ig` and
      shot-noise curves at `z = 0.6` and overlay them on `data-for-fig1.dat`. The
      historical curves used the MG fiducial, so a GR comparison is *not* expected to be
      exact; isolate the contribution from fiducial cosmology, backend and modelling.

Implementation: `scripts/validation/survey_observable_reference.py` (independent
transcription of the historical algebra) and `scripts/validation/validate_survey_observables.py`
(the CLI harness). Fast guard tests live in `tests/survey_observables_validation_test.py`.
The Tab. 7.1 numbers come from `uv run python scripts/validation/validate_survey_observables.py`.

**Exit criterion.** Every observable either matches within a stated tolerance or has a
documented, quantified explanation for the difference. **Met for the spectroscopic and
intensity-mapping observables and for the photometric redshift distribution and counts:**
all 33 machinery checks are algebra-level checks (the reference shares only the cosmology
object) and agree at machine precision; the Fig. 1 curves agree in shape and show the
expected few-percent modified-gravity offset (see Tab. 7.1). **Not met for photometric
angular spectra**, which are deliberately out of scope here.

### Phase 3 - Forecast comparisons

**Goal.** A common GR fiducial and parameter basis, so survey comparisons are fair.

Common setup: `Omegam 0.32, Omegab 0.05, h 0.67, ns 0.96`, `mnu = 0.06` eV held fixed
(not varied), flat LCDM, the same `k`/`mu` sampling and the same derivative method.

Tasks

- [x] **Photo:** Euclid vs Rubin, `GCph`, `WL`, and the 3x2pt combination.
- [x] **Spectro:** Euclid vs DESI BGS and vs DESI ELG, separately first, then combined.
- [x] **SKAO:** continuum photometric, HI galaxy clustering, intensity mapping
      individually, then the IM x DESI-ELG cross-correlation on aligned bins.
- [x] **Planck:** rerun the shipped CMB configuration.
- [ ] **Planck (follow-up):** compare against the published covariance / likelihood
      where reference inputs exist. The shipped `Planck.yaml` is a single-channel
      approximation with `lmax = 1500` and no lensing, so this is a separate task.
- [x] For every combination, state explicitly whether it is a cross-spectrum-only Fisher
      or a genuine joint auto + cross analysis. Check bin overlaps, cross-covariances and
      distinct nuisance names before adding information.

Implementation: `scripts/validation/run_survey_forecasts.py` (LCDM and w0waCDM reports,
JSON + Markdown). The numbers are in Tab. 7.2.

**Exit criterion.** A results table with a stable parameter set per probe, plus the
warnings that apply to each combination. **Met** for the GR probes; the Planck
published-covariance comparison is tracked as a follow-up.

### Phase 4 - Scripts, plots, notebook, docs, paper

**Goal.** Everything above is reproducible by a reader.

Tasks

- [x] CLI scripts under `scripts/validation/` with quick / default (full) modes,
      writing the effective configuration, backend version and an output directory.
      `run_survey_forecasts.py --case ...` selects a subset (the quick mode); the default
      runs every case in the chosen model.
- [x] Plots: survey coverage and inputs (n(z), bias, noise), representative spectra,
      Fisher ellipses via the existing `fishconsumer` machinery, marginal-error
      comparison panels, and the Fig. 1 historical-vs-current diagnostic.
      Produced by `scripts/validation/plot_survey_validation.py`.
- [x] One tutorial notebook that runs the quick configuration end-to-end:
      `notebooks/09-Survey-validation.ipynb`.
- [x] Docs page under `docs/source/` with the migrated specs, commands, results,
      limitations and comparisons; link it from `user_guide.md`
      (`docs/source/survey_validation.md`).
- [ ] JOSS paper: one compact figure and one paragraph, added **only** after Phase 3
      passes; revise the current "can load user specifications for DESI and LSST"
      wording to say what is actually shipped.

**Exit criterion.** Executed notebook, strict docs build (`sphinx -W`), and paper figure
regenerable from a committed script.

### Phase 5 - Verification and completion

Tasks

- [x] Tests for every shipped survey configuration: loading, package data, bin
      consistency, parameter-name completeness and uniqueness
      (`tests/survey_specs_test.py`).
- [x] Tests for the observable and covariance paths touched by the new configurations
      (`tests/survey_observables_validation_test.py`, `tests/survey_covariance_test.py`).
- [x] Quick end-to-end forecast per survey as a smoke test; full forecasts run separately
      with recorded timings and settings (Phase 3 timings above, from a full run).
- [x] Derivative-step and resolution checks; Fisher symmetry and conditioning checks;
      nuisance-marginalisation checks. See the step scan below.
- [x] Results table separating historical MG references, matched historical observables
      and new GR forecasts (Tab. 7.1 marks each row `ok` or `expected`, with the reason;
      Tab. 7.2 holds the new GR numbers).
- [x] CHANGELOG entry (updated per step).
- [x] Final review pass; PR body prepared (branch `feature/survey-validation`).

Derivative-step scan, DESI ELG `GCsp` (`sigma(Omegam)`, `sigma(sigma8)`; nuisance
marginalised). The spectroscopic run is not converged at the 1% step used in the first
pass; the 0.2% step agrees with 0.05% at the 0.1% level and is used for Tab. 7.2.

| Step | sigma(Omegam) | sigma(sigma8) |
| --- | --- | --- |
| 0.01 | 0.004833 | 0.003894 |
| 0.005 | 0.005018 | 0.005361 |
| 0.002 | 0.005036 | 0.005353 |
| 0.001 | 0.005034 | 0.005351 |
| 0.0005 | 0.005034 | 0.005350 |

Resolution check at the 1% step (96 k x 9 mu vs 128 k x 12 mu): `sigma(Omegam)` changes
from 0.004833 to 0.004825 and `sigma(sigma8)` from 0.003894 to 0.003895, i.e. below 0.2%.

The same 1% -> 0.2% comparison was run on every clustering probe. The bias affects all
three-dimensional clustering analyses (GCsp and IM), not one survey:

| Probe | sigma(sigma8) at 1% | at 0.2% | ratio |
| --- | --- | --- | --- |
| Euclid `GCsp` | 0.005023 | 0.006269 | 1.25 |
| DESI ELG `GCsp` | 0.003895 | 0.005353 | 1.37 |
| SKAO HI `GCsp` | 0.027125 | 0.037376 | 1.38 |
| SKAO `IM` | 0.006163 | 0.007406 | 1.20 |

In absolute terms the largest effect is on SKAO HI (0.0271 -> 0.0374) and DESI ELG
(0.0039 -> 0.0054); relative to their own error bar all four are 20-38%. The photometric
probes are stable: Euclid `GCph+WL` gives `0.002414`/`0.002995` at 1% and
`0.002415`/`0.002995` at 0.2%, and Rubin and SKAO photometric behave the same way.

**Exit criterion.** Green CI, strict docs build, and a reviewer can reproduce at least
one number per survey from the docs page alone.

---

## 4. Known issues to resolve along the way

| # | Issue | Where | Phase | Status |
| --- | --- | --- | --- | --- |
| 1 | SKAO photometric scale cuts differ between historical (`lmax_GCph` 1500, `lmax_WL` 5000) and shipped (750/3000) | `SKAO-Photometric-Redbook.yaml` | 1 | **resolved** - paper-era cuts kept in `SKAO-Photometric-SKAOPaper.yaml` |
| 2 | SKAO spectro defines 5 z-bins but only `Ps_1..Ps_4` shot-noise keys | `SKAO-Spectroscopic-Redbook.yaml` | 1 | **fixed** - added `Ps_5`; covered by `tests/survey_specs_test.py` |
| 3 | IM config has both `area_survey_IM: 5000` and `fsky_IM: 0.48`; the IM noise uses `fsky_IM` while `SpectroCov.volume_survey` used `fsky_spectro` | `SKAO-IM-Redbook.yaml`, `spectro_cov.py` | 1-2 | **fixed** - `SpectroCov.fsky_volume` now uses `fsky_IM` for IM-only and the smaller of the two fractions for a cross-spectrum; covered by `tests/survey_covariance_test.py` |
| 4 | Historical IM x DESI-ELG cross used bins aligned to DESI ELG; current covariance uses `intersect1d` on bins/mids | `spectro_cov.py` | 2-3 | **resolved** - the aligned `SKAO-IM-Redbook-DESI-ELG.yaml` gives 11 matching bins; the covariance test pins the overlap and the effective volume |
| 5 | `observables=['GCsp','IM']` selects the cross-spectrum only, not auto + cross | `fishermatrix/cosmicfish.py` | 3 | **documented** - stated in the docs page, the roadmap and the paper; not changed |
| 6 | Old runs used external MGCAMB tables, unavailable here | historical project | n/a | documented |
| 7 | `surveyName="DESI"` fails with a missing-file error | `config.py` | 1 | **documented** - requires an explicit `survey_name_spectro` option |
| 8 | Rubin and DESI have code branches but no shipped YAML | `config.py`, docs | 1 | **resolved** - `-SKAOPaper` files shipped |
| 9 | `kmax_IM`/`kmin_IM` are not consumed anywhere | `fishermatrix/cosmicfish.py`, specs | 2 | **traced and documented** - the historical project also used `kmin_GCsp`/`kmax_GCsp` for IM, so the IM forecasts inherit the GCsp range by design; the unused YAML entries are flagged on the docs page |
| 10 | Survey-table numbers in the docs had not been re-checked against the generated reports | docs | 1 | **fixed** - the LCDM/w0waCDM tables are generated from `results/survey_validation/*.json` |
| 11 | Photometric angular spectra are not re-compared against the historical project | `scripts/validation` | 2 | **deferred** - the harness checks `dN/dz` and bin counts only; the angular paths are covered by existing photometric tests |
| 12 | Fisher combinations rebuild each covariance from diagonal errors, dropping parameter correlations | `scripts/validation/run_survey_forecasts.py` | 6 | **fixed** - the script stores and sums the full marginalised blocks, refuses to combine a report without them, and keeps the summed block for further use; covered by correlated and missing-block regression tests |
| 13 | A cross-spectrum volume used `min(fsky_spectro, fsky_IM)`, which is the true overlap only when the smaller footprint is nested in the larger one | `spectro_cov.py`, docs | 5-6 | **documented** - the default is now explicitly a nested-footprint approximation, flagged as `fsky_cross_assumed_nested`; an optional `fsky_cross` key overrides it and values above the nested bound are rejected; covered by two covariance tests |
| 14 | The `w0`-`wa` figure overlaid six probes including the much weaker Planck-like run, and the script silently skipped missing Fisher files | `plot_survey_validation.py` | 4 | **fixed** - the figure is now four paired panels (photo, spectro, combined, IM vs GCsp) built from the stored blocks; a missing case raises |
| 15 | The cross-covariance test exercised `veff()` instead of the `veff_Ig()` used by the cross-spectrum forecast | `tests/survey_covariance_test.py` | 5 | **fixed** - the test now checks `veff_Ig` |

---

## 5. Historical reference material (read-only)

Path: `/home/santiago/CosmoProjects/CosmicFish-Projects/cosmicfish_reloaded_skaproject`
(remote `git@gitlab.com:matmartinelli/cosmicfish_reloaded.git`, HEAD `76f4892`).
**Do not modify this checkout.** It contains locally modified notebooks and untracked
Overleaf files.

Key inputs in `survey_specifications/`:

- `DESI_BGS_GCsp.dat`, `DESI_ELG_GCsp.dat` - `zmin zm zmax dn3 bias`, area in a header
  comment.
- `SKA1_GCsp_MDB2_Redbook.dat` - same format, SKAO HI galaxies.
- `SKA1_IM_MDB1_Redbook*.dat` - IM bins, including the DESI-ELG-aligned variant.
- `Rubin-Optimistic.yaml`, `DESI-Optimistic.yaml`, `SKA1-Redbook-Optimistic.yaml` -
  old-schema survey specs.
- `nofz_ska1_5000.dat`, `SKA1_THI_sys_noise.txt`, `SKA1-IM-z_Pnoise.txt`,
  `lumratio_file.dat` - auxiliary tables.
- `data-for-fig1.dat` - the spectra behind the paper's Fig. 1 at `z = 0.6`.
- `vfinal/`, `v2results/`, `results/`, `raw_results/`, `benchmark_results/` - saved
  Fisher matrices and plot data.

Reference parameter basis in the saved matrices:
`Omegam, Omegab, h, ns, sigma8, E11, E22, lnbgs8_1..N, Ps_1..N` with fiducial
`0.32, 0.05, 0.67, 0.96, 0.822246, 0.1007, 0.8293`.

---

## 6. Provenance and assumptions table

Filled in during Phase 0. One row per historical input or convention.

| Historical input | Source path / notebook | Unit | Current schema element | Match | Notes |
| --- | --- | --- | --- | --- | --- |
| `dn3` column | `*.dat` files, read as `gc_table[:,3]` | dN/dz per deg^2 | `dndOmegadz` | **matched** | Old `n_density = dn3*dz/d_volume_per_deg2`; current `n_density = dnz*dz/d_volume*areasky`. Since `d_volume_per_deg2 = d_volume/areasky`, the two expressions are algebraically identical. Copy `dn3` verbatim into `dndOmegadz`. |
| DESI BGS n(z), bias | `DESI_BGS_GCsp.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | 5 bins 0.00-0.50, densities 1165/3074/1909/732/120, bias 1.36436..1.45367, area 14000 deg^2 |
| DESI ELG n(z), bias | `DESI_ELG_GCsp.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | 11 bins 0.60-1.70, densities 309/2269/1923/2094/1441/1353/1337/523/466/329/126, bias 1.01916..1.36020 |
| SKAO HI galaxy n(z), bias | `SKA1_GCsp_MDB2_Redbook.dat` | dN/dz/deg^2 | `dndOmegadz`, `bHg_*` | **matched** | Identical to the shipped `SKAO-Spectroscopic-Redbook.yaml` (2714.82..154.353, 0.64813..0.97350) |
| SKAO IM bins | `SKA1_IM_MDB1_Redbook.dat` | - | `z_bins_IM` | **matched by design** | Multiple variants exist; shipped `SKAO-IM-Redbook.yaml` uses 10 bins 0.5-2.6 |
| IM x DESI-ELG bins | `SKA1_IM_MDB1_Redbook-new-DESI_E.dat` | - | `z_bins_IM` | **different by design** | Historical cross used IM bins aligned to DESI ELG. Needs a dedicated YAML; current `intersect1d` path must be tested (issue 4). |
| Photo `dNdz(z)` shape | `photo_window.py` | - | `dNdz` | **matched** | Both old and new use `(z/z0_p)^2 exp(-(z/z0)^ngamma)`. Old set `z0_p=1.0` for non-Euclid, new sets `z0_p=z0`; the difference is a constant factor that cancels in the bin normalization. |
| Photo `z0` | old/new config | - | `z0` | **matched** | `z0 = zm/sqrt(2)` in both. Rubin `zm=0.156`, SKAO `zm=1.1`, DESI-photo `zm=0.9`. |
| `ngal_per_bin` | old/new config | count | `ngalbin_GCph`, `ngalbin_WL` | **matched** | Both compute `(ngal_sqarmin*3600/nbins)*sr` with `sr` the sky area in deg^2. |
| Photo bias | old/new config | - | `photobiaspars` | **matched** | `binned` model generates `b_i = sqrt(1 + 0.5*(z_i+z_{i-1}))` in both. |
| Survey area | old `area_survey` | deg^2 | `area_survey_GCph`, `area_survey_WL`, `area_survey_spectro`, `area_survey_IM` | **different by design** | Current schema is per-probe and an explicit `fsky_*` overrides the area. When migrating, convert a single historical area into the per-probe keys and do not also copy a conflicting `fsky_*`. |
| Old volume formula | old `SpectroCov.volume_bin` | Mpc^3 per deg^2 | `d_volume`, `volume_survey` | **matched** | Old `volume_bin` divides the spherical shell by `4*pi*(180/pi)^2` and `volume_survey` multiplies by `area_survey`; current uses the full shell times `fsky`. Equivalent. |
| Shot noise | old configs | - | `shot_noise_parametrization` | **matched** | `Ps_*` all `0.0` in the saved matrices; still add every key for every bin (see issue 2). |
| FoG / `sigmap` | old configs | - | `nonlinear_parametrization` | **different by design** | Old defaults had `bfs8terms: True`; the JAX GCsp observable requires `False`. The two are algebraically identical at the fiducial (see `docs/source/gcsp_intermediate.md`), so this does not change the Fisher. |
| AP effect | old configs | - | `AP_effect` | **matched** | `True` in both. |
| Fig. 1 spectra | `data-for-fig1.dat` | Mpc^3 | new `P_gg`, `P_II`, `P_Ig` at `z=0.6` | **investigated** | Shapes agree to <= 1.5% over `0.005 <= k <= 0.05` 1/Mpc; the 0.5%-6.8% amplitude offset and the `Tbar`/noise residuals are the MG fiducial (`E11`, `E22`) used in the reference. Above `k ~ 0.05` the exponential FoG/beam damping amplifies the MG difference in the velocity moments. |
| Old MG parameter basis | `vfinal/*.paramnames` | - | - | **out of scope** | `E11`/`E22`/`mu`/`eta` cannot be reproduced; GR runs only. |

---

## 7. Results tables

### 7.1 Observable validation (Phase 2)

All numbers are the maximum relative difference between the package and the independent
reference transcription in `scripts/validation/survey_observable_reference.py`, at the GR
fiducial `Omegam=0.32, Omegab=0.05, h=0.67, ns=0.96, sigma8=0.822`.

| Observable | Survey | Reference | Max relative difference | Verdict | Notes |
| --- | --- | --- | --- | --- | --- |
| n_density | DESI BGS | `DESI_BGS_GCsp.dat` | 0.0 | matched | 5 bins |
| volume_survey | DESI BGS | `DESI_BGS_GCsp.dat` | 2.0e-16 | matched | Mpc^3 |
| fiducial bias | DESI BGS | `DESI_BGS_GCsp.dat` | 0.0 | matched | |
| P_gg(k, mu, z) | DESI BGS | historical recipe | 5.2e-16 | matched | 3 mu values, 4 redshifts |
| n_density | DESI ELG | `DESI_ELG_GCsp.dat` | 1.2e-16 | matched | 11 bins |
| volume_survey | DESI ELG | `DESI_ELG_GCsp.dat` | 2.4e-16 | matched | |
| fiducial bias | DESI ELG | `DESI_ELG_GCsp.dat` | 0.0 | matched | |
| P_gg(k, mu, z) | DESI ELG | historical recipe | 6.6e-16 | matched | |
| n_density | SKAO HI | `SKA1_GCsp_MDB2_Redbook.dat` | 2.2e-16 | matched | 5 bins |
| volume_survey | SKAO HI | `SKA1_GCsp_MDB2_Redbook.dat` | 1.4e-16 | matched | |
| fiducial bias | SKAO HI | `SKA1_GCsp_MDB2_Redbook.dat` | 0.0 | matched | |
| P_gg(k, mu, z) | SKAO HI | historical recipe | 6.5e-16 | matched | |
| Omega_HI(z), b_HI(z) | SKAO IM | paper Eqs. 19-21 | 0.0 | matched | analytic |
| Tbar_b(z), theta_b(z) | SKAO IM | paper Eqs. 19-22 | 0.0 | matched | |
| beam beta(k, mu) | SKAO IM | paper Eq. 24 | 0.0 | matched | |
| P_noise_21 | SKAO IM | paper Eq. 27 | 0.0 | matched | |
| P_II(k, mu, z) | SKAO IM | historical recipe | 7.1e-16 | matched | |
| P_Ig(k, mu, z) | SKAO IM x DESI ELG | historical recipe | 4.3e-16 | matched | aligned bins |
| dN/dz shape | Rubin, SKAO | analytic | 0.0 | matched | `z0 = zm/sqrt(2)` |
| galaxies per bin | Rubin, SKAO | `ngal_sqarmin` | 0.0 | matched | GCph and WL |
| Fig. 1 shape (`P_gg`, `P_II`, `P_Ig`) | SKAO IM x HI | `data-for-fig1.dat` | <= 1.5e-2 | quantified | p10-p90 spread over `0.005 <= k <= 0.05` 1/Mpc |
| Fig. 1 amplitude (`P_gg`, `P_II`, `P_Ig`) | SKAO IM x HI | `data-for-fig1.dat` | 0.5% - 6.8% | expected | reference used the MG fiducial (`E11`, `E22`); the offset is the GR-vs-MG growth/damping difference |
| Fig. 1 Tbar_b(0.6) | SKAO IM | `data-for-fig1.dat` | 1.1e-3 | expected | `Tbar` depends on `H(z)`; MG background |
| Fig. 1 P_noise_21 | SKAO IM | `data-for-fig1.dat` | 9.9e-5 | expected | same `H(z)` dependence |

### 7.2 GR forecast comparison (Phase 3)

Common setup for every row: GR fiducial `Omegam=0.32, Omegab=0.05, h=0.67, ns=0.96,
sigma8=0.822`, `mnu = 0.06` eV fixed, flat LCDM, `derivatives = 3PT`, relative steps `0.002`,
same `k`/`mu` sampling. A step scan (Tab. in Phase 5) showed that the three-dimensional clustering derivatives
(GCsp and IM) need `0.002`: at `0.01` their `sigma(sigma8)` is biased low by 20-38%
(Euclid GCsp 25%, DESI ELG 37%, SKAO HI 38%, SKAO IM 20%), while `0.002` and `0.0005`
agree to better than 0.1%. The photometric probes are stable at the
0.03% level between `0.01` and `0.002`. Bias, shot-noise and (where present) `sigma_v`/`sigma_p` nuisances
are marginalised before the errors are quoted. Produced by
`uv run python scripts/validation/run_survey_forecasts.py` (add `--model w0waCDM` for the
dark-energy table). The report records the resolved settings per case, the fiducial and
the package versions. Combinations sum the full nuisance-marginalised Fisher blocks of the
two probes (correlations retained), not their diagonal errors, and a report missing those
blocks is rejected. For IM the survey volume uses `fsky_IM`; the cross uses an explicit
`fsky_cross` when given and otherwise the smaller of the two sky fractions, which assumes
the smaller footprint is nested in the larger one. The IM `k` range is
inherited from the GCsp settings as in the historical project (see issue 9).

Marginalised 1-sigma errors, LCDM (`sigma8`, not `10^9As`, is the free amplitude here so
that every backend can run it):

| Survey | Probe(s) | sigma(Omegam) | sigma(Omegab) | sigma(h) | sigma(ns) | sigma(sigma8) |
| --- | --- | --- | --- | --- | --- | --- |
| Euclid | GCph+WL (3x2pt) | 0.00241449 | 0.00218174 | 0.0173254 | 0.0097284 | 0.00299523 |
| Rubin/LSST | GCph+WL (3x2pt) | 0.00124975 | 0.00198969 | 0.0118478 | 0.00499616 | 0.00159136 |
| Euclid | GCsp | 0.00478616 | 0.00131012 | 0.0105564 | 0.00898969 | 0.00626847 |
| DESI BGS | GCsp | 0.0128422 | 0.00389834 | 0.0169271 | 0.0330358 | 0.0212149 |
| DESI ELG | GCsp | 0.0050355 | 0.0014544 | 0.00843915 | 0.00934154 | 0.00535276 |
| DESI BGS + ELG | GCsp | 0.00364307 | 0.00134059 | 0.00624908 | 0.00811367 | 0.00490995 |
| SKAO | GCph+WL (3x2pt) | 0.00556561 | 0.00621195 | 0.0465785 | 0.0269691 | 0.00738337 |
| SKAO HI | GCsp | 0.0243804 | 0.00861922 | 0.0446646 | 0.0580188 | 0.0373749 |
| SKAO | IM | 0.00692111 | 0.00225796 | 0.0156393 | 0.00749774 | 0.00644563 |
| SKAO x DESI | IM x ELG | 0.0129225 | 0.00336428 | 0.0283735 | 0.0176025 | 0.042502 |
| Planck-like | CMB TT+TE+EE | 0.016075 | 0.0012949 | 0.0115754 | 0.00693771 | 0.00942461 |
| Euclid | GCph+WL + GCsp | 0.00189726 | 0.00085189 | 0.00654836 | 0.00426305 | 0.00218619 |

Marginalised 1-sigma errors, w0waCDM (`w0 = -1`, `wa = 0`; `FoM = 1/sqrt(det Cov(w0,wa))`):

| Survey | Probe(s) | sigma(Omegam) | sigma(Omegab) | sigma(h) | sigma(ns) | sigma(sigma8) | sigma(w0) | sigma(wa) | FoM(w0,wa) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Euclid | GCph+WL (3x2pt) | 0.0036437 | 0.00270685 | 0.023065 | 0.013234 | 0.00417464 | 0.041499 | 0.152296 | 378 |
| Rubin/LSST | GCph+WL (3x2pt) | 0.0025377 | 0.00225872 | 0.0134829 | 0.00530628 | 0.00252884 | 0.027936 | 0.0915612 | 897 |
| Euclid | GCsp | 0.0143087 | 0.00229787 | 0.0181856 | 0.0139647 | 0.0136481 | 0.116831 | 0.361461 | 83.9 |
| DESI BGS | GCsp | 0.0210305 | 0.00417824 | 0.0275829 | 0.0400758 | 0.031189 | 0.249038 | 1.20718 | 10.5 |
| DESI ELG | GCsp | 0.012488 | 0.00189264 | 0.0150732 | 0.0152487 | 0.0114671 | 0.0936742 | 0.32811 | 99.5 |
| DESI BGS + ELG | GCsp | 0.00936169 | 0.0015053 | 0.0115328 | 0.0138862 | 0.00920108 | 0.0640452 | 0.237508 | 161 |
| SKAO | GCph+WL (3x2pt) | 0.01689 | 0.00684925 | 0.0521334 | 0.0275988 | 0.0135739 | 0.193051 | 0.568189 | 25.9 |
| SKAO HI | GCsp | 0.037852 | 0.00910093 | 0.0551461 | 0.0647451 | 0.0563283 | 0.469886 | 2.44807 | 2.92 |
| SKAO | IM | 0.0148634 | 0.00285215 | 0.0220399 | 0.0137836 | 0.0112163 | 0.0969339 | 0.322458 | 72.5 |
| SKAO x DESI | IM x ELG | 0.0272612 | 0.00476902 | 0.0438979 | 0.02617 | 0.0536757 | 0.240052 | 0.733385 | 17.2 |
| Planck-like | CMB TT+TE+EE | 0.476852 | 0.0750947 | 0.501387 | 0.00799934 | 0.478239 | 4.61783 | 14.0196 | 0.0429 |
| Euclid | GCph+WL + GCsp | 0.00336613 | 0.00111382 | 0.00783857 | 0.00579484 | 0.00329397 | 0.0350528 | 0.120817 | 638 |

How to read these tables:

* **Rubin photometric beats the shipped Euclid photometric configuration on every
  parameter.** This is not a bug: the historical Rubin specification uses wider scale cuts
  (`lmax_WL = 5000` vs `1500` for the Euclid ISTF file) and a slightly different sky
  fraction. When comparing surveys, compare the *specifications*, not only the telescope
  names.
* **SKAO continuum photometric is weak** because the paper-era file uses `fsky = 0.1166`;
  its HI-galaxy and IM probes are competitive with each other but far weaker than the
  optical spectroscopic surveys on shape parameters.
* **The IM x DESI-ELG row is a cross-spectrum-only Fisher** (auto-spectra are not
  included). It is not directly comparable to the IM-only row.
* **IM volumes use the IM footprint.** The IM-only row uses `fsky_IM = 0.48` for both the
  volume and the noise; the cross uses the smaller of the two sky fractions. Before this
  fix the volume silently used the spectroscopic sky fraction. The IM `k` range still
  follows `kmin_GCsp`/`kmax_GCsp`, as it did historically.
* **Combinations retain the parameter correlations.** The combined rows add the full
  nuisance-marginalised Fisher matrices; the marginalised errors follow from the inverse
  of the sum. A diagonal-only combination would have understated the gain.
* **Planck-like** is the shipped single-channel approximation with `lmax = 1500` and no
  lensing, run with CAMB (the only backend that produces CMB spectra). It is not the real
  Planck likelihood and is included for completeness. Comparing against the published
  Planck covariance remains open (see Phase 3).
* All runs used `code = "symbolic"` except Planck (`code = "camb"`). The comparison is
  therefore *not* a backend comparison; the Phase 1/2 checks show the observables agree
  across backends.

### 7.3 SKAO paper cross-check (GR-only)

State clearly which paper numbers can and cannot be reproduced. The published headline
numbers are MG constraints and are **not** targets here.

| Quantity | Paper (MG) | This work (GR) | Comparable? | Comment |
| --- | --- | --- | --- | --- |
| sigma(mu) from SKAO radio | 2.7 % | n/a | no | MG parameter |
| sigma(Sigma) from SKAO radio | 1.8 % | n/a | no | MG parameter |
| Fig. 1 spectra | yes | <= 1.5% shape | quantified | shape matches; amplitude offset is the MG fiducial |

---

## 8. Deliverables checklist

- [x] `docs/SURVEY_VALIDATION_ROADMAP.md` (this file), kept up to date
- [x] New survey YAMLs under `cosmicjellyfish/configs/other_survey_specifications/`
- [x] `scripts/validation/` runners (observable harness, forecast comparison, plotting)
- [x] `notebooks/09-Survey-validation.ipynb` (executed)
- [x] `docs/source/survey_validation.md` + `user_guide.md` link
- [x] Figures committed under `docs/source/_static/survey_validation/`
- [x] Tests under `tests/` for configs, observables, script helpers and covariances
      (`tests/survey_specs_test.py`, `tests/survey_observables_validation_test.py`,
      `tests/survey_forecast_script_test.py`, `tests/survey_covariance_test.py`,
      `tests/survey_plot_test.py`)
- [x] CHANGELOG entry (updated per step)
- [x] `paper/` figure + paragraph
- [ ] PR

---

## 9. Progress log

Append one line per landed step. Keep it factual: what changed, what was verified, what
is next.

| Date | Step | Result |
| --- | --- | --- |
| 2026-11-13 | Wrote this roadmap | Plan recorded; next is Phase 0 provenance audit |
| 2026-11-13 | Phase 0: read historical `Nuisance`, `GalaxyPhotoDist`, `SpectroCov`, `config.py`, `.dat` tables and old YAMLs | `dn3` identified as dN/dz per deg^2; old and new `n_density`, `volume_survey`, `ngal_per_bin`, photo `dNdz` and photo bias all shown equivalent; assumptions table filled. Remaining Phase 0 item: per-figure mapping of `vfinal/` matrices |
| 2026-11-13 | Phase 1: migrated DESI BGS/ELG, Rubin, SKAO photo/spectro and IM x DESI-ELG specs; fixed the missing `Ps_5`; added `tests/survey_specs_test.py` | Six YAMLs parse, are per-bin consistent, load through `FisherMatrix`, and a DESI BGS `GCsp` forecast runs end-to-end. Next: Phase 2 observable validation |
| 2026-11-13 | Phase 2: added `scripts/validation/survey_observable_reference.py`, `scripts/validation/validate_survey_observables.py` and `tests/survey_observables_validation_test.py` | 33 machinery checks agree at machine precision (density, volume, bias, `P_gg`, IM thermodynamics, beam, noise, `P_II`, `P_Ig`, photo `dNdz` and bin counts). Fig. 1 diagnostic: shape agrees to <= 1.5% over `0.005 <= k <= 0.05` 1/Mpc with a 0.5%-6.8% amplitude offset from the MG fiducial. Next: Phase 3 forecast comparisons |
| 2026-11-13 | Phase 3: added `scripts/validation/run_survey_forecasts.py`; ran all 10 probe configurations at a common GR fiducial in LCDM and w0waCDM | Tab. 7.2 filled. Full LCDM set takes ~2 min, w0waCDM ~3 min (Planck/CAMB dominates). Rubin 3x2pt is stronger than the shipped Euclid photometric configuration because of its wider WL scale cuts; SKAO IM x DESI-ELG is cross-only. Next: Phase 4 scripts/plots/notebook/docs |
| 2026-11-13 | Phase 4 (docs half): added `scripts/validation/plot_survey_validation.py`, `docs/source/survey_validation.md`, `notebooks/09-Survey-validation.ipynb` and the four committed figures under `docs/source/_static/survey_validation/` | Figures regenerate from the JSON reports; the notebook executes top-to-bottom (three quick cases + observable validation, ~2 min). Strict docs build still to run. Next: paper figure/paragraph, then Phase 5 checks |
| 2026-11-13 | Phase 4 (paper half) + Phase 5: paper figure/paragraph, strict docs build, covariance tests, derivative-step and resolution scan | `paper/figures/fig4_survey_comparison.png` and the JOSS paragraph added; `sphinx -W` passes. New `tests/survey_covariance_test.py` covers the DESI-ELG and SKAO x DESI covariance paths. The step scan showed the GCsp derivatives were under-converged at 1%; Tab. 7.2 was regenerated at 0.2% and the docs updated. Next: final review and PR |
| 2026-11-13 | Final review: roadmap numbers, docs page, figures and notebook regenerated at the 0.2% step; 22 survey tests, ruff/black/isort and `sphinx -W` green | Branch ready to push as one PR |
| 2026-11-13 | Addressed the external review: full-matrix Fisher combination, probe-consistent IM volume, IM k-range documented as inherited, ellipse centring fixed, explicit `mnu = 0.06` eV, per-case settings and package versions recorded, claims narrowed (photo spectra deferred; Fig. 1 attribution softened) | LCDM and w0waCDM reports regenerated, tables/figures refreshed, correlated-combination and sky-fraction tests added |
| 2026-11-13 | Second review pass: combination now requires the stored blocks and keeps the summed one; cross-spectrum footprint marked as a nested-footprint default with an optional `fsky_cross`; cross covariance tested through `veff_Ig`; ellipse figure regrouped into four paired panels without the Planck-like run; remaining MG attribution and axis-title wording fixed | `w0wa_comparisons.png` replaces the six-curve plot; new tests cover missing/misshaped blocks and an explicit cross footprint |
