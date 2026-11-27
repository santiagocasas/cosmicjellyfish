# JOSS paper for cosmicjellyfish

This folder goes into the repository root as `paper/`:

```text
paper/
  paper.md        the manuscript (Markdown with a YAML header, JOSS format)
  paper.bib       the bibliography (BibTeX); keys are cited as [@Key] in paper.md
  figures/        the PNG figures referenced by paper.md (versioned, see below)
  scripts/        scripts that regenerate Figures 1, 2, 4 and 5
```

The GitHub workflow that builds the draft lives in `.github/workflows/draft-pdf.yml`.

There is no JOSS template to copy into the repository. The template (LaTeX class, logo,
citation style) lives inside the `openjournals/inara` Docker image, which both routes
below use. The repository only needs `paper.md`, `paper.bib` and the figures.

The five PNG figures referenced by the paper are committed (a narrow exception in
`.gitignore`), so the CI build can find them. The PDF copies, the `fig2_*` extras and the
`results/`, `cache/` and `memory_cache/` folders written by the scripts stay ignored.

## Compile locally with Docker

From the repository root:

```bash
docker run --rm \
    --volume "$PWD/paper":/data \
    --user "$(id -u)":"$(id -g)" \
    --env JOURNAL=joss \
    openjournals/inara
```

This writes `paper/paper.pdf` (draft mode: watermark and line numbers) and
a JATS folder next to it. Paths inside `paper.md` are relative to `paper.md`, so the figures
resolve as `figures/...`. To build only the PDF, append `-o pdf paper.md` to the command.

The build products (`paper/paper.pdf`, `paper/jats/`) are already ignored by git.

## Author roles (CRediT)

[![CRediT](https://img.shields.io/badge/contributions-CRediT-using?color=%23cd2653)](https://credit.niso.org/implementing-credit/)

Contributor roles follow the [CRediT taxonomy](https://credit.niso.org/). The source of truth
is the `roles:` list of each author in the YAML front matter of `paper.md`, e.g.
`- {credit: software, credit-name: "Software"}`. The Open Journals build (pandoc's JATS
template) turns these into machine-readable `<role vocab="credit" ...>` elements in
`paper/jats/paper.jats`; they do not appear in the PDF, so the "Author contributions" section
repeats them in prose. To keep both in sync, run from the repository root:

```bash
python paper/scripts/check_credit_roles.py
```

It checks every role against the 14 official CRediT roles and compares the YAML with the prose
bullets (needs PyYAML).

## Compile with GitHub Actions

The "Draft PDF" workflow (`.github/workflows/draft-pdf.yml`) runs on every push to any
branch, so each commit of a paper PR gets a draft PDF. It can also be started by hand
from the Actions tab ("Draft PDF" -> "Run workflow").

To get the PDF of the latest push: Actions -> the run -> Artifacts -> `paper`.
With the `gh` CLI: `gh run download --name paper` (add `--dir paper-draft` to choose
the target folder).

The workflow uses `openjournals/openjournals-draft-action`, which runs the same Docker
image as above.

## Regenerate the figures

```bash
uv sync --extra jaxcosmo
cd paper/figures
uv run python ../scripts/fig1_euclid_probes.py   # about 10 s
uv run --extra jaxcosmo python ../scripts/fig2_autodiff.py   # about 1 min
uv run python ../scripts/fig4_survey_comparison.py   # about 2-3 min (needs the symbolic backend)
uv run python ../scripts/fig5_spectro_survey_comparison.py   # about 2 min
```

`fig5_spectro_survey_comparison.py` drives `scripts/validation/run_survey_forecasts.py` with
the Euclid GCsp, DESI 2023 (BGS, LRG, ELG, QSO) and SKAO IM x DESI cases, so it needs the
DESI-2023 and SKAO-IM specifications and the survey-forecast runner from `main`. It writes
`paper/figures/fig5_spectro_survey_comparison.png` directly and keeps the per-model JSON
reports in a temporary directory.

The scripts write PNG and PDF files and a `results/` folder into the current directory.
`fig3_fisher_vs_nautilus.png` is a copy of
`docs/source/_static/likelihood_validation/wl_gcsp_symbolic_euclid_64cpu_joint.png`; it
is regenerated with `scripts/likelihood/postprocess/render_likelihood_validation.py`
from the 64-core chains (see the likelihood validation page of the documentation).

## Notes for whoever (person or agent) finishes the paper

- Search `paper.md` for `TODO`: affiliations and ORCIDs in the YAML header, three
  missing citations, the hardware for the symbolic timings, the AI usage disclosure,
  the acknowledgements and the author contributions.
- `paper.bib` was written by hand. Check every entry against ADS or INSPIRE before
  submission; the ones marked `% CHECK` are the least certain. JOSS reviewers ask for a
  DOI on every reference that has one.
- JOSS asks for 750 to 1750 words. The text is at about 2200 words without the code
  listings, so it has to be shortened for a JOSS submission (not for arXiv).
- The repository linters (`isort`, `black`, `ruff`) also run on `paper/scripts/`; the
  scripts pass them as delivered.
- Do not change numbers in the text without rerunning the source: the autodiff numbers
  come from `scripts/paper-joss/autodiff_numbers.py`, the Nautilus numbers and timings
  from `scripts/paper-joss/reproduce_all.sh` (see `scripts/paper-joss/README.md`; the
  first run is in `docs/source/likelihood_validation.md`), the CAMB/CLASS timings from
  `docs/source/default_vs_hp_profiles.md`.
