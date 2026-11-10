#!/usr/bin/env python3
"""Regression tests for preserving model editorial content during catalog refreshes."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from model_editorial_guard import (
    fingerprint, is_model_page, protect_model_pages, regressions, snapshot, verify,
)


def sample(
    price: str = "$1.00",
    context: str = "200K",
    summary: str = "Original API guide with $1.00 pricing and 200K context",
    *,
    section: bool = True,
    faq: bool = True,
    lab: bool = True,
    table: bool = True,
    controls: bool = True,
    latest: str = "Latest model update",
    additional: str = "",
) -> str:
    prose = (
        "Original independent model analysis with source-backed context limits, "
        "API tradeoffs and deployment pitfalls. The current listed price is $1.00 "
        "and the model supports 200K context tokens. This evidence-based explanation "
        "is editorial material, not a generated price card."
    )
    schema = json.dumps({
        "@graph": [
            {"@type": "TechArticle", "headline": "Original research"},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": "How much does the API cost?"}
            ]} if faq else {},
        ]
    })
    guide = (
        '<section id="original-model-research" data-sxf-model-guide>'
        f'<h2>Independent analysis for {context} context</h2>'
        f'<p>{prose.replace("$1.00", price).replace("200K", context)}</p>'
        '<a href="/guides/ai-agent-reliability/">Related evidence</a>'
        + ('<table><tr><th>API</th><td>Pricing</td></tr></table>' if table else '')
        + ('<label>Input <input type="number" /></label>' if controls else "")
        + additional + "</section>"
    ) if section else ""
    questions = (
        '<section id="original-model-faq"><h2>Frequently asked questions</h2>'
        '<details><summary>How much does the API cost?</summary>'
        f'<p>Its documented price is {price} per million input tokens and may vary '
        'for caching and different model tiers.</p></details></section>'
    ) if faq else ""
    return f'''<!doctype html><html lang="en"><head>
<title>Model API Guide: {context} Context &amp; Pricing | SXF</title>
<meta name="description" content="{summary.replace("$1.00", price).replace("200K", context)}" />
<meta name="robots" content="index,follow"/>
<meta property="og:image" content="https://sxf.si/assets/model-preview.webp"/>
<link rel="canonical" href="https://sxf.si/models/sample/" />
<link rel="stylesheet" href="/assets/model-guide.css?v=1" />
<script type="application/ld+json">{schema}</script>
</head><body><main><h1>Model API: {context} tokens</h1>
<div class="model-fact-grid"><p>Live Standard price {price}, {context} context.</p></div>
{guide}
{questions}
<section class="model-change-watch" data-what-changed><h2>Recent news</h2>
<p>{latest}. This volatile model-news paragraph is expected to be replaced
whenever provider or research signals change in the editorial feed.</p></section>
</main>{'<script defer src="/assets/model-calculator.js?v=8"></script>' if lab else ''}
</body></html>'''


def check():
    assert is_model_page(Path("models/sample/index.html"))
    assert not is_model_page(Path("models/pricing/extra.html"))
    assert not is_model_page(Path("guides/sample/index.html"))
    old = fingerprint(sample())
    new_price = fingerprint(sample(
        price="$2.75", context="300K",
        latest="An entirely new provider signal and source",
    ))
    assert not regressions(old, new_price), regressions(old, new_price)
    assert regressions(old, fingerprint(sample(section=False)))
    assert any("faq" in x for x in regressions(old, fingerprint(sample(faq=False))))
    assert any("tables" in x for x in regressions(old, fingerprint(sample(table=False))))
    assert any("controls" in x for x in regressions(old, fingerprint(sample(controls=False))))
    assert any("assets" in x for x in regressions(old, fingerprint(sample(lab=False))))
    assert any("description" in x for x in regressions(
        old, fingerprint(sample(summary="Reverted to a generic auto-generated reference"))
    ))
    assert any("sources" in x for x in regressions(
        old, fingerprint(sample().replace(
            '<a href="/guides/ai-agent-reliability/">Related evidence</a>', ""
        ))
    ))
    assert any("prose" in x for x in regressions(
        old, fingerprint(sample().replace(
            "Original independent model analysis with source-backed context limits, ",
            "Generic catalog data with no authored content. ",
        ))
    ))
    assert not regressions(old, fingerprint(sample(
        additional="<p>Additional cited editorial research that the next generation "
                   "of the page must preserve across every scheduled build.</p>"
    )))
    with TemporaryDirectory() as td:
        root = Path(td)
        path = root / "models/sample/index.html"
        path.parent.mkdir(parents=True)
        path.write_text(sample(), encoding="utf-8")
        base = snapshot(root)
        assert len(base) == 1
        with protect_model_pages(root):
            path.write_text(sample(price="$5.00", context="400K"), encoding="utf-8")
        verify(root, base)

        with_error = path.read_bytes()
        try:
            with protect_model_pages(root):
                path.write_text(sample(section=False), encoding="utf-8")
        except RuntimeError as exc:
            assert "models/sample/index.html" in str(exc)
        else:
            raise AssertionError("A deleted editorial section must block the build")
        assert path.read_bytes() == with_error, "Failed builds must restore model HTML"

        path.unlink()
        try:
            verify(root, base)
        except RuntimeError as exc:
            assert "page disappeared" in str(exc)
        else:
            raise AssertionError("A missing model route must block the build")

        path.write_text(sample(), encoding="utf-8")
        output = root / "model-baseline.json"
        subprocess.run([
            sys.executable, str(ROOT / "scripts/model_editorial_guard.py"),
            "snapshot", "--root", str(root), "--file", str(output)
        ], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([
            sys.executable, str(ROOT / "scripts/model_editorial_guard.py"),
            "verify", "--root", str(root), "--file", str(output)
        ], check=True, stdout=subprocess.DEVNULL)

    source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "with preserve_authored_pages(ROOT), protect_model_pages(ROOT):" in source
    print("PASS: prices/specs update; authored SEO, research, FAQ and labs cannot disappear")


if __name__ == "__main__":
    check()
