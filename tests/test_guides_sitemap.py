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


def test_ai_sdr_guide_contract():
    from content_ownership import is_authored_html, preserve_authored_pages
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from html.parser import HTMLParser
    import re
    relative = Path("guides/best-ai-sdr-tools/index.html")
    page = (ROOT / relative).read_text(encoding="utf-8")
    source = (ROOT / "scripts/editorial/best-ai-sdr-tools.md").read_text(encoding="utf-8")
    assert is_authored_html(relative), "AI SDR guide must be editorial-owned"
    assert 'href="https://sxf.si/guides/best-ai-sdr-tools/"' in page and 'id="sdr-editorial"' in page
    assert 'href="/guides/best-ai-sdr-tools/"' in (ROOT / "guides/index.html").read_text(encoding="utf-8")
    assert '"href": "/guides/best-ai-sdr-tools/"' in (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    for path in ["guides/best-ai-agents/index.html","guides/best-ai-agents-for-marketing/index.html","guides/ai-agent-cost/index.html","research/ai-agent-reliability/index.html","guides/ai-agent-testing-tools/index.html","guides/ai-agent-observability/index.html"]:
        assert 'href="/guides/best-ai-sdr-tools/"' in (ROOT / path).read_text(encoding="utf-8"), path
    class Text(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    # Every source block must remain in the visible HTML, including tables, code, and final disclosure.
    article = page.split('<article class="sdr-article" id="sdr-editorial">', 1)[1].split("</article>", 1)[0]
    parser = Text()
    parser.feed(article)
    visible = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    content = source.split("---", 2)[2]
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("```") or re.fullmatch(r"[|: -]+", line):
            continue
        line = re.sub(r"^#{1,3} |^[-] |^\d+\. ", "", line)
        line = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", line)
        line = line.replace("**", "").replace("`", "")
        parts = [p.strip() for p in line.split("|") if p.strip()] if line.startswith("|") else [line]
        for part in parts:
            # HTML inline tags can add whitespace before punctuation; normalize it away.
            compact = re.sub(r"\s+", "", part)
            assert compact in re.sub(r"\s+", "", visible), "Missing AI SDR source content: " + part[:120]
    with TemporaryDirectory() as temp:
        root = Path(temp)
        target = root / relative
        target.parent.mkdir(parents=True)
        target.write_text(page, encoding="utf-8")
        with preserve_authored_pages(root):
            target.unlink()
        assert target.read_text(encoding="utf-8") == page
    print("PASS: complete AI SDR source, reciprocal links and authored-page restore")

if __name__ == "__main__":
    test_ai_sdr_guide_contract()


def test_voice_agent_guide_contract():
    from content_ownership import is_authored_html, preserve_authored_pages
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from html.parser import HTMLParser
    import re

    relative = Path("guides/best-ai-voice-agent-platforms/index.html")
    page = (ROOT / relative).read_text(encoding="utf-8")
    source = (ROOT / "scripts/editorial/best-ai-voice-agent-platforms.md").read_text(encoding="utf-8")
    route = "/guides/best-ai-voice-agent-platforms/"
    assert is_authored_html(relative)
    assert 'href="https://sxf.si' + route + '"' in page
    assert 'name="robots" content="index,follow' in page
    assert 'href="' + route + '"' in (ROOT / "guides/index.html").read_text(encoding="utf-8")
    assert '"href": "' + route + '"' in (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    for path in ["guides/ai-receptionist/index.html","guides/gpt-realtime-2-1-playground/index.html","guides/best-ai-text-to-speech-models/index.html","guides/best-ai-agents/index.html","guides/best-ai-sdr-tools/index.html","guides/ai-agent-cost/index.html","guides/ai-agent-observability/index.html","guides/ai-agent-security/index.html","guides/ai-agent-testing-tools/index.html","research/ai-agent-reliability/index.html"]:
        other = (ROOT / path).read_text(encoding="utf-8")
        assert 'href="' + route + '"' in other, path
        assert 'href="/' + path.removesuffix("index.html") + '"' in page, path

    class Text(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)

    article = page.split('<article id="voice-editorial">', 1)[1].split("</article>", 1)[0]
    parser = Text()
    parser.feed(article)
    visible = "".join("".join(parser.parts).split())
    segments = 0
    for line in source.split("---", 2)[2].splitlines():
        line = line.strip()
        if not line or line in ("[[COST_TOOL]]", "[[LAB_TOOL]]") or re.fullmatch(r"[|: -]+", line):
            continue
        line = re.sub(r"^#{1,3} |^[-] |^[0-9]+[.] ", "", line)
        line = re.sub(r"[[]([^]]+)[]][(][^)]*[)]", lambda m: m.group(1), line).replace("**", "").replace(chr(96), "")
        parts = [p.strip() for p in line.split("|") if p.strip()] if line.startswith("|") else [line]
        for part in parts:
            assert "".join(part.split()) in visible, "Missing voice guide source: " + part[:100]
            segments += 1
    assert segments >= 282
    for control in ("cost-form", "trial-list", "lab-selftest", "lab-export", "cost-export"):
        assert 'id="' + control + '"' in article
    assert (ROOT / relative.parent / "voice.css").is_file()
    assert (ROOT / relative.parent / "voice.js").is_file()
    with TemporaryDirectory() as temp:
        root = Path(temp)
        target = root / relative
        target.parent.mkdir(parents=True)
        target.write_text(page, encoding="utf-8")
        with preserve_authored_pages(root):
            target.unlink()
        assert target.read_text(encoding="utf-8") == page
    print("PASS: voice guide full source, reciprocal links, tools and authored-page restoration")


if __name__ == "__main__":
    test_voice_agent_guide_contract()
