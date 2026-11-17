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

    # The generated Guides directory must retain authored Wallet coverage after
    # every scheduled feed refresh. Manual edits to guides/index.html are overwritten.
    # The economic guide must stay linked from the generated catalog and retain its original evidence lab.
    bubble_url = BASE + "/guides/ai-bubble-explained/"
    bubble_dir = ROOT / "guides/ai-bubble-explained"
    assert bubble_url in actual_list, "SXF AI Bubble guide is missing from sitemap"
    bubble_page = (bubble_dir / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="{bubble_url}"' in bubble_page, "AI Bubble canonical changed"
    assert bubble_page.count("<h1") == 1, "AI Bubble guide must have one H1"
    assert 'id="monitor"' in bubble_page and 'id="portfolio-lab"' in bubble_page, "SXF original research labs missing"
    assert (bubble_dir / "bubble-monitor.js").is_file(), "Interactive SXF Bubble Monitor missing"
    for figure in ("ai-bubble-economic-transmission-map.svg", "ai-bubble-2026-capex-evidence.svg", "ai-bubble-scenarios-2027-2030.svg"):
        assert (bubble_dir / "images" / figure).is_file(), "Missing original AI Bubble graphic " + figure
        assert figure in bubble_page, "Bubble guide does not reference its original figure " + figure
    catalog_source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    directory = (ROOT / "guides/index.html").read_text(encoding="utf-8")
    assert '"href": "/guides/ai-bubble-explained/"' in catalog_source, "Bubble guide missing from generator source"
    assert 'href="/guides/ai-bubble-explained/"' in directory, "Bubble guide missing from generated Guides directory"
    for slug in ("ai-agent-cost", "why-does-ai-use-water", "ai-agent-use-cases", "what-is-agentic-ai"):
        assert 'href="/guides/ai-bubble-explained/"' in (ROOT / "guides" / slug / "index.html").read_text(encoding="utf-8"), "Missing backlink from " + slug

    # Authored privacy field guide stays discoverable on every regenerated directory and sitemap.
    privacy = BASE + "/guides/remove-personal-information-online/"
    generator_text = (ROOT / "scripts" / "update_news.py").read_text(encoding="utf-8")
    directory_text = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    assert privacy in actual_list, "Privacy removal guide missing from sitemap"
    assert '"href": "/guides/remove-personal-information-online/"' in generator_text, "Privacy guide missing from source catalog"
    assert 'href="/guides/remove-personal-information-online/"' in directory_text, "Privacy guide missing from rendered directory"
    privacy_page = (ROOT / "guides/remove-personal-information-online/index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="{privacy}"' in privacy_page, "Privacy guide canonical changed"
    assert privacy_page.count("<h1") == 1, "Privacy guide must have one H1"
    for asset in ("personal-information-removal-map.svg", "google-search-removal-decision-tree.svg", "ai-chat-data-deletion-checklist.svg"):
        assert (ROOT / "guides/remove-personal-information-online/images" / asset).exists(), "Missing privacy guide graphic: " + asset
        assert asset in privacy_page, "Privacy guide figure is not referenced: " + asset
    for inbound in ("how-to-tell-if-an-image-is-ai-generated", "why-does-chatgpt-make-things-up", "chatgpt-wallet"):
        linked_page = (ROOT / "guides" / inbound / "index.html").read_text(encoding="utf-8")
        assert 'href="/guides/remove-personal-information-online/"' in linked_page, "Missing inbound privacy guide link from " + inbound

    wallet = BASE + "/guides/chatgpt-wallet/"
    directory = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    generator = (ROOT / "scripts" / "update_news.py").read_text(encoding="utf-8")
    assert 'href="/guides/chatgpt-wallet/"' in directory, "Wallet guide missing from rendered Guides directory"
    assert '"href": "/guides/chatgpt-wallet/"' in generator, "Wallet guide missing from source catalog"
    assert wallet in actual_list, "Wallet guide missing from sitemap"
    page = (ROOT / "guides" / "chatgpt-wallet" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="' + wallet + '">' in page, "Wallet canonical changed"
    image_urls = (
        wallet + "images/chatgpt-wallet-payment-flow.webp",
        wallet + "images/agentic-commerce-market-shift.webp",
    )
    sitemap_root = ET.parse(ROOT / "sitemap.xml").getroot()
    image_ns = "{http://www.google.com/schemas/sitemap-image/1.1}"
    wallet_nodes = [
        node for node in sitemap_root.findall("s:url", NS)
        if node.findtext("s:loc", namespaces=NS) == wallet
    ]
    assert len(wallet_nodes) == 1, "Wallet sitemap page missing or duplicated"
    actual_images = [
        img.findtext(image_ns + "loc") for img in wallet_nodes[0].findall(image_ns + "image")
    ]
    assert all(url in actual_images for url in image_urls), "Wallet images missing from generated image sitemap"
    for asset in image_urls:
        assert (ROOT / asset.removeprefix(BASE + "/")).is_file(), "Wallet image file missing: " + asset

    print(f"PASS: all {len(expected)} indexable guide URLs are present exactly once")


if __name__ == "__main__":
    main()
