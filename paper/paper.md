---
title: "cosmicjellyfish: Fisher-matrix and Monte Carlo forecasts for cosmological surveys in Python and JAX"
tags:
  - Python
  - JAX
  - cosmology
  - large-scale structure
  - Fisher matrix
  - forecasts
  - automatic differentiation
  - nested sampling
authors:
  - name: Santiago Casas
    orcid: 0000-0002-4751-5138
    corresponding: true
    affiliation: "1, 2"  # TODO: confirm affiliations
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: data-curation, credit-name: "Data curation"}
      - {credit: investigation, credit-name: "Investigation"}
      - {credit: methodology, credit-name: "Methodology"}
      - {credit: project-administration, credit-name: "Project administration"}
      - {credit: software, credit-name: "Software"}
      - {credit: supervision, credit-name: "Supervision"}
      - {credit: validation, credit-name: "Validation"}
      - {credit: visualization, credit-name: "Visualization"}
      - {credit: writing-original-draft, credit-name: "Writing – original draft"}
      - {credit: writing-review-editing, credit-name: "Writing – review & editing"}
  - name: Sefa Pamuk
    orcid: 0009-0004-0852-8624
    affiliation: 3
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: investigation, credit-name: "Investigation"}
      - {credit: methodology, credit-name: "Methodology"}
      - {credit: software, credit-name: "Software"}
      - {credit: validation, credit-name: "Validation"}
      - {credit: writing-original-draft, credit-name: "Writing – original draft"}
  - name: V. M. Sabarish
    orcid: 0000-0001-5677-0838
    affiliation: "2, 4"
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: software, credit-name: "Software"}
  - name: Ziad Sakr
    orcid: 0000-0002-4823-3757
    affiliation: "18, 19, 20"
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: methodology, credit-name: "Methodology"}
      - {credit: software, credit-name: "Software"}
      - {credit: validation, credit-name: "Validation"}
  - name: Domenico Sapone
    orcid: 0000-0001-7089-4503
    affiliation: 5
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: software, credit-name: "Software"}
      - {credit: supervision, credit-name: "Supervision"}
  - name: Matías Leizerovich
    orcid: 0000-0002-6438-2285
    affiliation: "6, 7"
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: software, credit-name: "Software"}
      - {credit: validation, credit-name: "Validation"}
  - name: Noemi Frusciante
    orcid: 0000-0002-7375-1230
    affiliation: "8, 9"
    roles:
      - {credit: software, credit-name: "Software"}
  - name: Francesco Pace
    orcid: 0000-0001-8039-0480
    affiliation: "10, 11, 12, 13"
    roles:
      - {credit: methodology, credit-name: "Methodology"}
      - {credit: software, credit-name: "Software"}
  - name: Emilio Bellini
    orcid: 0000-0003-4762-0795
    affiliation: 15
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: data-curation, credit-name: "Data curation"}
      - {credit: software, credit-name: "Software"}
  - name: Kazuya Koyama
    orcid: 0000-0001-6727-6915
    affiliation: 14
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: methodology, credit-name: "Methodology"}
      - {credit: supervision, credit-name: "Supervision"}
      - {credit: validation, credit-name: "Validation"}
  - name: Stefano Camera
    orcid: 0000-0003-3399-3574
    affiliation: "10, 11, 12, 16"
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: methodology, credit-name: "Methodology"}
  - name: Marco Raveri
    orcid: 0000-0002-7354-3802
    affiliation: 17
    roles:
      - {credit: conceptualization, credit-name: "Conceptualization"}
      - {credit: software, credit-name: "Software"}
affiliations:
  - name: Institute for Theoretical Particle Physics and Cosmology (TTK), RWTH Aachen University, Germany
    index: 1
  - name: Scientific Information, German Aerospace Center (DLR), Germany
    index: 2
  - name: Instituto de Física de Cantabria (IFCA), Spain
    index: 3
  - name: Hamburger Sternwarte, Universität Hamburg, Germany
    index: 4
  - name: Departamento de Física, FCFM, Universidad de Chile, Chile
    index: 5
  - name: Departamento de Física, Facultad de Ciencias Exactas y Naturales, Universidad de Buenos Aires, Argentina
    index: 6
  - name: Instituto de Física de Buenos Aires (IFIBA), CONICET – Universidad de Buenos Aires, Argentina
    index: 7
  - name: 'Dipartimento di Fisica "E. Pancini", Università degli Studi di Napoli "Federico II", Italy'
    index: 8
  - name: INFN – Sezione di Napoli, Italy
    index: 9
  - name: Dipartimento di Fisica, Università degli Studi di Torino, Italy
    index: 10
  - name: INFN – Sezione di Torino, Italy
    index: 11
  - name: INAF – Osservatorio Astrofisico di Torino, Italy
    index: 12
  - name: Instituto de Astrofísica e Ciências do Espaço, Faculdade de Ciências, Universidade de Lisboa, Portugal
    index: 13
  - name: Institute of Cosmology and Gravitation, University of Portsmouth, United Kingdom
    index: 14
  - name: Center for Astrophysics and Cosmology, University of Nova Gorica, Slovenia
    index: 15
  - name: Department of Physics and Astronomy, University of the Western Cape, South Africa
    index: 16
  - name: Department of Physics, University of Genova, and INFN – Sezione di Genova, Italy
    index: 17
  - name: Instituto de Física Teórica, Spain
    index: 18
  - name: Institut de Recherche en Astrophysique et Planétologie, France
    index: 19
  - name: Université Saint Joseph, Lebanon
    index: 20
date: 23 November 2026
bibliography: paper.bib
---

# Summary


`cosmicjellyfish` is a Python package for Fisher-matrix and Monte Carlo forecasts of
cosmological surveys. It is the current version of `cosmicfishpie`, the Python successor of the
[CosmicFish](https://github.com/CosmicFish/CosmicFish) code [@Raveri2016], and has been used in about ten
publications since the Euclid forecast-validation programme [@Blanchard2020]. It computes the
observables of photometric galaxy clustering and weak lensing, spectroscopic galaxy
clustering, 21cm intensity mapping and the cosmic microwave background, and returns the
expected parameter constraints either as a Fisher matrix or as a posterior obtained by
nested sampling with [Nautilus](https://nautilus-sampler.readthedocs.io/en/latest/), both from a single configuration, so that going beyond the Gaussian approximation for a forecast, is only a matter of computing time. Theory predictions are supplied interchangeably by [CAMB](https://github.com/cmbant/CAMB),
[CLASS](https://github.com/lesgourg/class_public), [symbolic emulators](https://github.com/DeaglanBartlett/symbolic_pofk) [@Bartlett2024a; @Bartlett2024b; @Sui2025], or [jax-cosmo](https://github.com/DifferentiableUniverseInitiative/jax_cosmo); derivatives come from four finite-difference
schemes or from automatic differentiation with JAX [@Bradbury2018]. Both routes are validated against each other and against the reference
[MontePython](https://github.com/brinckmann/montepython_public) Euclid likelihoods [@Casas2024],
and a public dashboard compares CAMB and CLASS forecasts for 25 validation
cases. The survey specifications, solver settings, source revisions and chains behind
every number quoted here are released following the FAIR principles (findable, accessible, interoperable and reusable) [@Wilkinson2016]. The change of name from
`cosmicfishpie` to `cosmicjellyfish` was motivated by the transition to JAX and the availability of Monte Carlo methods.

# Statement of need


Forecasts shape the analysis of a survey long before the data arrives: they guide the
choice of scale cuts and redshift binning, the modelling of galaxy bias, intrinsic
alignments and baryonic feedback, and they set the expected sensitivity to the neutrino
mass [@Archidiacono2025] and to dynamical dark energy. Fisher forecasts are the standard tool because they
need tens of model evaluations instead of the $10^5$ to $10^6$ of a sampler, but they
rest on two assumptions: stable numerical derivatives of the observables, and a nearly
Gaussian posterior. Neither is routinely checked, and independent Fisher pipelines have
differed by 10% or more before their recipes were harmonised [@Blanchard2020].

`cosmicjellyfish` is built to make both checks inexpensive. The same observable can be
differentiated with four finite-difference schemes or by automatic differentiation, and
the same configuration can be sampled with the nested sampler Nautilus [@Lange2023].
Specifications for Euclid
[@Mellier2025], the SKA Observatory [@Bacon2020] and CMB experiments [@Planck2018] are
shipped, transcriptions of DESI [@DESI2016] and Rubin/LSST [@Ivezic2019] specifications
are available, and further surveys are added as YAML files. The intended users are
members of survey collaborations preparing forecast and validation studies, theorists who
need the sensitivity of a survey to a new model, and students, for whom the package is a
compact route from a power spectrum to a parameter constraint.

# State of the field

Several codes produce forecasts for large-scale structure surveys. `Augur` [@Rogozenski2026] is the Fisher tool of the LSST Dark Energy Science
Collaboration, built on CCL [@Chisari2019] and validated against CosmoSIS [@Zuntz2015]
and nested sampling, and `DerivKit` [@Sarcevic2026] provides stable numerical
derivatives independently of any cosmology code. General inference frameworks such as
MontePython [@Audren2013; @Brinckmann2019] and Cobaya [@Torrado2021] contain forecasting
likelihoods, but they are not Fisher codes. Differentiable libraries such as `jax-cosmo`
[@Campagne2023], CosmoPower-JAX [@Piras2023] and `cloelib` [@Bonici2026] provide
predictions and gradients, but not survey specifications, covariances or Fisher tools.

Three gaps remain. First, validation: the Fisher approach for spectroscopic surveys had
to be validated against MCMC [@YahiaCherif2021], and numerical derivatives were found to
dominate the instability of LSST-like forecasts [@Bhandari2021]. Second, CAMB and CLASS
have been compared at the level of power spectra [@Lesgourgues2011;
@LesgourguesTram2011], but rarely at the level of forecasts, where the accuracy settings
for massive neutrinos matter most [@Archidiacono2025]. Third, `jax-cosmo` compared
automatic and finite differences for two parameters [@Campagne2023]; a comparison for a
full survey with nuisance parameters, and against a non-differentiable implementation of
the same observable, was missing.

We extended `cosmicfishpie` instead of contributing to these frameworks for two reasons.
The checks above require exchanging one element of the forecast (theory, derivative,
or Fisher against posterior) while keeping all others fixed, so the survey
specification, observable, covariance, derivative and sampler must live in one code
base; this does not map onto a single likelihood or theory module of a general
framework. Second, the code is the reference implementation of published Euclid
forecasts [@Blanchard2020; @Casas2024; @Archidiacono2025; @Casas2026fR; @Frusciante2024], and those results had to stay
reproducible. Its Fisher recipes were validated against the MontePython likelihoods
[@Casas2024], which served as a basis for current Euclid likelihood codes such as
`cloelike` [@cloelike2026]; `cosmicjellyfish` is therefore an independent reference for
them.

# Software design

A forecast is a chain of exchangeable elements: theory backend, survey specification,
observable and covariance, derivative method, and Fisher assembly or likelihood. The
design choices below serve one aim: to change one element while keeping the others
fixed, so that a difference in the result can be attributed.

**One interface for several theory backends.** CAMB [@Lewis2000], CLASS [@Blas2011],
the SYREN emulators [@Bartlett2024a; @Bartlett2024b; @Sui2025], `jax-cosmo` and precomputed tables
are wrapped behind one `cosmo_functions` interface and selected with a single option.
The emulators reduce a survey forecast from minutes to seconds, at the cost of a restricted model space ($\Lambda$CDM and $w_0w_a$CDM with
massive neutrinos); the Boltzmann solvers remain the reference, with the precision
profiles of @Archidiacono2025 shipped as YAML files. New backends, such as the
differentiable DISCO-DJ [@Hahn2024] or CosmoPower-JAX [@Piras2023], only need to
implement this interface. Beyond $\Lambda$CDM, a modified-gravity module for Hu-Sawicki
$f(R)$ gravity loads the Winther fitting formula [@Winther2019] and the e-MANTIS emulator
[@SaezCasares2024] for the nonlinear boost of the power spectrum.

**Derivative methods replace only the Jacobian.** Finite differences (three-point,
four-point forward, polynomial fit and an adaptive scheme) and automatic differentiation
are implemented as derivative providers that return the Jacobian of an observable; the
covariance and the Fisher assembly are shared, so the two Fisher matrices differ only in
the derivative. Automatic differentiation needs the observables written in JAX, so
the photometric and spectroscopic observables exist in two implementations, one in NumPy
and one in JAX. The JAX version currently covers flat $\Lambda$CDM and $w_0w_a$CDM with
massless neutrinos, and the code raises an error outside this range instead of quietly
falling back to finite differences. We keep both on purpose: each one checks the other,
and their outputs are compared in continuous integration.

**Sampling without gradients.** The likelihoods reuse the observable and covariance
code, and they are sampled with Nautilus [@Lange2023], which needs no gradients and
therefore works with CAMB and CLASS. Other samplers, such as pocoMC [@Karamanis2022], and
gradient-based methods such as Hamiltonian Monte Carlo with the JAX backend, can be added
through the same likelihood interface.

**Configuration as data.** Survey specifications and solver settings are versioned YAML
files, and every run writes its full settings to a JSON file, so a forecast can be
rebuilt from its output. Every setting has a default that reproduces the Euclid
forecast-validation recipes [@Blanchard2020], so a user only has to specify the settings
that should differ from the Euclid setup, as in the example below. The former import
path `cosmicfishpie` is kept as a deprecated alias, so configurations of published
forecasts still run.

# Example

The examples use version 2.1.0, which is installed with
`pip install cosmicjellyfish==2.1.0` and archived on Zenodo (DOI for all versions:
[10.5281/zenodo.24593176](https://doi.org/10.5281/zenodo.24593176)). The `symbolic` backend used below also needs the
symbolic emulators of the linear and nonlinear power spectrum [@Bartlett2024a; @Bartlett2024b], which are not on PyPI:
`pip install git+https://github.com/DeaglanBartlett/symbolic_pofk.git`.
The defaults reproduce the pessimistic Euclid setup of @Blanchard2020, so a
photometric and a spectroscopic forecast, and their combination, take three statements:

```python
from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix

photo = FisherMatrix(options={"code": "symbolic", "feedback": 1},
                     observables=["WL", "GCph"], cosmoModel="LCDM").compute()
spectro = FisherMatrix(options={"code": "symbolic", "feedback": 1},
                       observables=["GCsp"], cosmoModel="LCDM").compute()
combined = photo + spectro  # nuisance parameters of both probes are kept
```

Both Fisher matrices together take about 15 s on a laptop with 16 cores.

<!-- [C16] NEW short paragraph replacing the autodiff listing (old 35 lines). The
autodiff route is one extra argument, which is itself the design point of [C11].
TESTED: with "code": "jaxcosmo" the default fiducial is refused (mnu = 0.06; the JAX
backend needs massless neutrinos), so the sentence says a massless fiducial is needed.
Notebook 07 shows the full comparison. -->

Replacing `"symbolic"` by `"camb"` or `"class"` repeats the forecast with a Boltzmann
solver. With `"jaxcosmo"` and a fiducial cosmology with massless neutrinos, passing
`derivative_provider=JaxAutodiffProvider()` to `FisherMatrix` replaces the finite
differences by automatic differentiation. A posterior for the same setup is obtained by
sampling the likelihood:

<!-- [C17] SIMPLIFIED listing (old: 2 blocks, 45 lines; now 12 lines). Dropped ell
sampling, results_dir, outroot, survey names, n_eff and verbose: all have defaults.
The sampler needs fiducial, priors and the four sampler settings shown.
On paper/joss-draft (no code patches) the options must also contain "survey_name"
(sampler.py reads options["survey_name"]) and "feedback" (read by FisherMatrix in the
main process), so the listing sets both. NOT re-run on this branch (Nautilus run
skipped on purpose); checked against the code only.
The plotting part (load chain + triangle plot) is gone: notebook 06 shows it. -->

```python
from cosmicjellyfish.likelihood import NautilusSampler

config = {
    "name": "wl_demo",
    "observables": ["WL"],
    "fiducial": {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67,
                 "ns": 0.96, "sigma8": 0.815584},
    "options": {"code": "symbolic", "cosmo_model": "LCDM",
                "survey_name": "Euclid", "feedback": 1},
    "priors": {"Omegam": [0.28, 0.36], "sigma8": [0.75, 0.87]},
    "sampler_settings": {"n_live": 500, "n_networks": 1, "n_batch": 50, "pool": 8},
}

if __name__ == "__main__":  # worker processes are spawned
    NautilusSampler(config).run()
```

# Research impact statement


**Publications.** As `cosmicfishpie`, the code has been used in about ten publications.
It produced the Euclid forecasts for the spectroscopic and photometric probes
[@Blanchard2020], and was then used in Euclid forecasts for $f(R)$ gravity
[@Casas2026fR], for scale-independent modifications of gravity [@Frusciante2024] and for
primordial features [@Ballardini2024], in the validation of the MontePython forecasting
likelihoods [@Casas2024], in the Euclid study of the sensitivity to neutrino parameters
[@Archidiacono2025], and in forecasts for radio and optical survey synergies with the SKA
Observatory [@Casas2023SKAO]. Earlier works with the code and its predecessors cover modified gravity and
dark energy [@Casas2017; @Frusciante2019; @Atayde2024], inflation and its connection to dark
energy [@Casas2018; @Casas2019; @Akrami2021], the anisotropic stress [@Sakr2025], the validation
of the Fisher approach for spectroscopic surveys [@YahiaCherif2021] and the impact of nonlinear
and baryonic feedback prescriptions on weak lensing [@Martinelli2021].

**Community.** The code is developed openly on GitHub by eleven contributors, with code
review through pull requests and continuous integration; the eleven authors of this paper
work at institutions in nine countries.

**Validation suite.** A public dashboard
(<https://www.santicasas.space/cosmicjellyfish/dashboard/>) compares CAMB and CLASS
forecasts for 25 cases: the photometric and spectroscopic Euclid probes in $\Lambda$CDM
and $w_0w_a$CDM, with and without massive neutrinos and $N_{\mathrm{eff}}$, following
@Casas2024 and @Archidiacono2025. The validation data are public and live in a Hugging Face
dataset (<https://huggingface.co/datasets/santicas/cjfp-data>). With the shipped high-precision profiles the two
solvers agree to better than 1% on all marginalised errors of the photometric benchmark.
A Euclid photometric forecast then takes 138 s with CAMB and 186 s with CLASS, and 30 s
and 111 s with the default profiles.

**Fisher matrices against posteriors.** The Fisher matrices of the code have been
validated in several earlier works, against independent Fisher codes [@Blanchard2020]
and against MCMC posteriors [@Casas2024; @Archidiacono2025], and the dashboard above
keeps tracking them. We repeat the comparison here with the built-in sampler. For Euclid
weak lensing (WL), spectroscopic clustering (GCsp) and their combination, with all
nuisance parameters sampled (5, 10 and 13 dimensions), the Fisher forecast and the
Nautilus posterior are almost indistinguishable (\autoref{fig:nautilus}). The marginalised
errors on $\Omega_{\mathrm{m}}$ and $\sigma_8$ agree to within 1.4%, 1.2% and 0.9%, which is
the size of the sampling noise itself: with about 2000 to 3000 effective samples per
chain, the noise on an error bar is about 1%. For these setups the Gaussian approximation
therefore holds, and the chains, which took 11 min, 10 min and 36 min on 64 workers, are
cheap enough to check it case by case instead of assuming it. The figure and these numbers
are produced by `scripts/paper-joss/reproduce_all.sh` (steps `nautilus` and `render`),
which runs the three chains and draws the comparison in about 70 min on one 64-worker
node.

![Fisher forecasts (dashed lines) and Nautilus posteriors (thin solid lines) for Euclid
weak lensing, spectroscopic clustering and their combination, with the symbolic backend
and all nuisance parameters marginalised in both cases. The two agree closely in every
case. Reproduced by
`scripts/paper-joss/reproduce_all.sh`.\label{fig:nautilus}](figures/fig3_fisher_vs_nautilus.png){ width=70% }

**Automatic differentiation.** Two Fisher matrices can differ for two reasons: the way
the derivatives are taken, and the way the observable is computed. To separate them, we
compute the Euclid photometric Fisher matrix (WL and photometric clustering, 17
parameters) three times: with automatic differentiation of the JAX observable, which has
no step size; with finite differences of the same JAX observable, which isolates the
derivative method; and with finite differences of the standard NumPy implementation, which
also tests the implementation of the observable itself (\autoref{fig:autodiff}). The
marginalised errors agree to 0.05% for the same JAX observable and to 0.4% for the NumPy
implementation, for all 17 parameters. The JAX and NumPy implementations are therefore
equivalent for this purpose, and the finite-difference steps are small enough not to bias
the errors, so any of the three routes can be used. These deviations are far below the 10%
or more by which independent Fisher pipelines have differed [@Blanchard2020]. The numbers
come from `scripts/paper-joss/autodiff_numbers.py` and the figure from
`scripts/paper-joss/plot_autodiff_ratios.py`, both run by the `autodiff` step of
`scripts/paper-joss/reproduce_all.sh` in a few minutes.

![Marginalised errors from finite differences relative to automatic differentiation for
the Euclid photometric forecast with the `jaxcosmo` backend, for the 17 free parameters
(cosmological, galaxy bias and intrinsic alignment): same JAX observable (dots) and
standard NumPy observable (squares). Reproduced by
`scripts/paper-joss/plot_autodiff_ratios.py`.\label{fig:autodiff}](figures/fig2_autodiff_ratios.png){ width=90% }

**Surveys and spectroscopic settings.** The code ships specifications for
Euclid[^euclid] [@Mellier2025], DESI[^desi] [@DESI2016], Rubin/LSST[^rubin]
[@Ivezic2019], the SKA Observatory[^skao] [@Bacon2020], MeerKLASS[^meerklass]
[@Santos2017], Planck[^planck] [@Planck2018], the Simons Observatory[^so] [@Ade2019]
and CMB-S4[^cmbs4] [@Abazajian2016]. Euclid is provided for the photometric and
spectroscopic probes, with the pessimistic and optimistic settings of @Blanchard2020 and
the data-release settings of @Archidiacono2025; the SKA Observatory for photometric and
spectroscopic clustering and for intensity mapping, summarized in @Casas2023SKAO; and DESI for the target samples of
its survey-validation programme [@DESI2024]. Spectroscopic clustering carries
more settings than the survey itself: the bias model (a linear bias per redshift bin,
parametrised directly or by its logarithm, or a scale-dependent bias), the shot noise,
the nonlinear velocity-dispersion damping, the redshift errors and the scale cuts, with
the corresponding nuisance parameters all free in the Fisher matrix.

[^euclid]: <https://www.euclid-ec.org>
[^desi]: <https://www.desi.lbl.gov>
[^rubin]: <https://rubinobservatory.org>
[^skao]: <https://www.skao.int>
[^meerklass]: <https://meerklass.github.io>
[^planck]: <https://www.cosmos.esa.int/web/planck>
[^so]: <https://simonsobservatory.org>
[^cmbs4]: <https://cmb-s4.org>

\autoref{fig:spectro} compares Euclid spectroscopic clustering, the
four DESI samples (BGS, LRG, ELG and QSO) and SKAO intensity mapping combined with the
DESI ELG sample, on a common $\Lambda$CDM fiducial and with all nuisance parameters marginalised.
The ranking reflects the specifications as transcribed and, for DESI, the assumption that
the four samples are independent, since they cover disjoint redshift ranges. The figure is
produced by `paper/scripts/fig5_spectro_survey_comparison.py` in about 2 min.

![Spectroscopic forecasts for Euclid GCsp, the four DESI samples (independent blocks
added) and SKAO intensity mapping with the DESI ELG sample (auto- and cross-spectra),
with all nuisance parameters marginalised. Left: marginalised errors on
$\Omega_{\mathrm{m}}$ and $\sigma_8$ in $\Lambda$CDM. Right: 68.27% and 95.45% contours
in the $w_0$-$w_a$ plane in $w_0w_a$CDM. Reproduced by
`paper/scripts/fig5_spectro_survey_comparison.py`.\label{fig:spectro}](figures/fig5_spectro_survey_comparison.png){ width=100% }

**Modified gravity.** The code also has a modified-gravity module for Hu-Sawicki
$f(R)$ gravity. The $f(R)$ background and linear growth come from a `hi_class`
[@Zumalacarregui2017] based solver (`frahiclassy`, which will be made available soon), and the nonlinear power
spectrum is the $\Lambda$CDM one multiplied by a boost, either the fitting formula of
@Winther2019 or the e-MANTIS emulator [@SaezCasares2024]. The implementation follows
closely the MontePython likelihood used for the $f(R)$ photometric analysis of
@Koyama2025
(<https://github.com/Sefa76/photometric_fofR/>).
On the grid in multipole and redshift of that likelihood, the boost agrees exactly (zero
difference) with it, for both models and for $10^{-7} \le |f_{R0}| \le 10^{-4}$. The table
shows the resulting Fisher errors for the pessimistic Euclid setting (WL, photometric
clustering and their cross-correlation) in the $f(R)$ model of @Casas2026fR, against the
Fisher forecast of that paper. The errors on $\Omega_\mathrm{m}$ and $n_\mathrm{s}$
agree within 2% and that on $\Omega_\mathrm{b}$ within 7%, while those on $h$ and
$\sigma_8$ are 10% to 22% larger here; in $\Lambda$CDM they coincide. We attribute this
partly to the sky fraction ($f_\mathrm{sky}=0.35$ here, 15000 deg$^2$ $\approx 0.364$
there) and to the scale-independent growth used here for the intrinsic alignment. The
error on $\log_{10}|f_{R0}|$ is 0.137 with the Winther boost and 0.128 with e-MANTIS,
against 0.143 in @Casas2026fR. The MCMC analysis of @Koyama2025 gives 0.11 for both
boosts, in a different parameter basis.

| Relative error (%) | $\Omega_\mathrm{m}$ | $\Omega_\mathrm{b}$ | $h$ | $n_\mathrm{s}$ | $\sigma_8$ | $\log_{10}\lvert f_{R0}\rvert$ |
|:-------------------|-----:|-----:|-----:|-----:|-----:|-----:|
| Table 2 of @Casas2026fR | 0.80 | 5.0 | 3.3 | 1.7 | 0.40 | 2.7 |
| `cosmicjellyfish`, Winther boost | 0.81 | 5.34 | 3.64 | 1.74 | 0.48 | 2.59 |
| `cosmicjellyfish`, e-MANTIS boost | 0.82 | 5.37 | 3.72 | 1.76 | 0.49 | 2.42 |

Table: Fisher forecast for the $f(R)$ model of @Casas2026fR, Euclid pessimistic setting, marginalised relative errors.

The configurations, source revisions and chains behind every number
in this section are public (<https://huggingface.co/datasets/santicas/cjfp-data>).

# AI usage disclosure

<!-- [C25] UPDATED. The manuscript paragraph now reflects what happened in this
conversation, including this restructuring. Model names: earlier sessions ran on
Claude Fable 5.2, this one on Claude Opus 5.5. The software part is still yours to
write. JOSS: tools and versions, where applied, and an affirmation of human review.
26 Nov: "to produce Figure 1" removed (that figure was dropped). -->

**[TODO, authors: state which coding assistants were used for the code, tests and
documentation, and for which parts. The repository ships an `AGENTS.md` guide for coding
agents.]**

For this manuscript, the authors wrote the first draft of the Summary, Statement of need,
State of the field, Software design and the validation text. Claude (Anthropic; models
Claude Fable 5.2 and Claude Opus 5.5) was used to correct the language, to restructure
the text to the JOSS guidelines, to propose and format references, to draft the Research
impact statement from the repository documentation, to test the code listings against the
repository. The authors reviewed, edited and validated all of
this content **[TODO: confirm]**.

# Acknowledgements

**[TODO: funding; computing time on JURECA at the Jülich Supercomputing Centre for the
Nautilus validation; acknowledgements to the CosmicFish authors and to the Euclid
Consortium colleagues involved in the forecast validation.]**

We thank Matteo Martinelli for initiating this project, the ideas, the motivation and for
bringing researchers together.

We thank Valeria Pettorino, Julien Lesgourgues, Nils Schöneberg and Maria Archidiacono for
scientific ideas, validation and discussions.

DS acknowledges support from the Fondecyt Regular project N.1251339 (ANID). ML is
supported by grant PIP 11220200100729CO CONICET and grant 20020170100129BA UBACYT.

# Author contributions

Author contributions follow the CRediT (Contributor Roles Taxonomy) [@Brand2015]. For
the authors who had not specified their roles, we derived a first proposal from the
all-contributors record of the repository (`code` as Software, `ideas` as Conceptualization,
`design` as Methodology, `research` as Investigation, `test`, `bug`, `review` and
`userTesting` as Validation, `data` as Data curation, `projectManagement` and `maintenance`
as Project administration, `mentoring` as Supervision, `doc`, `example` and `tutorial` as
Software, and `content` as Writing -- original draft).

- **S. Casas**: Conceptualization, Data curation, Investigation, Methodology, Project
  administration, Software, Supervision, Validation, Visualization, Writing -- original
  draft, Writing -- review & editing.
- **S. Pamuk**: Conceptualization, Investigation, Methodology, Software, Validation,
  Writing -- original draft.
- **V. M. Sabarish**: Conceptualization, Software.
- **Z. Sakr**: Conceptualization, Methodology, Software, Validation.
- **D. Sapone**: Conceptualization, Software, Supervision.
- **M. Leizerovich**: Conceptualization, Software (Hu-Sawicki $f(R)$ interface to
  hi_class-based codes, frahi_class, and the Winther and e-MANTIS nonlinear boosts),
  Validation.
- **N. Frusciante**: Software.
- **F. Pace**: Methodology, Software.
- **K. Koyama**: Conceptualization, Methodology, Supervision, Validation.
- **E. Bellini**: Conceptualization, Data curation, Software.
- **S. Camera**: Conceptualization, Methodology.
- **M. Raveri**: Conceptualization, Software (the original IST:Forecast code, started with
  M. Martinelli).

# References
