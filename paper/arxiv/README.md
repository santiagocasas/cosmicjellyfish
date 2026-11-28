# arXiv version of the paper

arXiv accepts neither Markdown nor a PDF produced by LaTeX: it wants LaTeX source and
compiles it itself with pdflatex. `paper/make_arxiv.sh` converts `paper/paper.md` into
a JOSS-style LaTeX project (the same front matter as the cloelib arXiv submission) and
packs it for upload.

`paper.md` stays the only source of the text. Do not edit `build/ms.tex`: it is
overwritten on every run.

## Run

From the repository root:

```bash
bash paper/make_arxiv.sh
```

Output, both ignored by git:

- `paper/arxiv/build/ms.pdf`: local preview
- `paper/arxiv/cosmicjellyfish_arxiv.tar.gz`: upload this file to arXiv
  (`ms.tex`, `ms.bbl`, `front_matter/`, `figures/`, `paper.bib`, `mnras.bst`)

Requirements: pandoc >= 3.2 (otherwise Docker is used with the `pandoc/core` image),
and a TeX Live installation with pdflatex, BibTeX, `orcidlink`, and the TikZ `bayesnet`
library (`tikzlibrarybayesnet.code.tex`) for the preview and the `.bbl`. A minimal TeX
installation may omit these packages. If the `cm-super` fonts are not
installed locally, the preview falls back to Latin Modern; the uploaded files are not
changed by this, and arXiv has the fonts.

## Files

| File | Purpose |
| --- | --- |
| `ms.latex` | pandoc template: authors and affiliations from the YAML header of `paper.md`, then the body |
| `front_matter/preamble.tex` | JOSS page layout, fonts, header (JOSS logo) and footer (citation line) |
| `front_matter/margin.tex` | first-page sidebar: links, install line, licence, DOI and dates (fill in when known) |
| `front_matter/macros.tex` | shared macros (journal abbreviations, Euclid acknowledgement texts) |
| `metadata.yaml` | title as typeset, with the package name in monospace |
| `latex_filters.lua` | inline code as `\texttt`, and drops the `# References` heading (BibTeX adds its own) |
| `mnras.bst` | MNRAS reference style, as for cloelib |
| `figures/joss-logo.png` | header logo, from the official JOSS template (openjournals/inara) |

## Things to adjust by hand

- **Sidebar position:** `\sidebaroffset` at the top of `front_matter/margin.tex`. Make it
  less negative if the sidebar overlaps the header logo, more negative if it starts
  well below the title. It depends on the length of the author list.
- **Sidebar contents:** DOI, Zenodo archive and dates in `front_matter/margin.tex`.
- **Corresponding author e-mail:** add `email:` to that author in the YAML header of
  `paper.md`; the template prints it in the footnote.
- **"On behalf of" line:** define `\collaborationline` (see `front_matter/preamble.tex`)
  only if the paper is published on behalf of a collaboration.
- **Affiliations and author names in `paper.md`:** write accents as Unicode characters
  (`Astrofísica`, not `Astrof\'{i}sica`) and use plain quotes. LaTeX escapes and
  backtick quotes in the YAML header are printed literally.
