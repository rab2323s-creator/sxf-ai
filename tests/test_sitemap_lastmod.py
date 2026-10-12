#!/usr/bin/env python3
"""Regression tests for content-driven Sitemap lastmod updates."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sitemap_lastmod import (
    content_fingerprint, refresh_existing_sitemap, synchronize_lastmod,
    validate_sitemap_state,
)

BASE = "https://sxf.si"
URL = BASE + "/guides/example/"
NEXT = BASE + "/models/pricing/"


def page(body, *, chrome="Nav", title="Example"):
    return (
        f'<html><head><title>{title}</title>'
        '<meta name="description" content="A useful guide"></head>'
        f'<body><header>{chrome}</header><main><h1>Example</h1>'
        f'<p>{body}</p><time>2026-10-12</time>'
        '</main><footer>Footer</footer><script>var a = 1;</script></body></html>'
    )


def xml(rows):
    return '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"


def row(url, lastmod):
    return f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>"


def main():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "data").mkdir()
        target = root / "guides" / "example" / "index.html"
        target.parent.mkdir(parents=True)
        target.write_text(page("Useful original explanation"), encoding="utf-8")
        sitemap = root / "sitemap.xml"
        sitemap.write_text(xml([row(URL, "2026-10-01")]), encoding="utf-8")

        first = synchronize_lastmod([row(URL, "2026-10-12")], sitemap, BASE, today="2026-10-12")
        assert "<lastmod>2026-10-01</lastmod>" in first[0], "Bootstrap must preserve existing date"
        sitemap.write_text(xml(first), encoding="utf-8")
        validate_sitemap_state(sitemap, BASE)

        # Nav, scripts, style and timestamp-only changes are not editorial updates.
        before = content_fingerprint(root, URL, BASE)
        target.write_text(page("Useful original explanation", chrome="Updated nav") + "<style>p{color:red}</style>", encoding="utf-8")
        assert content_fingerprint(root, URL, BASE) == before
        again = synchronize_lastmod([row(URL, "2026-10-12")], sitemap, BASE, today="2026-10-12")
        assert again == first
        sitemap.write_text(xml(again), encoding="utf-8")
        validate_sitemap_state(sitemap, BASE)

        # A visible factual change bumps the date, and then remains stable.
        target.write_text(page("A corrected and expanded explanation"), encoding="utf-8")
        corrected = synchronize_lastmod(again, sitemap, BASE, today="2026-10-12")
        assert "<lastmod>2026-10-12</lastmod>" in corrected[0]
        sitemap.write_text(xml(corrected), encoding="utf-8")
        validate_sitemap_state(sitemap, BASE)
        assert synchronize_lastmod(corrected, sitemap, BASE, today="2026-10-13") == corrected

        # Dataset-driven UI must update even if its HTML stays the same.
        price_page = root / "models" / "pricing" / "index.html"
        price_page.parent.mkdir(parents=True)
        price_page.write_text(page("Compare official prices"), encoding="utf-8")
        dataset = root / "data" / "model-pricing.json"
        dataset.write_text(json.dumps({"source_verified": "2026-10-01", "models": [{"model": "A", "price": 2, "provenance": {"verified_at": "2026-10-01"}}]}), encoding="utf-8")
        extra = synchronize_lastmod([*corrected, row(NEXT, "2026-10-01")], sitemap, BASE, today="2026-10-12")
        assert "<lastmod>2026-10-01</lastmod>" in extra[1]
        sitemap.write_text(xml(extra), encoding="utf-8")
        initial_data_hash = content_fingerprint(root, NEXT, BASE)
        dataset.write_text(json.dumps({"source_verified": "2026-10-13", "models": [{"model": "A", "price": 2, "provenance": {"verified_at": "2026-10-13"}}]}), encoding="utf-8")
        assert content_fingerprint(root, NEXT, BASE) == initial_data_hash, "Verification alone must not count"
        dataset.write_text(json.dumps({"source_verified": "2026-10-13", "models": [{"model": "A", "price": 3, "provenance": {"verified_at": "2026-10-13"}}]}), encoding="utf-8")
        assert content_fingerprint(root, NEXT, BASE) != initial_data_hash
        refresh_existing_sitemap(sitemap, BASE)
        assert "<lastmod>2026-10-12</lastmod>" in sitemap.read_text().splitlines()[-2]
        validate_sitemap_state(sitemap, BASE)

        # Detect unrefreshed content and refuse to silently claim timestamps are accurate.
        target.write_text(page("New facts after sitemap regeneration"), encoding="utf-8")
        try:
            validate_sitemap_state(sitemap, BASE)
        except ValueError as e:
            assert "Stale" in str(e)
        else:
            raise AssertionError("Validation must reject stale dates")
        refresh_existing_sitemap(sitemap, BASE)
        validate_sitemap_state(sitemap, BASE)

        try:
            synchronize_lastmod([row(URL, "2026-10-01")] * 2, sitemap, BASE, today="2026-10-12")
        except ValueError as e:
            assert "Duplicate" in str(e)
        else:
            raise AssertionError("Duplicate URL must be rejected")

    print("PASS: content-based lastmod is persistent, stable and validated")


if __name__ == "__main__":
    main()
