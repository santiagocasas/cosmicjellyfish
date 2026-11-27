# User guide

Reference-style guides for using `cosmicjellyfish` beyond the first forecast.

- {doc}`comprehensive_guide`: backends, observables, survey files and working with Fisher
  matrices.
- {doc}`derivatives`: the finite-difference schemes and how to choose one.
- {doc}`jaxcosmo`: the optional JAXcosmo backend, autodiff providers and comparison notebook.
- {doc}`modified_gravity_fR`: Hu-Sawicki f(R) forecasts with frahi_class and the Winther and
  e-MANTIS nonlinear boosts.
- {doc}`gcsp_intermediate`: the GCsp intermediate-parameter forecast and its Jacobian
  projection, with validation results.
- {doc}`likelihood_sampling`: posterior sampling with Nautilus, to check or replace the
  Fisher approximation.
- {doc}`cmb_benchmarks`: CMB observables, shipped experiment specifications and the
  smoke-test script.
- {doc}`survey_validation`: DESI, Rubin/LSST, SKAO and Planck-like forecasts, the migrated
  historical specifications and their validation against the independent reference recipes.

```{toctree}
:maxdepth: 1
:hidden:

comprehensive_guide
derivatives
jaxcosmo
modified_gravity_fR
gcsp_intermediate
likelihood_sampling
cmb_benchmarks
survey_validation
```
