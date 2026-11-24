"""Source-cited, regeneration-safe editorial updates for selected model routes.

The dated register is a narrowly scoped editorial review, not a replacement
for the canonical pricing/specs catalog or its historical verification dates.
Apply after all page renderers and before sitemap fingerprinting.
"""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "data/model-page-content/verified-model-updates.json"
SCHEMA = re.compile(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.S)
PAGE_TYPES = {"WebPage", "CollectionPage", "TechArticle", "Article"}


def load_register(root=ROOT):
    return json.loads((Path(root) / REGISTER.relative_to(ROOT)).read_text(encoding="utf-8"))


def update_fragment(slug, row, stamp):
    sources = " · ".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>'
        for url, label in row["sources"]
    )
    return (
        f'<section class="shell model-deep-section" id="sxf-verified-model-update" data-verified-model-update="{slug}">'
        f'<div class="model-section-head"><p class="eyebrow">SOURCE-VERIFIED EDITORIAL UPDATE · {stamp}</p>'
        f'<h2>{escape(row["title"])}</h2><p>{escape(row["text"])}</p></div>'
        f'<p class="reference-note">Primary sources: {sources}</p></section>'
    )


def apply_update(page, slug, row, stamp):
    for old, new in row.get("replacements", []):
        page = page.replace(old, new)
        escaped = escape(old)
        if escaped != old:
            page = page.replace(escaped, escape(new))
    marker = f'data-verified-model-update="{slug}"'
    fragment = update_fragment(slug, row, stamp)
    if marker in page:
        pattern = re.compile(r'<section\b[^>]*' + re.escape(marker) + r'[^>]*>.*?</section>', re.S)
        page, count = pattern.subn(lambda _: fragment, page)
        if count != 1:
            raise ValueError(f"Invalid verified model update section for {slug}")
    else:
        hero = page.find("</section>", page.find("<main"))
        if hero < 0:
            raise ValueError(f"Missing main hero section for {slug}")
        hero += len("</section>")
        page = page[:hero] + "\n" + fragment + page[hero:]

    def schema_rewrite(match):
        obj = json.loads(match.group(2))
        nodes = obj if isinstance(obj, list) else obj.get("@graph", [obj])
        for node in nodes:
            if not isinstance(node, dict) or node.get("@type") not in PAGE_TYPES:
                continue
            if str(node.get("dateModified", ""))[:10] < stamp:
                node["dateModified"] = stamp
            citations = node.setdefault("citation", [])
            if isinstance(citations, list):
                for url, _label in row["sources"]:
                    if url not in citations:
                        citations.append(url)
        return match.group(1) + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + match.group(3)

    return SCHEMA.sub(schema_rewrite, page)


def apply_verified_model_updates(root=ROOT):
    root = Path(root)
    register = load_register(root)
    for slug, row in register["updates"].items():
        path = root / "models" / slug / "index.html"
        before = path.read_text(encoding="utf-8")
        after = apply_update(before, slug, row, row.get("date", register["date"]))
        if after != before:
            path.write_text(after, encoding="utf-8")
