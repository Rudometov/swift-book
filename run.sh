#!/bin/bash

rm -rf HTML
find . -type f -name '*.md' -exec bash -c 'f="$1"; out="HTML/${f#./}"; out="${out%.md}.html"; mkdir -p "$(dirname "$out")"; pandoc "$f" --lua-filter=doc_links.lua -o "$out"' _ {} \;
cp -R ./TSPL.docc/Assets ./HTML/TSPL.docc/
python3.11 fix_html_links.py /Users/victor/IdeaProjects/swift-book/HTML/TSPL.docc/