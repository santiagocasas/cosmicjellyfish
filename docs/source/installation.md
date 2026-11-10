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

If you prefer conda-style environments, create one with `mamba` (or `conda`) and install
in editable mode:

```bash
mamba create -n cosmicjellyfish -c conda-forge python=3.11 pip
mamba activate cosmicjellyfish
git clone https://github.com/santiagocasas/cosmicjellyfish.git
cd cosmicjellyfish
pip install -e .
```

## Optional extras

| Extra | Adds |
| --- | --- |
| `emulators` | `euclidemu2`, for the EuclidEmulator2 nonlinear boost with CLASS |
| `jaxcosmo` | JAX, `jax-cosmo` and compatibility dependencies for the optional differentiable backend |
| `docs` | Sphinx and the theme needed to build this documentation |
| `dev` | Linters, type checker, `pytest` and coverage, packaging tools |

```bash
pip install "cosmicjellyfish[emulators]"   # from PyPI
uv sync --extra emulators                # from a source checkout
uv sync --extra docs --extra dev         # several extras
```

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
