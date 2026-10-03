#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "data" / "ai-enrichment-review.json"
PREVIEW_ROOT = ROOT / "preview" / "signals"
SIGNALS_ROOT = ROOT / "signals"
SITEMAP_PATH = ROOT / "sitemap.xml"


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def schema_types(html):
    found = set()
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    )
    for raw in blocks:
        data = json.loads(raw)
        if isinstance(data, dict):
            graph = data.get("@graph") or []
            if isinstance(graph, list):
                for node in graph:
                    if isinstance(node, dict) and isinstance(node.get("@type"), str):
                        found.add(node["@type"])
            elif isinstance(data.get("@type"), str):
                found.add(data["@type"])
    return found


def robots_value(html):
    match = re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)',
        html,
        re.I,
    )
    return match.group(1).lower() if match else ""


def canonical_value(html):
    match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
        html,
        re.I,
    )
    return match.group(1) if match else ""


def main():
    payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    expect(payload.get("version") == "sxf-ai-enrichment-review-v1", "review version drift")
    expect(payload.get("mode") == "manual-review", "review mode must stay manual-review")
    rows = payload.get("items")
    expect(isinstance(rows, list) and rows, "review list missing")

    sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
    expect("/preview/" not in sitemap, "preview URL must never enter sitemap")

    for row in rows:
        slug = row["signal_slug"]
        draft = row["draft"]
        expected_types = set(row.get("schema_types") or [])
        expect(int(row.get("validator_quality_score", 0)) >= 90, f"{slug}: quality score below 90")
        expect(len(row.get("evidence_hash", "")) == 64, f"{slug}: evidence hash invalid")

        if row.get("review_status") == "preview":
            expect(row.get("approved_for_publish") is False, f"{slug}: preview cannot be approved")
            expect(row.get("index_decision") == "noindex", f"{slug}: preview must stay noindex")
            preview_path = PREVIEW_ROOT / draft["seo_slug_recommendation"] / "index.html"
            expect(preview_path.exists(), f"{slug}: preview HTML missing")
            html = preview_path.read_text(encoding="utf-8")
            expect("noindex" in robots_value(html), f"{slug}: preview must be noindex")
            expect("MANUAL REVIEW PREVIEW" in html, f"{slug}: preview banner missing")
            expect(canonical_value(html) == row["signal_url"], f"{slug}: preview canonical drift")
            continue

        expect(row.get("review_status") == "approved", f"{slug}: unsupported review status")
        expect(row.get("approved_for_publish") is True, f"{slug}: approved row must allow publish")
        expect(row.get("index_decision") == "index", f"{slug}: approved row must allow index")
        expect(row.get("approved_at"), f"{slug}: approved_at missing")
        expect(slug == draft["seo_slug_recommendation"], f"{slug}: live slug must equal reviewed SEO slug")

        live_path = SIGNALS_ROOT / slug / "index.html"
        expect(live_path.exists(), f"{slug}: promoted live page missing")
        live_html = live_path.read_text(encoding="utf-8")
        expect("noindex" not in robots_value(live_html), f"{slug}: promoted page must be indexable")
        expect(canonical_value(live_html) == row["signal_url"], f"{slug}: promoted canonical drift")
        expect("MANUAL REVIEW PREVIEW" not in live_html, f"{slug}: preview banner leaked into live page")
        expect("NOT PUBLISHED" not in live_html, f"{slug}: preview safety text leaked into live page")
        expect(f'<h1>{draft["h1"]}</h1>' in live_html, f"{slug}: reviewed H1 missing")

        types = schema_types(live_html)
        for required in expected_types:
            expect(required in types, f"{slug}: live schema missing {required}")
        for faq in draft.get("faq") or []:
            expect(faq["question"] in live_html, f"{slug}: FAQ question not visible")
            expect(faq["answer"] in live_html, f"{slug}: FAQ answer not visible")
        for source in draft.get("sources") or []:
            expect(source in live_html, f"{slug}: official source missing from live page")

        expect(row["signal_url"] in sitemap, f"{slug}: promoted URL missing from sitemap")

        preview_path = PREVIEW_ROOT / draft["seo_slug_recommendation"]
        expect(not preview_path.exists(), f"{slug}: preview directory must be removed after promotion")

        legacy_slug = row.get("legacy_signal_slug")
        legacy_url = row.get("legacy_signal_url")
        if legacy_slug:
            legacy_path = SIGNALS_ROOT / legacy_slug / "index.html"
            expect(legacy_path.exists(), f"{slug}: legacy route missing")
            legacy_html = legacy_path.read_text(encoding="utf-8")
            expect("noindex" in robots_value(legacy_html), f"{slug}: legacy route must be noindex")
            expect(canonical_value(legacy_html) == row["signal_url"], f"{slug}: legacy canonical drift")
            expect(row["signal_url"] in legacy_html, f"{slug}: legacy route must point to promoted URL")
            if legacy_url:
                expect(legacy_url not in sitemap, f"{slug}: legacy URL must leave sitemap")

    print(f"AI enrichment review promotion tests passed: {len(rows)} page(s)")


if __name__ == "__main__":
    main()
