#!/usr/bin/env python3
"""A narrow, offline integrity check of SXF's editorial hallucination example audit."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SLUG = "why-does-chatgpt-make-things-up"
BASE = ROOT / "guides" / SLUG
URL = "https://sxf.si/guides/" + SLUG + "/"

def main():
    page = (BASE / "index.html").read_text(encoding="utf-8")
    audit = json.loads((BASE / "research" / "verification-cases.json").read_text(encoding="utf-8"))
    method = (BASE / "research" / "methodology.md").read_text(encoding="utf-8")
    assert audit["schemaVersion"] == 1
    assert len(audit["cases"]) == 8
    assert len({r["id"] for r in audit["cases"]}) == 8
    assert len({r["fault"] for r in audit["cases"]}) == 8
    assert len(audit["sources"]) >= 3
    assert "not raw model outputs" in audit["uncheckedAnswersAre"].lower()
    for r in audit["cases"]:
        for key in ("id", "question", "fault", "unchecked", "verified", "source", "check"):
            min_length = 3 if key == "id" else 9
            assert isinstance(r.get(key), str) and len(r[key].strip()) >= min_length, (r.get("id"), key)
        assert r["source"] in audit["sources"]
        assert r["unchecked"] != r["verified"]
        assert r["id"] in page
        assert len(r["question"].strip()) >= 25
    for src in audit["sources"].values():
        assert src["url"].startswith("https://")
        assert src["url"] in page
    assert "not output transcripts" in method
    assert "not that an AI model was tested" in method
    assert '<link rel="canonical" href="' + URL + '"' in page
    assert "index,follow" in page.split("</head>")[0]
    assert page.count("<h1") == 1
    assert page.count("<main") == 1 and page.count("</main>") == 1
    assert page.count("<article") == page.count("</article>")
    assert "application/ld+json" in page
    start = page.index('<script type="application/ld+json">') + len('<script type="application/ld+json">')
    graph = json.loads(page[start:page.index("</script>", start)])["@graph"]
    assert {"WebPage", "Article", "BreadcrumbList"}.issubset({n.get("@type") for n in graph})
    ids = re.findall(r'id="([^"]+)"', page)
    assert len(ids) == len(set(ids)), "Duplicate HTML ID"
    assert "research/methodology.md" in page
    assert "research/verification-cases.json" in page
    assert "not a ChatGPT benchmark" in page.lower()
    assert "fabricated quotes" in page.lower()
    assert "how to fact-check chatgpt" in page.lower()
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert URL in sitemap, "Missing published sitemap entry"
    guides = (ROOT / "guides/index.html").read_text(encoding="utf-8")
    assert '/guides/' + SLUG + '/' in guides
    for path in ("guides/ai-deception-alignment-faking/index.html", "research/ai-agent-reliability/index.html"):
        assert '/guides/' + SLUG + '/' in (ROOT / path).read_text(encoding="utf-8"), path
    print("PASS: original editorial evidence provenance, SEO, schema, source references and internal linking")

if __name__ == "__main__":
    main()
