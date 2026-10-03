#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "data" / "ai-enrichment-review.json"
PREVIEW_ROOT = ROOT / "preview" / "signals"
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


def main():
    payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    expect(payload.get("version") == "sxf-ai-enrichment-review-v1", "review version drift")
    expect(payload.get("mode") == "manual-review", "review mode must stay manual-review")
    rows = payload.get("items")
    expect(isinstance(rows, list) and rows, "review preview list missing")

    sitemap = SITEMAP_PATH.read_text(encoding="utf-8")
    expect("/preview/" not in sitemap, "preview URL must never enter sitemap")

    for row in rows:
        slug = row["signal_slug"]
        draft = row["draft"]
        preview_slug = draft["seo_slug_recommendation"]
        expect(row.get("review_status") == "preview", f"{slug}: review status drift")
        expect(row.get("approved_for_publish") is False, f"{slug}: preview cannot be approved for publish")
        expect(row.get("index_decision") == "noindex", f"{slug}: preview must stay noindex")
        expect(int(row.get("validator_quality_score", 0)) >= 90, f"{slug}: quality score below 90")
        expect(len(row.get("evidence_hash", "")) == 64, f"{slug}: evidence hash invalid")

        path = PREVIEW_ROOT / preview_slug / "index.html"
        expect(path.exists(), f"{slug}: generated preview HTML missing")
        html = path.read_text(encoding="utf-8")

        robots = re.search(
            r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)',
            html,
            re.I,
        )
        expect(robots and "noindex" in robots.group(1).lower(), f"{slug}: preview must be noindex")

        canonical = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
            html,
            re.I,
        )
        expect(canonical and canonical.group(1) == row["signal_url"], f"{slug}: canonical drift")

        expect("MANUAL REVIEW PREVIEW" in html, f"{slug}: preview banner missing")
        expect("NOT PUBLISHED" in html, f"{slug}: not-published safety marker missing")
        expect(f'<h1>{draft["h1"]}</h1>' in html, f"{slug}: reviewed H1 missing")

        types = schema_types(html)
        for required in row.get("schema_types") or []:
            expect(required in types, f"{slug}: schema missing {required}")

        for faq in draft.get("faq") or []:
            expect(faq["question"] in html, f"{slug}: FAQ question not visible")
            expect(faq["answer"] in html, f"{slug}: FAQ answer not visible")

        for source in draft.get("sources") or []:
            expect(source in html, f"{slug}: official source missing from preview")

    print(f"AI enrichment review preview tests passed: {len(rows)} page(s)")


if __name__ == "__main__":
    main()
