-- doc_links.lua
function RawInline(el)
  if el.format == "html" then
    local id = el.text:match("^<doc:(.-)>")
    if id then
      return pandoc.Link(id, id .. ".html")
    end
  end
  return nil
end