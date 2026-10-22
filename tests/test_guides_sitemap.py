#!/usr/bin/env python3
"""Ensure every indexable, self-canonical guide appears in the generated sitemap."""
from pathlib import Path
import sys
import tempfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sitemap_generation import indexable_guide_urls, append_missing_guide_rows, sitemap_entry

BASE = "https://sxf.si"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def main():
    expected = set(indexable_guide_urls(ROOT, BASE))
    actual_list = [
        (node.findtext("s:loc", namespaces=NS) or "")
        for node in ET.parse(ROOT / "sitemap.xml").findall("s:url", NS)
    ]
    assert len(actual_list) == len(set(actual_list)), "Duplicate sitemap URLs"
    missing = sorted(expected - set(actual_list))
    assert not missing, "Indexable guides missing from sitemap: " + ", ".join(missing)

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        guides = root / "guides"
        for slug, robots in (("new-guide", "index,follow"), ("private-guide", "noindex,follow")):
            folder = guides / slug
            folder.mkdir(parents=True)
            (folder / "index.html").write_text(
                '<html><head><link rel="canonical" href="' + BASE + '/guides/' + slug + '/">'
                '<meta name="robots" content="' + robots + '"></head><body><main>Guide</main></body></html>',
                encoding="utf-8",
            )
        rows = [sitemap_entry(BASE + "/guides/existing-guide/", "2026-10-01")]
        append_missing_guide_rows(rows, root, BASE, "2026-10-22")
        append_missing_guide_rows(rows, root, BASE, "2026-10-22")
        assert sum("/guides/new-guide/" in row for row in rows) == 1
        assert not any("/guides/private-guide/" in row for row in rows)
        page = guides / "new-guide" / "index.html"
        page.write_text('<html><head><link rel="canonical" href="https://wrong.example/"></head></html>')
        try:
            list(indexable_guide_urls(root, BASE))
        except ValueError as error:
            assert "self-canonical" in str(error)
        else:
            raise AssertionError("Canonical mismatch must fail validation")

    print(f"PASS: all {len(expected)} indexable guide URLs are present exactly once")


if __name__ == "__main__":
    main()
