#!/usr/bin/env bash
# Build the arXiv version of the paper (JOSS-style LaTeX, as for cloelib) from paper.md.
#
# arXiv takes neither Markdown nor a PDF produced by LaTeX; it wants the LaTeX
# source and compiles it itself with pdflatex. This script converts paper.md
# with pandoc into paper/arxiv/build/ms.tex, using the JOSS-style front matter
# in paper/arxiv/front_matter/ (taken from the cloelib arXiv submission), runs
# pdflatex + bibtex to produce ms.bbl, and packs everything arXiv needs.
#
# Usage, from the repository root:
#     bash paper/make_arxiv.sh
# Output:
#     paper/arxiv/build/ms.pdf                   local preview
#     paper/arxiv/cosmicjellyfish_arxiv.tar.gz   <- upload this file to arXiv
# Both are ignored by git (paper/arxiv/.gitignore).
#
# Requirements:
#   - pandoc >= 3.2, or Docker (then the pandoc/core image is used)
#   - pdflatex and bibtex (TeX Live) for the .bbl and the local preview.
#     arXiv runs BibTeX itself only if no .bbl is uploaded, so ship the .bbl.
#
# Edit paper.md, not build/ms.tex: the build folder is overwritten every time.
set -euo pipefail

cd "$(dirname "$0")"
SRC=arxiv
OUT=arxiv/build
PANDOC_IMAGE=pandoc/core:3.6

rm -rf "$OUT"
mkdir -p "$OUT/figures" "$OUT/front_matter"

# 1. Markdown -> LaTeX. HTML comments in paper.md (review notes) are dropped.
# Use a local pandoc >= 3.2 if there is one, otherwise the Docker image.
if command -v pandoc >/dev/null 2>&1 && pandoc --version | head -1 | grep -qE ' 3\.([2-9]|[1-9][0-9])'; then
    PANDOC=(pandoc)
else
    PANDOC=(docker run --rm --volume "$PWD":/data --user "$(id -u)":"$(id -g)" "$PANDOC_IMAGE")
fi
echo "Using $("${PANDOC[@]}" --version | head -1)"
# Code blocks as LaTeX listings: --syntax-highlighting=idiomatic since pandoc 3.8,
# --listings before (deprecated, but still accepted, in 3.8 and later).
if "${PANDOC[@]}" --help | grep -q -- '--syntax-highlighting'; then
    LISTINGS=(--syntax-highlighting=idiomatic)
else
    LISTINGS=(--listings)
fi
"${PANDOC[@]}" paper.md --from markdown --to latex \
    --template "$SRC/ms.latex" \
    --metadata-file "$SRC/metadata.yaml" \
    --lua-filter "$SRC/latex_filters.lua" \
    --natbib "${LISTINGS[@]}" \
    -o "$OUT/ms.tex"

# 2. Copy the files that ms.tex needs.
cp "$SRC"/front_matter/*.tex "$OUT/front_matter/"
cp "$SRC/figures/joss-logo.png" "$OUT/figures/"
cp paper.bib "$OUT/paper.bib"
cp "$SRC/mnras.bst" "$OUT/"
grep -o 'figures/[A-Za-z0-9_.-]*\.\(png\|pdf\|jpg\)' "$OUT/ms.tex" | sort -u | while read -r fig; do
    cp "$fig" "$OUT/$fig"
done

# 3. Compile as arXiv does: pdflatex, bibtex, pdflatex, pdflatex.
if command -v pdflatex >/dev/null 2>&1; then
    (cd "$OUT"
     # Without the cm-super fonts (present on arXiv), microtype stops with "auto
     # expansion is only possible with scalable fonts". The local preview then
     # loads Latin Modern, which looks the same; the uploaded ms.tex is unchanged.
     TEXINPUT='\input{ms}'
     run() { pdflatex -jobname=ms -interaction=nonstopmode -halt-on-error "$TEXINPUT" > ms.build.log 2>&1 && return 0
             if grep -q "auto expansion is only possible with scalable" ms.build.log && [ "$TEXINPUT" = '\input{ms}' ]; then
                 echo "Note: cm-super fonts not installed locally; previewing with Latin Modern."
                 TEXINPUT='\RequirePackage{lmodern}\input{ms}'; run; return
             fi
             echo "pdflatex failed, see $OUT/ms.build.log"; tail -20 ms.build.log; exit 1; }
     run; bibtex ms > ms.bibtex.log 2>&1 || { cat ms.bibtex.log; exit 1; }; run; run
     echo "Local build OK: $OUT/ms.pdf ($(grep -c '' ms.bbl) lines of references)")
else
    echo "pdflatex not found: skipping the local build and the .bbl (arXiv will then run BibTeX)."
fi

# 4. Tarball with only the files arXiv needs.
(cd "$OUT"
 files=(ms.tex front_matter figures paper.bib mnras.bst)
 [ -f ms.bbl ] && files+=(ms.bbl)
 tar czf ../cosmicjellyfish_arxiv.tar.gz "${files[@]}")
echo "Upload paper/arxiv/cosmicjellyfish_arxiv.tar.gz to arXiv."
