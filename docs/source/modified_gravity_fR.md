# Hu-Sawicki f(R) gravity

`cosmicjellyfish` can forecast constraints on Hu-Sawicki f(R) gravity (n = 1) with the `class`
backend, using [frahi_class](https://github.com/matiasleize/frahi_class), a hi_class-based CLASS
that solves the exact f(R) background and the quasi-static perturbations. The model parameter is
`log10fR0` = log10|f_R0|, with f_R0 = f_R(z = 0) of the solution.

Everything described here is opt-in: with the default options the behaviour of the `class`
backend is unchanged.

## Installation

frahi_class is not installed by any extra. See {doc}`installation` (section *Hu-Sawicki f(R)
gravity*) for how to get and build it, and for the optional `emantis` package.

## Running a forecast

Select the frahi_class wrapper explicitly, together with `cosmo_model: HuSawicki` and one of the
shipped profiles, and add `log10fR0` to the fiducial parameters:

```python
from cosmicjellyfish.fishermatrix import cosmicfish

options = {
    "code": "class",
    "class_module": "hiclassy",  # the Python module built by frahi_class
    "class_object": "HiClass",
    "cosmo_model": "HuSawicki",
    "class_config_yaml": "<path>/frahiclass_hs_photo_winther2019.yaml",
    "nonlinear": True,
    "feedback": 1,
    # survey options as for any photometric forecast
}
fiducial = {
    "Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.815, "mnu": 0.06,
    "log10fR0": -5.301,  # |f_R0| = 5e-6
}
fisher = cosmicfish.FisherMatrix(
    fiducialpars=fiducial,
    freepars={"log10fR0": 0.01},  # plus the other parameters to vary
    options=options,
    observables=["WL", "GCph"],
    cosmoModel="HuSawicki",
    surveyName="Euclid",
)
result = fisher.compute()
```

Selecting a `frahiclass_hs_photo*.yaml` profile does **not** select the wrapper: without
`class_module` and `class_object` the official `classy.Class` is used and the f(R) parameters
are rejected.

`log10fR0` is translated to the frahi_class input `parameters_smg = "<log10fR0>, 0.0"` (the
second value is the starting guess of the shooting parameter, solved for by frahi_class). As in
LCDM, `w0` and `wa` are dropped for `cosmo_model: HuSawicki`.

## Shipped profiles

The profiles live in `cosmicjellyfish/configs/default_boltzmann_yaml_files/class/`.

| profile | nonlinear power spectrum |
|---|---|
| `frahiclass_hs_photo.yaml` | HMcode-2020 applied by frahi_class to the f(R) linear P(k) (validated against Winther et al. 2019 only for \|f_R0\| <= 1e-4) |
| `frahiclass_hs_photo_winther2019.yaml` | LCDM nonlinear P(k) times the Winther et al. 2019 boost |
| `frahiclass_hs_photo_emantis.yaml` | LCDM nonlinear P(k) times the e-MANTIS boost (needs `emantis`) |

In all of them, massive neutrinos are three degenerate species, and the lensing kernel uses
Sigma = 1 (the factor 1/(1 + f_R) is neglected, an O(|f_R|) approximation).

## Nonlinear boosts

With `NONLINEAR: model: 'winther2019'` or `'emantis'`, frahi_class only provides the linear
spectra and `A_s`. The nonlinear spectrum is

P_NL^f(R)(k, z) = P_NL^LCDM(k, z) x B(k, z),

where P_NL^LCDM is computed with the official `classy` for LCDM with the same parameters and the
same `A_s` as the f(R) run, and B(k, z) is the f(R) boost. The implementation
(`cosmicjellyfish/cosmology/modified_gravity.py`) reproduces the MontePython likelihood
`euclid_photometric_z_fofr` (Sefa76/photometric_fofR, used in Koyama et al. 2024):

- `winther2019`: the Winther et al. 2019 fitting formula (arXiv:1903.08798), with `hasBug = False`.
- `emantis`: the e-MANTIS emulator, with Omega_m and the LCDM sigma8 clipped to the overlap of the
  likelihood bounds ([0.24, 0.39] and [0.60, 1.00]) and the installed emulator's bounds.
  With e-MANTIS 1.4.0, this sets the lower LCDM sigma8 bound to 0.6083.
- Beyond the range of each boost: power-law extrapolation above k_max (10 h/Mpc for Winther, the
  last e-MANTIS bin for e-MANTIS) and above z = 2; B is clipped to [1, 2], and B = 1 outside
  0.001 < k < 50 h/Mpc.

The same boost is applied to the cb spectrum (an approximation, as for the EE2 boost).

Keys of the `NONLINEAR` section:

| key | default | meaning |
|---|---|---|
| `model` | — | `winther2019` or `emantis` |
| `lcdm_nonlinear` | `hmcode_2020` | nonlinear prescription of the LCDM run; the shipped profiles use `halofit` (Halofit-Takahashi, as in Casas et al. 2023) |
| `fofR_settings` | likelihood defaults | overrides of `modified_gravity.LKL_DEFAULTS`: `use_bug`, `fofR_interpolation_k_boost`, `fofR_interpolation_z_boost`, `k_min_h_by_Mpc`, `k_max_h_by_Mpc`, `zmin`, `zmax`, `nzmax` |
| `cb_prescription` | `neutrino_subtraction` | how the LCDM cb spectrum is obtained: `neutrino_subtraction` or `class_native` |

Two derived quantities are stored in the results: `lcdm_sigma8` (sigma8 of the LCDM run, the
input of e-MANTIS) and `sigma8_fofR_kazuya` (sigma8 of f(R) from the linear Winther enhancement
with the correction of the likelihood; a cross-check only, not used in the observables).

## frahi_class flags in the profiles

These flags belong to frahi_class and are passed to it unchanged from the `HuSawicki` section of
the profile. Since frahi_class 2026-11-19 most of them are its defaults for
`gravity_model = hu_sawicki`; the profiles keep them explicit so that older builds give the same
result. See the frahi_class README for the full list.

| flag | value in the profiles | meaning |
|---|---|---|
| `gravity_model` | `hu_sawicki` | Hu-Sawicki f(R), n = 1, with the exact f(R) background |
| `hs_parametrization` | `log_10(fR0)` | the first entry of `parameters_smg` is log10\|f_R0\| |
| `hs_convention` | `physical` | f_R0 and H0 are those of the solution at z = 0 (`lcdm_anchored`: they refer to the LCDM-like c1/c2) |
| `hs_field` | `u` | integration variable u = log((f_R - 1)/f_R0) |
| `hs_handoff_ic_smg` | `slow` | the scalaron starts on the slow manifold at the handoff from GR |
| `hubble_evolution` | `no` | H from the Friedmann constraint (`yes` integrates H; at \|f_R0\| = 1e-5 it changes sigma8 by ~5e-8) |
| `qsa_mu_gamma_smg` | `yes` | quasi-static mu-gamma closure of the metric potentials, with c_s^2 = 1 |
| `qsa_only_smg` | `yes` | the scalaron is quasi-static at all times |
| `method_qs_smg` | `automatic` | quasi-static method of hi_class |
| `skip_stability_tests_smg` | `yes` | skip the hi_class stability tests |
| `kineticity_safe_smg` | `0` | no extra kineticity added for numerical safety |
| `Omega_smg` | `-1` | the scalar field closes the energy budget (with `Omega_Lambda = Omega_fld = 0`) |

## Validation

For the Euclid photometric probes (WL + GCph + XC, ISTF pessimistic) at |f_R0| = 5e-6, the
forecast relative error on log10|f_R0| is 2.59 % with the Winther boost and 2.42 % with
e-MANTIS, compared with 2.7 % in Casas et al. 2023 (Table 2).
