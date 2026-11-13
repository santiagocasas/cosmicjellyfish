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
  - name: Matteo Martinelli
    affiliation: 3  # TODO: ORCID
  - name: Sefa Pamuk
    orcid: 0009-0004-0852-8624
    affiliation: 4
  - name: Sabarish V. M.
    affiliation: 5  # TODO: ORCID, name format
affiliations:
  - name: Theoretische Teilchenphysik und Kosmologie, RWTH Aachen University, Germany 
    index: 2
  - name: Scientific Information, German Aerospace Center (DLR), Germany
    index: 1
  - name: TODO affiliation of M. Martinelli
    index: 3
  - name: Universidad de Cantabria, Spain
    index: 4
  - name: TODO affiliation of Sabarish V. M.
    index: 5
date: 13 November 2026
bibliography: paper.bib
---

# Summary

`cosmicjellyfish` is a Python package for cosmological forecasts with Fisher-matrix and
Monte Carlo methods. Given a fiducial cosmology and a survey specification, it computes
the observables of galaxy clustering, weak lensing, intensity mapping and the cosmic
microwave background (CMB), and it returns the expected constraints on cosmological
parameters, either as a Fisher matrix or as a sampled posterior. Previously known as
`cosmicfishpie`, it has been used in about ten papers since the Euclid IST:F forecasts
[@Blanchard2020].

Three things are new in this release:

- **Speed.** The symbolic emulator [@Bartlett2024a; @Bartlett2024b; @Sui2025] gives
  Fisher matrices in about 5 seconds.
- **Differentiability.** The integration of JAX [@Bradbury2018] and of the `jax-cosmo`
  backend [@Campagne2023] allows for autodiff Fisher matrices.
- **Fisher and MCMC from the same settings.** This is version 2.0 also because MCMC
  forecasts can now be run with exactly the same settings as the Fisher forecast, which
  allows us to test contours that were not obvious before.

This is also, to our knowledge, the only project that provides a CAMB--CLASS validation
dashboard for many cosmological models in a FAIR way (Findable, Accessible,
Interoperable, Reusable) [@Wilkinson2016], with all the ini files, YAML files and a full
reproducibility pipeline. A companion DagsHub repository contains the validation data for
both Fisher matrices and MCMC chains.

The tentacles of the jellyfish in the logo stand for the chains, and the J in the name
stands for the new JAX compatibility.

# Statement of need

`cosmicjellyfish` is needed to forecast constraints for current and future probes, and
especially for their combinations, in an efficient, validated and reproducible way.

The code ships survey specifications for Euclid [@Mellier2025], SKAO [@Bacon2020] and
Planck-like CMB experiments [@Planck2018], and it can load user specifications for DESI
[@DESI2016] and LSST [@Ivezic2019]. These surveys are far from over: Euclid still has
about six years of observations ahead and LSST ten, and their cross-correlations have
barely been studied so far. A forecasting code of this kind will therefore remain useful
for a long time. Moreover, the step from here into real-data analysis is no longer a
large one.

The plan for the future is twofold:

- implement new probes, such as SPHEREx [@Dore2014], WST [@Mainieri2024] and other
  futuristic probes, or extensions such as SPT-10k **[TODO: cite SPT-10k]**;
- implement cross-correlations that have been studied in previous papers, such as dark
  sirens $\times$ Euclid GCph **[TODO: cite Giona's paper]**.

# State of the field

**Unvalidated forecasts.** Many forecasts in the literature, especially those based on
Fisher matrices, are not validated. We have seen in the Euclid IST:F paper
[@Blanchard2020] and in other works that independent pipelines differed by 10% or more,
and that it was hard to make them agree. The same lesson appears elsewhere: the Fisher
approach for spectroscopic surveys had to be validated against MCMC [@YahiaCherif2021],
numerical derivatives were shown to be a major source of instability in LSST-like
forecasts [@Bhandari2021], and the Euclid $\times$ CMB forecasts needed their own
cross-validation [@Ilic2022]. Recent tools address parts of the problem: `Augur`
[@Rogozenski2026] is the Fisher tool of LSST DESC, built on CCL [@Chisari2019] and
validated against CosmoSIS [@Zuntz2015] and nested sampling, and `DerivKit`
[@Sarcevic2026] provides stable numerical derivatives independently of any cosmology
code. General samplers such as MontePython [@Audren2013; @Brinckmann2019] and Cobaya
[@Torrado2021] can produce forecasts, but they are not Fisher codes.

**CAMB versus CLASS.** Beyond the original comparisons of the two codes at the level of
spectra [@Lesgourgues2011; @LesgourguesTram2011], almost no one has published validated
comparisons between CAMB [@Lewis2000] and CLASS [@Blas2011] at the level of forecasts,
especially in the neutrino sector [@Archidiacono2025]. `cosmicjellyfish` therefore also
acts as a translator between these two codes in a FAIR way, or at least on the road to
FAIR.

**Autodiff Fisher matrices.** `jax-cosmo` showcased autodiff Fisher matrices and compared
them with finite differences from CCL for two parameters [@Campagne2023], and
differentiable emulators have followed in recent years [@Piras2023]. Here we show, for a
full Euclid setup with nuisance parameters, that the autodiff Fisher matrix agrees well
with finite differences of the same observable, and also with a non-JAX implementation of
the observable.

**An independent testing ground.** Finally, we have implemented likelihoods that agree
with the direct Fisher method. The Fisher recipes were validated against the MontePython
likelihoods in 2023 [@Casas2024], and those likelihoods were in turn used as a backbone
of current likelihoods such as `cloelike` [@cloelike2026], which uses `cloelib`
[@Bonici2026]. `cosmicjellyfish` is therefore a very good way of having a fully
independent but modern code as a backdrop, testing ground and validation tool.

# Software design

The software is designed in a very modular way. The package layout follows the steps of a
forecast:

```text
cosmicjellyfish/
  cosmology/     background, power spectra, backends, nuisance models
  LSSsurvey/     photometric, spectroscopic and intensity-mapping probes
  CMBsurvey/     CMB observables and covariances
  fishermatrix/  FisherMatrix driver, finite-difference and autodiff derivatives
  likelihood/    photometric and spectroscopic likelihoods, Nautilus sampler
  analysis/      Fisher operations, plotting, chains on top of Fisher contours
  configs/       survey specifications and Boltzmann-solver profiles (YAML)
```

**Cosmology and backends.** The cosmology module computes the background and other
quantities, and it calls the different backends: CAMB [@Lewis2000] and CLASS [@Blas2011]
through their Python wrappers, SYREN (`symbolic_pofk`), a fast symbolic emulator
[@Bartlett2024a; @Bartlett2024b; @Sui2025], and `jax-cosmo`, a JAX implementation of the
cosmological background and perturbation quantities [@Campagne2023]. The backend is
chosen with a single option, `options["code"]`, which takes `"camb"`, `"class"`,
`"symbolic"`, `"jaxcosmo"` or `"external"` (precomputed tables). This design makes it
easy to implement other backends in the future, such as CosmoPower-JAX [@Piras2023] and
DISCO-DJ [@Hahn2024], which are also differentiable.

**Probes.** The photometric, spectroscopic and intensity-mapping probes are coded
independently in their own modules, and they work with any cosmological backend. The CMB
part can in principle also be used with several backends, although for the moment we
limit it to CAMB. In the near future we might integrate it with candl [@Balkenhol2024] to
get easier access to CMB likelihoods.

**Derivatives.** The derivatives are also coded in a modular way, so that the different
finite-difference methods (`3PT`, `4PT_FWD`, `POLY`, `STEM`) can be used independently,
and JAX autodiff can be used instead by passing a derivative provider to `FisherMatrix`.

**Likelihoods and sampling.** We also have independent likelihood modules with several
options, and modules that manage the runs with Nautilus [@Lange2023]. While Nautilus is
the standard sampler for now, this can easily be extended to samplers such as pocoMC
[@Karamanis2022] and others, and to gradient-based methods such as HMC that make use of
autodiff gradients, as was done in `jax-cosmo` [@Campagne2023].

**Analysis and plotting.** Finally, the code provides a set of tools for analysing and
plotting Fisher matrices: marginalising, combining, reparametrising and so on. Chains can
easily be plotted on top of Fisher contours, using ChainConsumer [@Hinton2016].

# Usage examples

## A Euclid photometric Fisher matrix, combined with spectroscopic

A simple Euclid photometric Fisher matrix, combined with the spectroscopic one and
marginalised over the nuisance parameters. With the symbolic backend the two forecasts
take a few seconds on a laptop. The result is shown in \autoref{fig:probes}.

```python
from cosmicjellyfish.analysis.fisher_operations import marginalise
from cosmicjellyfish.analysis.fishconsumer import make_triangle_plot
from cosmicjellyfish.fishermatrix import cosmicfish as cff

fiducial = {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67,
            "ns": 0.96, "sigma8": 0.815584}
freepars = {"Omegam": 0.01, "h": 0.01, "sigma8": 0.01}  # relative steps


def options(photo, spectro):
    return {
        "code": "symbolic",  # or "camb" / "class"
        "accuracy": 1,
        "nonlinear": True,
        "derivatives": "3PT",
        "results_dir": "results",
        "outroot": "example",
        "survey_name": "Euclid",
        "survey_name_photo": photo,
        "survey_name_spectro": spectro,
    }


photo = cff.FisherMatrix(
    fiducialpars=fiducial,
    freepars=freepars,
    options=options("Euclid-Photometric-ISTF-Pessimistic", False),
    observables=["WL", "GCph"],
    cosmoModel="LCDM",
    surveyName="Euclid",
).compute()

spectro = cff.FisherMatrix(
    fiducialpars=fiducial,
    freepars=freepars,
    options=options(False, "Euclid-Spectroscopic-ISTF-Pessimistic"),
    observables=["GCsp"],
    cosmoModel="LCDM",
    surveyName="Euclid",
).compute()

combined = photo + spectro  # nuisance parameters of both probes are kept
reduced = marginalise(combined, ["Omegam", "h", "sigma8"])
print(reduced.get_confidence_bounds())  # marginalised 1-sigma errors

make_triangle_plot(
    fishers=[spectro, photo, combined],
    fisher_labels=["GCsp", "WL+GCph", "WL+GCph+GCsp"],
    params=["Omegam", "h", "sigma8"],
    savefile="euclid_triangle.png",
)
```

Another experiment is added in the same way, by choosing another shipped specification
(for example `"SKAO-Spectroscopic-Redbook"`) and summing the resulting Fisher matrix.

![Marginalised constraints from Euclid spectroscopic clustering (GCsp), the photometric
probes (WL+GCph) and their combination, for flat $\Lambda$CDM with the IST:F pessimistic
specifications and the symbolic backend. This is the output of the example
above.\label{fig:probes}](figures/fig1_euclid_probes.png){ width=75% }

## A Nautilus chain that matches the Fisher matrix

A simple example running a chain with Nautilus from the same settings as the Fisher
forecast. The sampler writes the weighted chain, a resumable checkpoint and a metadata
file, which are then loaded and plotted on top of the Fisher contours.

```python
from cosmicjellyfish.likelihood import NautilusSampler

config = {
    "name": "wl_demo",
    "fiducial": fiducial,  # as above
    "observables": ["WL"],
    "options": {
        "code": "symbolic",
        "cosmo_model": "LCDM",
        "accuracy": 1,
        "nonlinear": True,
        "ell_sampling": 25,  # coarse grid for speed
        "results_dir": "results",
        "outroot": "wl_demo",
        "survey_name": "Euclid",
        "survey_name_photo": "Euclid-Photometric-ISTF-Pessimistic",
        "survey_name_spectro": False,
    },
    "priors": {"Omegam": [0.28, 0.36], "sigma8": [0.75, 0.87]},
    "sampler_settings": {"n_live": 500, "n_networks": 1, "n_batch": 50,
                         "pool": 8, "n_eff": 2000, "verbose": False},
}

if __name__ == "__main__":  # required for pool > 1: workers are spawned
    NautilusSampler(config).run()
```

```python
from cosmicjellyfish.analysis.fishconsumer import (
    load_Nautilus_chains_from_txt,
    make_triangle_plot,
)
from cosmicjellyfish.likelihood.sampler import load_chain_metadata

chain_file, sampled_fiducial, metadata, labels = load_chain_metadata(
    "chains/chains_wl_demo"
)
columns = open(chain_file).readline().lstrip("# ").split()[:-2]
chain = load_Nautilus_chains_from_txt(chain_file, columns)

make_triangle_plot(
    chains=[chain], chain_labels=["Nautilus"],
    fishers=[fisher], fisher_labels=["Fisher"],  # a WL Fisher matrix
    params=columns, truth_values=sampled_fiducial, param_labels=labels,
    savefile="wl_chain_vs_fisher.png",
)
```

A chain that samples only the cosmological parameters has to be compared with the Fisher
matrix at fixed nuisance parameters (`eliminate_parameters`); when the nuisance
parameters are sampled as well, it is compared with the marginalised one, as in
\autoref{fig:nautilus}.

## A JAX autodiff Fisher matrix against the standard one

Finally, a JAX autodiff Fisher matrix against the standard finite-difference one, with
the same `jaxcosmo` theory. This needs the optional extra,
`pip install "cosmicjellyfish[jaxcosmo]"`.

```python
from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.fishermatrix.jaxcosmo_derivatives import JaxAutodiffProvider

fiducial = {"10^9As": 2.1, "Omegam": 0.32, "Omegab": 0.05,
            "h": 0.67, "ns": 0.96, "mnu": 0.0}
freepars = {name: 0.01 for name in ("10^9As", "Omegam", "Omegab", "h")}


def forecast(provider, outroot):
    options = {  # a fresh dictionary for each forecast
        "code": "jaxcosmo",
        "accuracy": 1,
        "nonlinear": True,
        "derivatives": "3PT",
        "results_dir": "results",
        "outroot": outroot,
        "survey_name_photo": "Euclid-Photometric-ISTF-Pessimistic",
    }
    return FisherMatrix(
        fiducialpars=fiducial,
        freepars=freepars,
        options=options,
        observables=["GCph", "WL"],
        cosmoModel="LCDM",
        surveyName="Euclid",
        derivative_provider=provider,
    ).compute()


fisher_ad = forecast(JaxAutodiffProvider(), "photo_ad")  # autodiff (jax.jacfwd)
fisher_fd = forecast(None, "photo_fd")  # standard finite differences

print(fisher_ad.get_confidence_bounds() / fisher_fd.get_confidence_bounds())
```

For this setup the marginalised errors of the two routes agree to better than 0.4% for
all 17 cosmological and nuisance parameters (\autoref{fig:autodiff}). When the finite
differences are taken on the same JAX observable (`JaxFiniteDifferenceProvider`), the
agreement improves to better than 0.05%, and the two Fisher matrices differ by
$1.8\times10^{-5}$ in $\max|\Delta F|/\max|F|$. The remaining difference is therefore due
to the two implementations of the observable and not to the derivative method.

![Marginalised errors from finite differences relative to those from automatic
differentiation, for the Euclid WL+GCph forecast with the `jaxcosmo` backend. Filled
circles: finite differences of the same JAX observable. Open squares: finite differences
of the standard NumPy observable.\label{fig:autodiff}](figures/fig2_autodiff_ratios.png)

# Validation and performance

**Validation.** The CAMB--CLASS validation and the MontePython validation are documented
in the validation dashboard (<https://www.santicasas.space/cosmicjellyfish/dashboard/>),
with all the scripts and results in the data folders of the DagsHub repository
(<https://dagshub.com/santiagocasas/cjfp-data>). The suite covers 25 cases: photometric
and spectroscopic Euclid probes for $\Lambda$CDM and $w_0w_a$CDM, with and without
massive neutrinos and $N_{\mathrm{eff}}$, following the settings of @Casas2024 and
@Archidiacono2025. `cosmicjellyfish` itself (formerly `cosmicfishpie`) was validated in
several Euclid papers and beyond [@Blanchard2020; @Casas2024; @Archidiacono2025].

**Performance.** For a Euclid photometric forecast, the default profiles take about 30 s
(CAMB) and 111 s (CLASS), against 138 s and 186 s for the high-precision profiles of
@Archidiacono2025. The performance has been improving over the years. With the symbolic
module we now obtain Fisher matrices in a few seconds, also for models such as
$w_0w_a$CDM: with seven cosmological parameters and all nuisance parameters, the WL+GCph
Fisher matrix (20 parameters) takes about 8 s and the GCsp one (15 parameters) about
2.5 s **[TODO: measured on two cores of a cloud VM; replace by your own hardware]**. With
CAMB and CLASS we provide several levels of accuracy and precision, and the Fisher
matrices take less or more time depending on that.

**Chains against Fisher matrices.** We have also validated our chains against our own
Fisher matrices and shown that they agree (\autoref{fig:nautilus}). For Euclid WL, GCsp
and their combination, with all nuisance parameters sampled, the marginalised Nautilus
errors on $\Omega_{\mathrm{m}}$ and $\sigma_8$ are within 5%, 0.4% and 1.3% of the Fisher
ones, respectively, and the posterior means lie within 0.1$\sigma$ of the fiducial
values.

The timings of these runs are interesting in themselves. With the symbolic backend, 64
Nautilus workers on JURECA, `n_live=500` and a target of 2000 effective samples, the WL
chain (5 sampled dimensions) took 17 minutes, the GCsp chain (10 dimensions) 22 minutes
and the joint WL+GCsp chain (13 dimensions) 1 hour and 45 minutes. A full posterior for
the Euclid primary probes, including nuisance parameters, is thus obtained in about 18,
24 and 112 core-hours, respectively, while the corresponding Fisher matrices take
seconds. This makes it affordable to check the Gaussian approximation case by case,
instead of assuming it.

![Fisher forecasts (dark, thick lines) against Nautilus posteriors (light, thin lines)
for Euclid weak lensing, spectroscopic clustering and their combination, with the
symbolic backend and all nuisance parameters marginalised in both
cases.\label{fig:nautilus}](figures/fig3_fisher_vs_nautilus.png){ width=75% }

# Research impact statement

As `cosmicfishpie`, the code has been used in about ten publications. It started with
the Euclid IST:F forecasts for the spectroscopic and photometric probes [@Blanchard2020],
and it was then used in several Euclid papers forecasting extended models, such as $f(R)$
gravity [@Casas2026fR] and scalar-field and other modified-gravity models
[@Frusciante2024], and models of inflation [@Ballardini2024] **[TODO: confirm that these
three are the papers you mean]**. It served in the paper validating the MontePython
likelihoods [@Casas2024] and in the Euclid paper on the sensitivity to neutrino
cosmology, which used MontePython and `cosmicfishpie` together [@Archidiacono2025]. It
was also used in the papers on radio $\times$ optical probes with SKAO [@Casas2023SKAO]
and in a few other works **[TODO: cite the remaining papers]**.

The Boltzmann-solver precision profiles validated in those works are shipped with the
package, and the validation dashboard, the posterior chains and the cluster workflows are
public, so that every comparison quoted here can be reproduced from a recorded source
revision.

# Documentation

The documentation (<https://www.santicasas.space/cosmicjellyfish/docs/>) contains an
installation guide, a first forecast, a user guide on backends, observables, derivative
methods and likelihood sampling, the validation reports and an API reference. Eight
tutorial notebooks in the repository cover the cosmology interface, spectroscopic and
photometric forecasts, the CMB, Fisher post-processing, Nautilus sampling, autodiff
against finite differences, and forecasts in intermediate parameters. A migration guide
describes the change from `cosmicfishpie`, whose import path keeps working as a
deprecated alias.

# Availability

`cosmicjellyfish` is released under the Apache 2.0 licence. The source code is hosted at
<https://github.com/santiagocasas/cosmicjellyfish> and the package is installed with
`pip install cosmicjellyfish` for Python 3.10 to 3.12. Validation data and workflows are
available at <https://dagshub.com/santiagocasas/cjfp-data>.

# AI usage disclosure

**[TODO: to be completed and confirmed by the authors. JOSS asks for the tools and
versions, where they were applied, and a statement of human verification.]**

*Software and documentation:* **[TODO: state which coding assistants were used for the
code, tests and documentation, and for which parts. The repository ships an `AGENTS.md`
guide for coding agents.]**

*This manuscript:* the authors wrote the first draft of the Summary, Statement of need,
State of the field, Software design, Usage examples and Validation sections. Claude
(Anthropic) **[TODO: model version]** was then used to correct the language and organise
that text, to propose and format references, to draft the Research impact, Documentation
and Availability sections from the repository documentation, to test the code listings
against the repository, and to produce Figures 1 and 2. The authors reviewed, edited and
validated all of this content **[TODO: confirm]**.

# Acknowledgements

**[TODO: funding; computing time on JURECA at the Jülich Supercomputing Centre for the
Nautilus validation; acknowledgements to the CosmicFish authors and to the Euclid
Consortium colleagues involved in the forecast validation.]**

# Author contributions

Following the all-contributors record of the repository: S. Casas leads and maintains the
project and contributed to research, validation data, tests, tutorials and documentation.
S. Pamuk contributed code, design, tests, examples, documentation and code review.
M. Martinelli contributed code and design. Sabarish V. M. contributed code and
documentation. **[TODO: expand as needed.]**

# References
