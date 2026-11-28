-- Inline code -> \texttt{...} (as in the cloelib paper), instead of
-- \passthrough{\lstinline!...!} produced by pandoc's listings mode.
-- The text is kept as a Str, so pandoc escapes LaTeX special characters.
function Code(el)
  return {
    pandoc.RawInline("latex", "\\texttt{"),
    pandoc.Str(el.text),
    pandoc.RawInline("latex", "}"),
  }
end

-- The bibliography heading comes from \bibliography{} (natbib), so the
-- "# References" heading that JOSS needs in paper.md is dropped here.
function Header(el)
  if pandoc.utils.stringify(el.content) == "References" then
    return {}
  end
end
