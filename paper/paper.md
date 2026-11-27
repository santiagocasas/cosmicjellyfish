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

<!-- [C1] REPLACED (27 Nov) by the author's own summary text. The previous version
explained what a forecast is for a non-specialist reader and cited Bradbury2018,
Bartlett2024a/b, Sui2025 and Raveri2016. Those five citations are back in the new text
(27 Nov: Raveri2016 attached to a short clause "the Python successor of the CosmicFish
code", which I added). CHECK: the text has no sentence for non-specialists. The last sentence says the name change was motivated by the
transition to JAX (replaces "the J stands for JAX"). -->

`cosmicjellyfish` is a Python package for Fisher-matrix and Monte Carlo forecasts of
cosmological surveys, and the current version of `cosmicfishpie`, the Python successor of the
[CosmicFish](https://github.com/CosmicFish/CosmicFish) code [@Raveri2016], which has been used in about ten publications since the
Euclid forecast-validation programme [@Blanchard2020]. It computes the
observables of photometric galaxy clustering and weak lensing, spectroscopic galaxy
clustering, 21cm intensity mapping and the cosmic microwave background, and returns the
expected parameter constraints either as a Fisher matrix or as a posterior obtained by
nested sampling with [Nautilus](https://nautilus-sampler.readthedocs.io/en/latest/), both from a single configuration, so that the Gaussian approximation can
be tested rather than assumed. Theory predictions are supplied interchangeably by [CAMB](https://github.com/cmbant/CAMB),
[CLASS](https://github.com/lesgourg/class_public), [symbolic emulators](https://github.com/DeaglanBartlett/symbolic_pofk) [@Bartlett2024a; @Bartlett2024b; @Sui2025] that return a full
survey forecast in seconds, or [jax-cosmo](https://github.com/DifferentiableUniverseInitiative/jax_cosmo); derivatives come from four finite-difference
schemes or from automatic differentiation with JAX [@Bradbury2018]. Both routes are validated against each other and against the reference
[MontePython](https://github.com/brinckmann/montepython_public) Euclid likelihoods [@Casas2024],
and a public dashboard compares CAMB and CLASS forecasts for 25 validation
cases. The survey specifications, solver settings, source revisions and chains behind
every number quoted here are released following the FAIR principles (findable, accessible, interoperable and reusable) [@Wilkinson2016]. The change of name from
`cosmicfishpie` to `cosmicjellyfish` was motivated by the transition to JAX.

# Statement of need

<!-- [C3] REWORDED. Your opening ("cosmicjellyfish is needed to forecast constraints
...") was circular. Now it starts from the problem: forecasts drive survey decisions,
and Fisher forecasts rest on two assumptions that are rarely checked. The 10% figure is
your own, moved here from State of the field. The science list (neutrino mass, dark
energy, baryonic feedback) follows your usual framing. -->

Forecasts shape the analysis of a survey long before the data arrive: they guide the
choice of scale cuts and redshift binning, the modelling of galaxy bias, intrinsic
alignments and baryonic feedback, and they set the expected sensitivity to the neutrino
mass and to dynamical dark energy. Fisher forecasts are the standard tool because they
need tens of model evaluations instead of the $10^5$ to $10^6$ of a sampler, but they
rest on two assumptions: stable numerical derivatives of the observables, and a nearly
Gaussian posterior. Neither is routinely checked, and independent Fisher pipelines have
differed by 10% or more before their recipes were harmonised [@Blanchard2020].

<!-- [C4] NEW (facts from the repository). JOSS requires the target audience to be
named; the old draft did not. The survey list is your text. The list of backends is not
repeated here (it is in Software design, [C10]), to save words. Check the survey list: the
default_survey_specifications folder ships Euclid, Planck, Simons Observatory and
CMB-S4 (+PlanckLowEll); SKAO is in other_survey_specifications; DESI and Rubin/LSST
are only in the unmerged validation scripts (see [C24]). I wrote "transcriptions" for
those, as in your co-authors' text. -->

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

<!-- [C5] CUT to stay under 1750 words. JOSS judges impact on evidence, not plans, so the
roadmap is the cheapest paragraph to drop. Your text, ready to restore (51 words):

"Euclid will observe for several more years and Rubin for ten, and the combination of
their probes with each other, with radio surveys and with the CMB has barely been
explored. Planned extensions are specifications for SPHEREx [@Dore2014] and WST
[@Mainieri2024], and cross-correlations with gravitational-wave dark sirens
[TODO: cite]."

Also CUT earlier: "A forecasting code of this kind will therefore remain useful for a
long time. Moreover, the step from here into real-data analysis is no longer a large
one." (unsupported), and the SPT-10k bullet (no citation). If you restore the roadmap,
dark sirens still need Giona's paper (other_survey_specifications/Euclid-Photometric-
ISTF-GW.yaml looks related). Dore2014 and Mainieri2024 stay in paper.bib; unused entries
are not printed. -->

# State of the field

<!-- [C6] NEW + MOVED. JOSS asks how the software "compares to other commonly-used
packages". Your draft named Augur, DerivKit, MontePython and Cobaya inside the
"Unvalidated forecasts" paragraph; they are now one paragraph of their own, with the
differentiable libraries from your "Autodiff" paragraph. The original CosmicFish is
cited in the Summary [C2] instead of here, to save words.
NEW: the last sentence (what the theory libraries do not provide). -->

Several codes produce forecasts for large-scale structure surveys. `Augur` [@Rogozenski2026] is the Fisher tool of the LSST Dark Energy Science
Collaboration, built on CCL [@Chisari2019] and validated against CosmoSIS [@Zuntz2015]
and nested sampling, and `DerivKit` [@Sarcevic2026] provides stable numerical
derivatives independently of any cosmology code. General inference frameworks such as
MontePython [@Audren2013; @Brinckmann2019] and Cobaya [@Torrado2021] contain forecasting
likelihoods, but they are not Fisher codes. Differentiable libraries such as `jax-cosmo`
[@Campagne2023], CosmoPower-JAX [@Piras2023] and `cloelib` [@Bonici2026] provide
predictions and gradients, but not survey specifications, covariances or Fisher tools.

<!-- [C7] REWORDED. Your three points "Unvalidated forecasts", "CAMB versus CLASS" and
"Autodiff Fisher matrices", compressed into one paragraph of three gaps.
CUT: "almost no one has published validated comparisons" -> "rarely at the level of
forecasts" (provable, and it is what you meant).
CUT: "cosmicjellyfish therefore also acts as a translator between these two codes in a
FAIR way, or at least on the road to FAIR." The translator idea now lives in Research
impact [C24], with what is actually FAIR about it.
CUT: the Euclid x CMB example [@Ilic2022]; restore if you want three examples. -->

Three gaps remain. First, validation: the Fisher approach for spectroscopic surveys had
to be validated against MCMC [@YahiaCherif2021], and numerical derivatives were found to
dominate the instability of LSST-like forecasts [@Bhandari2021]. Second, CAMB and CLASS
have been compared at the level of power spectra [@Lesgourgues2011;
@LesgourguesTram2011], but rarely at the level of forecasts, where the accuracy settings
for massive neutrinos matter most [@Archidiacono2025]. Third, `jax-cosmo` compared
automatic and finite differences for two parameters [@Campagne2023]; a comparison for a
full survey with nuisance parameters, and against a non-differentiable implementation of
the same observable, was missing.

<!-- [C8] NEW. JOSS: "If related tools exist, provide a clear build vs. contribute
justification". The two reasons are the ones you gave me (whole-chain scope, backward
compatibility with published Euclid results). The last two sentences are your
"independent testing ground" paragraph, shortened.
CUT: "is therefore a very good way of having a fully independent, but modern code as a
backdrop and testing ground and validation" -> "an independent reference".
CHECK: "served as a basis for cloelike". Your words were "used as a backbone of current
likelihoods such as cloelike". Make sure the cloelike authors agree with the wording. -->

We extended `cosmicfishpie` instead of contributing to these frameworks for two reasons.
The checks above require exchanging one element of the forecast (theory, derivative,
or Fisher against posterior) while keeping all others fixed, so the survey
specification, observable, covariance, derivative and sampler must live in one code
base; this does not map onto a single likelihood or theory module of a general
framework. Second, the code is the reference implementation of published Euclid
forecasts [@Blanchard2020; @Casas2024; @Archidiacono2025], and those results had to stay
reproducible. Its Fisher recipes were validated against the MontePython likelihoods
[@Casas2024], which served as a basis for current Euclid likelihood codes such as
`cloelike` [@cloelike2026]; `cosmicjellyfish` is therefore an independent reference for
them.

# Software design

<!-- [C9] NEW framing. JOSS asks for "the trade-offs you weighed" and warns against "a
superficial code structure description". The directory tree and "designed in a very
modular way" are gone. Every paragraph below now says: what we chose, what it costs,
why. The facts are your text from the old Software design section; the trade-offs are
the ones I listed in the review and you approved.
CUT: the directory tree code block (about 60 words of listing). -->

A forecast is a chain of exchangeable elements: theory backend, survey specification,
observable and covariance, derivative method, and Fisher assembly or likelihood. The
design choices below serve one aim: to change one element while keeping the others
fixed, so that a difference in the result can be attributed.

<!-- [C10] REWORDED (your "Cosmology and backends"). NEW: the trade-off sentence about
the emulator model range, and the reference to the shipped precision profiles.
CUT: "This design makes it easy to implement other backends" -> "need only implement
this interface" ("easy" is a claim reviewers test).
CHECK: symbolic-emulator model range. I wrote LCDM, w0waCDM and massive neutrinos
(SYREN-new). Correct me if it is narrower. -->

**One interface for several theory backends.** CAMB [@Lewis2000], CLASS [@Blas2011],
the SYREN emulators, `jax-cosmo` and precomputed tables are wrapped behind one
`cosmo_functions` interface and selected with a single option. The emulators reduce a survey forecast from minutes to
seconds, at the cost of a restricted model space ($\Lambda$CDM and $w_0w_a$CDM with
massive neutrinos); the Boltzmann solvers remain the reference, with the precision
profiles of @Archidiacono2025 shipped as YAML files. New backends, such as the
differentiable DISCO-DJ [@Hahn2024] or CosmoPower-JAX [@Piras2023], only need to
implement this interface.

<!-- [C11] REWORDED (your "Derivatives"). NEW: why only the Jacobian is replaced, what the
JAX route costs (a second implementation, a narrower model range), and that the
duplication is turned into a CI test. The facts are from docs/source/jaxcosmo.md. -->

**Derivative methods replace only the Jacobian.** Finite differences (three-point,
four-point forward, polynomial fit and an adaptive scheme) and automatic differentiation
are implemented as derivative providers that return the Jacobian of an observable; the
covariance and the Fisher assembly are shared, so the two Fisher matrices differ only in
the derivative. The price is a second, JAX-native implementation of the photometric and spectroscopic observables,
limited for now to flat $\Lambda$CDM and $w_0w_a$CDM with massless neutrinos; outside
this range the code raises an error instead of falling back silently. Keeping both
implementations turns the duplication into a test: their outputs are compared in
continuous integration.

<!-- [C12] REWORDED (your "Likelihoods and sampling"). NEW: why Nautilus (no gradients,
so it works with CAMB/CLASS). Kept: pocoMC and HMC as extensions.
CUT: "this can easily be extended" -> "can be added through the same likelihood
interface". -->

**Sampling without gradients.** The likelihoods reuse the observable and covariance
code, and they are sampled with Nautilus [@Lange2023], which needs no gradients and
therefore works with CAMB and CLASS. Other samplers, such as pocoMC [@Karamanis2022], and
gradient-based methods such as Hamiltonian Monte Carlo with the JAX backend, can be added
through the same likelihood interface.

<!-- [C13] NEW (facts verified in the code: YAML specs in cosmicjellyfish/configs, the
JSON settings export in FisherMatrix, the defaults in configs/config.py, and the
cosmicfishpie alias described in the migration guide). This is your "open science,
reproducibility" theme, stated as a design decision. -->

**Configuration as data.** Survey specifications and solver settings are versioned YAML
files, and every run writes its full settings to a JSON file, so a forecast can be
rebuilt from its output. The defaults reproduce the Euclid forecast-validation recipes
[@Blanchard2020], so a forecast only states what differs from them. The former import
path `cosmicfishpie` is kept as a deprecated alias, so configurations of published
forecasts still run.

<!-- [C14] CUT to save words (your "Analysis and plotting" paragraph): "Fisher matrices
are objects that can be added, marginalised, reparametrised and plotted together with
chains through ChainConsumer [@Hinton2016]." It is a feature list rather than a design
trade-off. Restore it if you have words left; ChainConsumer is then cited again. -->

# Example

<!-- [C15] REWORDED + simplified code, as you asked. The listing now relies on the
defaults (Euclid IST:F pessimistic photometric and spectroscopic specifications,
fiducial cosmology, free parameters for the chosen model, 3-point derivatives,
nonlinear corrections). TESTED (26 Nov 2026) on paper/joss-draft without code changes:
"feedback" must be in options (cosmicfish.py reads options["feedback"]), so the listing
sets it. Both forecasts take 12 s on a laptop.
Figure of the Euclid probes (old Fig 1, fig1_euclid_probes.png) DROPPED on 26 Nov:
one ellipse figure (Fisher vs Nautilus) is enough. -->

<!-- [C15b] NEW (27 Nov): install line. Verified in a clean Python 3.12 venv with
`uv pip install cosmicjellyfish==2.1.0 git+https://github.com/DeaglanBartlett/symbolic_pofk.git`:
the first listing below runs unchanged in 14 s. symbolic_pofk is not on PyPI (PyPI rejects
direct-URL dependencies), hence the second package. The second listing (Nautilus) was not run
against the wheel here; it was run on the cluster from a source checkout. -->

The examples use version 2.1.0, which is installed with
`pip install cosmicjellyfish==2.1.0`. The `symbolic` backend used below also needs the
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

<!-- [C19] MOVED from the old Summary and the old Research impact. JOSS: "evidence of
realized impact (publications, external use, integrations)". Unchanged facts; I only
removed the duplicate mention of the IST:F paper.
TODO (still open from last time): confirm that Casas2026fR, Frusciante2024 and
Ballardini2024 are the papers you mean, and cite the "few other works". -->

**Publications.** As `cosmicfishpie`, the code has been used in about ten publications.
It produced the Euclid forecasts for the spectroscopic and photometric probes
[@Blanchard2020], and was then used in Euclid forecasts for $f(R)$ gravity
[@Casas2026fR], for scale-independent modifications of gravity [@Frusciante2024] and for
primordial features [@Ballardini2024], in the validation of the MontePython forecasting
likelihoods [@Casas2024], in the Euclid study of the sensitivity to neutrino parameters
[@Archidiacono2025], and in forecasts for radio and optical survey synergies with the SKA
Observatory [@Casas2023SKAO] **[TODO: cite the remaining works]**.

<!-- [C20] NEW. JOSS reviewers check "multiple contributors" and "community engagement"
(pre-review screening gate). Facts (26 Nov 2026): 11 entries in .all-contributorsrc on
main, 11 paper authors; nine countries from the affiliation list = Germany, Spain, Chile,
Argentina, Italy, Portugal, UK, Slovenia, South Africa. Update if authors change. -->

**Community.** The code is developed openly on GitHub by eleven contributors, with code
review through pull requests and continuous integration; the eleven authors of this paper
work at institutions in nine countries.

<!-- [C21] MOVED + shortened (old "Validation" paragraph). The CAMB-CLASS numbers are from
docs/source/default_vs_hp_profiles.md ("CLASS and CAMB agree to below about 0.9% on all
..." with the high-precision profiles), which I quote as "below 1%".
CUT: "cosmicjellyfish itself (formerly cosmicfishpie) was validated in several Euclid
papers and beyond" (already said in [C19]). -->

**Validation suite.** A public dashboard
(<https://www.santicasas.space/cosmicjellyfish/dashboard/>) compares CAMB and CLASS
forecasts for 25 cases: the photometric and spectroscopic Euclid probes in $\Lambda$CDM
and $w_0w_a$CDM, with and without massive neutrinos and $N_{\mathrm{eff}}$, following
@Casas2024 and @Archidiacono2025. The validation data are public and live in a Hugging Face
dataset (<https://huggingface.co/datasets/santicas/cjfp-data>). With the shipped high-precision profiles the two
solvers agree to better than 1% on all marginalised errors of the photometric benchmark.
A Euclid photometric forecast then takes 138 s with CAMB and 186 s with CLASS, and 30 s
and 111 s with the default profiles; the two forecasts of the example above take about
20 s together with the symbolic backend on two CPU cores.

<!-- [C22] MOVED + shortened (old "Performance" paragraph), merged into the paragraph
above [C21] to save a heading.
CUT: "The performance has been improving over the years." (empty).
CUT: the w0waCDM symbolic timing with the TODO about cloud cores; replaced by the timing
I measured for the listing in [C15]. TODO: re-measure on your laptop and replace.
The CAMB/CLASS timings are from docs/source/default_vs_hp_profiles.md (default profiles
4.6x faster for CAMB, 1.7x for CLASS). -->


<!-- [C23] MOVED + shortened (old "Chains against Fisher matrices" and the timings
paragraph you liked). Numbers from docs/source/likelihood_validation.md.
CUT: "We have also validated our chains against our own Fisher matrices and shown that
they agree" (the numbers say it).
CUT: the core-hour conversion (18, 24 and 112 core-hours); restore if you want it.
The autodiff numbers replace the dropped Figure 2 (my run of notebook 07's setup;
0.38% NumPy observable, 0.05% and 1.8e-5 same JAX observable). -->

<!-- [C23c] UPDATED (27 Nov) with the reproduction run of scripts/paper-joss on
paper/joss-draft @ b50f5b7 (36-core Xeon Gold 6140 node, 64 workers, 70 min for all five
steps): max sigma deviation 1.43% (WL), 1.16% (GCsp), 0.94% (WL+GCsp); chains 11, 10 and
36 min; autodiff 0.0477% and 0.376%. The earlier numbers (5%, 0.4%, 1.3%; 17 min, 22 min,
1 h 45 min) come from the first run in docs/source/likelihood_validation.md, whose WL
reference errors were ~3 sigma high; the 0.4% of GCsp was a low draw (ESS 2836 gives a
sampling error of ~1.3%). The figure file in paper/figures is still the one of the
first run: replace it with scripts/paper-joss/output/fig_fisher_vs_nautilus.png if you
want figure and text to come from the same run. -->

<!-- [C23b] NEW (26 Nov): one ellipse figure only; the text says explicitly that the
Fisher matrices were validated before. CHECK the citations: Blanchard2020 (code
comparison), Casas2024 (Fisher vs MontePython MCMC), Archidiacono2025 (Fisher vs MCMC
for neutrinos); add or remove as appropriate. -->

**Fisher matrices against posteriors.** The Fisher matrices of the code have been
validated in several earlier works, against independent Fisher codes [@Blanchard2020]
and against MCMC posteriors [@Casas2024; @Archidiacono2025], and the dashboard above
keeps tracking them. We repeat the comparison here with the built-in sampler. For Euclid
weak lensing, spectroscopic clustering and their combination, with all nuisance parameters sampled (5, 10 and 13 dimensions),
the marginalised Nautilus errors on $\Omega_{\mathrm{m}}$ and $\sigma_8$ agree with the
Fisher errors to within 1.4%, 1.2% and 0.9% (\autoref{fig:nautilus}). With about 2000
to 3000 effective samples per chain, the sampling noise on an error bar is itself about
1%. The chains took 11 min, 10 min and 36 min on 64 workers: affordable enough to check
the Gaussian approximation case by case instead of assuming it. For the
photometric probes, the automatic-differentiation errors agree with finite differences
of the same JAX observable to 0.05%, and with the standard NumPy implementation to 0.4%,
for all 17 parameters. The figure, these numbers, the timings and the two code listings
above are regenerated from a clean checkout by `scripts/paper-joss/reproduce_all.sh`,
in about 70 min on one 64-worker node.

![Fisher forecasts (dark, thick lines) against Nautilus posteriors (light, thin lines)
for Euclid weak lensing, spectroscopic clustering and their combination, with the
symbolic backend and all nuisance parameters marginalised in both
cases.\label{fig:nautilus}](figures/fig3_fisher_vs_nautilus.png){ width=70% }

<!-- [C24] SHORTENED from your co-authors' "Cross-survey validation" paragraph (190 words
-> 75). All claims kept: transcription of DESI, Rubin/LSST and SKAO specs from
Casas2023SKAO, machine-precision agreement of the algebra-level ingredients, <1.5%
SKAO spectra, common GR fiducial, ranking reflects specifications. Caption shortened
from 120 words to 50.
CUT: the sentence on photometric spectra not being re-compared, and the "amplitude
offset consistent with (but not uniquely attributable to) the modified-gravity
fiducial". Both are honest caveats; they belong in the validation docs, not the paper.
RESTORED (26 Nov, merge into paper.md): "algebra-level" and "shapes of" the SKAO spectra,
so the shortened sentence does not claim more than the original (an amplitude offset
remains, and the photometric spectra were not re-compared).
26 Nov: survey comparison figure (fig4) DROPPED, one ellipse figure is enough; the
fig4 reproducibility blocker is gone with it. The sentence on consistent constraints
across surveys went with the figure.
NEW: the last sentence is your "translator ... in a FAIR way" idea [C7], stated as what
is concretely open: configs, source revisions, chains.
CUT: the documentation URL and "eight tutorial notebooks" (old Documentation section).
JOSS prints the repository link in the paper margin, and the README points to the docs.
Restore it if you want it (about 15 words). -->

**Cross-survey validation.** To check that the pipeline is not tied to Euclid, the DESI,
Rubin/LSST and SKAO specifications of @Casas2023SKAO were transcribed into the current
format and compared with an independent re-implementation of the original recipes: all
algebra-level ingredients agree to machine precision, and the shapes of the SKAO power
spectra to better than 1.5%.
The configurations, source revisions and chains behind every number
in this section are public (<https://dagshub.com/santiagocasas/cjfp-data>).

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
