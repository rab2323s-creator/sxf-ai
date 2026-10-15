"""Regression tests for the evergreen intelligence explosion guide."""
import json
import re
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from intelligence_explosion_guide import render_intelligence_explosion_guide


class IntelligenceExplosionGuideTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "guides/intelligence-explosion/index.html").read_text(encoding="utf-8")
        cls.body = (ROOT / "data/guide-content/intelligence-explosion.html").read_text(encoding="utf-8")
        cls.styles = (ROOT / "guides/intelligence-explosion/reference.css").read_text(encoding="utf-8")
        structured = re.search(r'<script type="application/ld\+json">([^<]+)</script>', cls.html)
        assert structured, "Missing JSON-LD"
        cls.graph = json.loads(structured.group(1))["@graph"]

    def test_build_round_trip(self):
        self.assertEqual(self.html, render_intelligence_explosion_guide())

    def test_canonical_and_metadata(self):
        url = "https://sxf.si/guides/intelligence-explosion/"
        self.assertIn(f'<link rel="canonical" href="{url}"', self.html)
        self.assertEqual(self.html.count("<h1>"), 1)
        self.assertEqual(self.html.count('<meta property="og:image"'), 1)
        self.assertEqual(self.html.count('<meta name="twitter:card"'), 1)
        self.assertNotIn("intelligence-explosion-2026", self.html)
        article = next(x for x in self.graph if x["@type"] == "TechArticle")
        self.assertEqual(article["url"], url)
        self.assertIn("https://arxiv.org/abs/2608.14426", article["citation"])
        self.assertIn("https://metr.org/blog/2026-10-14-ai-rd-acceleration-assessment-proposal/", article["citation"])

    def test_faq_schema_matches_visible_content(self):
        faq = next(x for x in self.graph if x["@type"] == "FAQPage")
        visible = re.findall(r"<details><summary>([^<]+)</summary>", self.body)
        self.assertEqual(len(visible), 10)
        self.assertEqual(visible, [x["name"] for x in faq["mainEntity"]])

    def test_images_and_mobile_readability(self):
        self.assertEqual(self.body.count('class="ie-figure"'), 2)
        self.assertEqual(self.body.count('class="ie-fullsize"'), 2)
        self.assertIn("overflow-x:auto", self.styles)
        self.assertIn("min-width:680px", self.styles)
        for name in ("recursive-improvement-feedback-loop.svg", "hard-vs-soft-ai-takeoff.svg"):
            svg_path = ROOT / "guides/intelligence-explosion/images" / name
            svg = ET.parse(svg_path).getroot()
            self.assertEqual(svg.attrib.get("viewBox"), "0 0 1600 900")
            self.assertIn(name, self.html)
            self.assertIn(name, self.body)

    def test_site_indexes_and_reverse_links(self):
        route = "/guides/intelligence-explosion/"
        for path in (
            "guides/index.html",
            "superintelligence/index.html",
            "guides/can-ai-replicate-itself/index.html",
            "guides/will-ai-take-over-the-world/index.html",
            "scripts/update_news.py",
            "scripts/sitemap_generation.py",
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                if path == "scripts/sitemap_generation.py":
                    self.assertIn('guides/intelligence-explosion/', text)
                else:
                    self.assertIn(route, text)
        sitemap = ET.parse(ROOT / "sitemap.xml")
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
              "image": "http://www.google.com/schemas/sitemap-image/1.1"}
        pages = [entry for entry in sitemap.findall("sm:url", ns)
                 if entry.findtext("sm:loc", default="", namespaces=ns) ==
                 "https://sxf.si/guides/intelligence-explosion/"]
        self.assertEqual(len(pages), 1)
        self.assertEqual(len(pages[0].findall("image:image", ns)), 2)


if __name__ == "__main__":
    unittest.main()
