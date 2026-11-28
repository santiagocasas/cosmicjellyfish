-- Inline code -> \texttt{...} (as in the cloelib paper), instead of
-- \passthrough{\lstinline!...!} produced by pandoc's listings mode.
-- Keep text in Str nodes for LaTeX escaping and emit spaces explicitly.
function Code(el)
  local result = {pandoc.RawInline("latex", "\\texttt{")}
  local pos = 1
  for first, last in el.text:gmatch("() +()") do
    if first > pos then
      table.insert(result, pandoc.Str(el.text:sub(pos, first - 1)))
    end
    table.insert(result, pandoc.RawInline("latex", string.rep("{\\space}", last - first)))
    pos = last
  end
  if pos <= #el.text then
    table.insert(result, pandoc.Str(el.text:sub(pos)))
  end
  table.insert(result, pandoc.RawInline("latex", "}"))
  return result
end

-- The bibliography heading comes from \bibliography{} (natbib), so the
-- "# References" heading that JOSS needs in paper.md is dropped here.
function Header(el)
  if pandoc.utils.stringify(el.content) == "References" then
    return {}
  end
end
