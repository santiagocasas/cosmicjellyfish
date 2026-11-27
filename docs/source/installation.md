# Installation

`cosmicjellyfish` supports Python `>=3.10,<3.13`.

## Install from PyPI

```bash
pip install cosmicjellyfish
```

`camb` and `classy` (the CLASS Python wrapper) are required dependencies, so this already gives
you both solvers. The `symbolic` backend (`"code": "symbolic"`) does not run a
Boltzmann solver at runtime and is used by the {doc}`first_forecast`. It relies on the
[`symbolic_pofk`](https://github.com/DeaglanBartlett/symbolic_pofk) package, which is not
published on PyPI and therefore cannot be installed automatically with `cosmicjellyfish`
(PyPI does not allow packages to depend on Git URLs). Install it once by hand:

```bash
pip install git+https://github.com/DeaglanBartlett/symbolic_pofk.git
```

Without it, `"code": "symbolic"` raises an `ImportError` with this same hint; the `camb`
and `class` backends are unaffected.

## Install from source

Clone [the repository](https://github.com/santiagocasas/cosmicjellyfish) and install it
with `uv` (recommended; CI uses it) or `pip`:

```bash
git clone https://github.com/santiagocasas/cosmicjellyfish.git
cd cosmicjellyfish
uv sync --extra dev        # or: pip install -e ".[dev]"
```

Leave out `--extra dev` (or `[dev]`) for a lighter install without the test and
linting tools. With `uv`, `symbolic_pofk` is installed automatically from its upstream Git
repository (via a default dependency group); with `pip`, add it by hand as shown above.

## Install with mamba or conda

The repository ships an `environment.yml` that takes the compiled scientific packages
(CAMB, NumPy, SciPy, h5py, ...) from `conda-forge` and installs the rest, including
`symbolic_pofk` and cosmicjellyfish itself (editable), with `pip`:

```bash
git clone https://github.com/santiagocasas/cosmicjellyfish.git
cd cosmicjellyfish
mamba env create -f environment.yml    # or: conda env create -f environment.yml
mamba activate cosmicjellyfish
```

`classy`, `chainconsumer` and `colossus` are not on conda-forge, so they come from PyPI
inside that same step. `classy` is compiled from source and its build calls `gcc`, `g++` and `make` by name, so the
environment also installs the conda-forge `gcc`, `gxx` and `make` packages (Linux and
macOS), so no system compilers are needed. On macOS the compiler still needs an SDK:
install the Xcode Command Line Tools (`xcode-select --install`) or point `SDKROOT` at
an SDK before creating the environment. To add optional extras afterward, use
`pip install -e ".[jaxcosmo]"` (or `emulators`, `docs`, `dev`) in the activated
environment. The versions in `environment.yml` mirror `pyproject.toml`; `ipython` is the
one exception, since conda-forge stops at 8.37 and `pip` moves it to the pinned 8.39.

## Optional extras

| Extra | Adds |
| --- | --- |
| `emulators` | `euclidemu2` (EuclidEmulator2 nonlinear boost with CLASS) and `emantis` (e-MANTIS f(R) boost) |
| `jaxcosmo` | JAX, `jax-cosmo` and compatibility dependencies for the optional differentiable backend |
| `docs` | Sphinx and the theme needed to build this documentation |
| `dev` | Linters, type checker, `pytest` and coverage, packaging tools |

```bash
pip install "cosmicjellyfish[emulators]"   # from PyPI
uv sync --extra emulators                # from a source checkout
uv sync --extra docs --extra dev         # several extras
```

## Hu-Sawicki f(R) gravity (optional, manual install)

The `cosmo_model: HuSawicki` profiles (`class/frahiclass_hs_photo*.yaml`) need two packages
that are **not** installed by any extra:

1. **`frahi_class`**, a hi_class-based CLASS with the Hu-Sawicki f(R) model. It provides the
   linear spectra and `A_s` of the f(R) run. **It is currently a private code**
   ([matiasleize/frahi_class](https://github.com/matiasleize/frahi_class)): to request
   access, contact Matías Leizerovich (<mleize@df.uba.ar>) or open an issue in the
   cosmicjellyfish repository. Build it following the instructions in its own repository. The build must install the Python module `hiclassy` that
   exposes the class `HiClass`. Selecting a `frahiclass_hs_photo*.yaml` profile does **not**
   select this wrapper: set `class_module: "hiclassy"` and `class_object: "HiClass"`
   explicitly in the run options, next to `class_config_yaml` (the defaults are
   `classy` and `Class`). Install it in the same environment as cosmicjellyfish, next to the
   official `classy`, which is still used for the LCDM nonlinear spectrum.

   ```{warning}
   Do **not** run `pip install hiclassy`. The `hiclassy` package on PyPI is the public
   hi_class, not `frahi_class`, and does not contain the f(R) modifications used here.
   ```

2. **`emantis`**, only for the `NONLINEAR: model: 'emantis'` boost (the e-MANTIS emulator).
   It is on PyPI and is included in the `emulators` extra (`pip install "cosmicjellyfish[emulators]"`
   or `uv sync --extra emulators`). The `winther2019` boost needs no extra package, since
   its fitting formula ships with cosmicjellyfish.

Without them the f(R) tests in `tests/` skip themselves, and every other backend keeps
working. The nonlinear f(R) boosts are described in `cosmicjellyfish/cosmology/modified_gravity.py`.

## Differentiable backend

For the optional differentiable backend, use `uv sync --extra jaxcosmo` from a
checkout containing that implementation. See {doc}`jaxcosmo` for the supported
models, derivative providers and notebook setup.

## Survey data

The survey specifications and the Euclid luminosity-ratio file (used for intrinsic
alignment) ship with the package, so no extra download is needed for the Euclid examples.

## Check the installation

```bash
python -c "import cosmicjellyfish; print('cosmicjellyfish import OK')"
```

Then run the {doc}`first_forecast`. From a source checkout with the `dev` extra, `uv run pytest`
runs the test suite.
