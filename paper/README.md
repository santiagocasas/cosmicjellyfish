# JOSS paper for cosmicjellyfish

This folder goes into the repository root as `paper/`:

```text
paper/
  paper.md        the manuscript (Markdown with a YAML header, JOSS format)
  paper.bib       the bibliography (BibTeX); keys are cited as [@Key] in paper.md
  figures/        the three PNG figures referenced by paper.md
  scripts/        scripts that regenerate Figures 1 and 2
  github-workflow/draft-pdf.yml   move to .github/workflows/draft-pdf.yml
```

There is no JOSS template to copy into the repository. The template (LaTeX class, logo,
citation style) lives inside the `openjournals/inara` Docker image, which both routes
below use. The repository only needs `paper.md`, `paper.bib` and the figures.

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

Add the build products to `.gitignore`:

```text
paper/paper.pdf
paper/paper.jats/
paper/jats/
```

## Compile with GitHub Actions

1. Move `paper/github-workflow/draft-pdf.yml` to `.github/workflows/draft-pdf.yml` and
   delete the `github-workflow` folder.
2. Commit and push. The workflow runs on every push that touches `paper/**`, and it can
   be started by hand from the Actions tab ("Draft PDF" -> "Run workflow").
3. Download the PDF from the run page: Actions -> the run -> Artifacts -> `paper`.
   With the `gh` CLI: `gh run download --name paper`.

The workflow uses `openjournals/openjournals-draft-action`, which runs the same Docker
image as above.

## Regenerate the figures

```bash
uv sync --extra jaxcosmo
cd paper/figures
uv run python ../scripts/fig1_euclid_probes.py   # about 10 s
uv run --extra jaxcosmo python ../scripts/fig2_autodiff.py   # about 1 min
```

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
  come from `scripts/fig2_autodiff.py`, the Nautilus numbers and timings from
  `docs/source/likelihood_validation.md`, the CAMB/CLASS timings from
  `docs/source/default_vs_hp_profiles.md`.
