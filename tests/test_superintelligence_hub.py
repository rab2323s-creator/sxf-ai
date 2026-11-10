#!/usr/bin/env python3
"""Guard authored superintelligence SEO, content, internal links, schema and layout."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "superintelligence/index.html").read_text(encoding="utf-8")
source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
css = (ROOT / "intelligence.css").read_text(encoding="utf-8")

assert '<title>Artificial Superintelligence (ASI): AGI vs ASI Explained | SXF / AI</title>' in page
assert '<meta name="description" content="What is artificial superintelligence (ASI)?' in page
assert 'rel="canonical" href="https://sxf.si/superintelligence/"' in page
assert 'https://sxf.si/assets/og/superintelligence-asi.webp' in page
assert 'Last verified <strong>Nov 10, 2026</strong>' in page
assert '<h1>' in page and page.count('<h1') == 1
assert 'Research directly relevant to artificial superintelligence.' in page
assert 'github-copilot-slack' not in page and 'amazon-hope-moe' not in page
assert page.count('href="/guides/intelligence-explosion/"') >= 2

part = page.split('<section class="si-continuum shell">', 1)[1].split('</section>', 1)[0]
assert part.index('class="si-continuum-grid"') < part.index('class="si-compare"') < part.index('class="guide-callout"')
assert part.count('<tr><th scope="row">') == 4 and part.count('<th scope="col">') == 3
assert part.count('data-label="AGI"') == 4 and part.count('data-label="ASI"') == 4
assert 'role="region" aria-label="AGI versus ASI comparison"' in part
assert 'stacked cards on phones' in css and 'content:attr(data-label)' in css
assert '(SUPERINTELLIGENCE_DIR / "index.html").write_text' not in source
# Inspect the renderer's syntax tree instead of matching a formatting-specific
# "with" string: both editorial ownership and model-page protection are required.
render_functions = [
    node for node in ast.parse(source).body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "render_site"
]
assert len(render_functions) == 1, "Expected exactly one site renderer"
guarded_blocks = [
    {
        item.context_expr.func.id
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
        and isinstance(item.context_expr.func, ast.Name)
    }
    for node in ast.walk(render_functions[0])
    if isinstance(node, ast.With)
]
assert any(
    {"preserve_authored_pages", "protect_model_pages"} <= guards
    for guards in guarded_blocks
), "Site renderer must preserve authored pages and validate model pages together"

ld = re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>', page)
assert ld, "Missing JSON-LD"
graph = json.loads(ld.group(1))["@graph"]
collection = next(x for x in graph if x["@type"] == "CollectionPage")
faq = next(x for x in graph if x["@type"] == "FAQPage")["mainEntity"]
assert collection["dateModified"] == "2026-11-10"
assert len(faq) == len(re.findall(r"<details><summary>", page)) == 10
for question in faq:
    assert f'<summary>{question["name"]}</summary>' in page
print("PASS: authored ASI SEO, sources, schema, table, responsive CSS and generator ownership")
