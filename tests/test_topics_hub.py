"""Guard the topic index's SEO intent, structured data and link architecture."""
from __future__ import annotations
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("topics_hub", ROOT / "scripts" / "topics_hub.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TopicsHubTests(unittest.TestCase):
    def setUp(self):
        self.slugs = (*module.SUBJECT_ORDER, *module.PLATFORM_ORDER)
        self.groups = {
            slug: ({"name": slug.replace("-", " ").title(), "description": "Relevant AI signals"}, [{"signal_slug": "test"}])
            for slug in self.slugs
        }

    def test_schema_graph_and_list_positions(self):
        graph = module.topic_schema(self.groups)["@graph"]
        page, listing, crumbs = graph
        self.assertEqual(page["@type"], "CollectionPage")
        self.assertEqual(page["mainEntity"]["@id"], listing["@id"])
        self.assertEqual(page["breadcrumb"]["@id"], crumbs["@id"])
        self.assertEqual(listing["numberOfItems"], len(self.slugs))
        self.assertEqual(
            [entry["position"] for entry in listing["itemListElement"]],
            list(range(1, len(self.slugs) + 1)),
        )
        self.assertTrue(all(entry["url"].startswith(module.CANONICAL) for entry in listing["itemListElement"]))
        self.assertEqual(crumbs["@type"], "BreadcrumbList")

    def test_generator_page_single_h1_and_nine_real_links(self):
        result = module.render_topics_hub(
            self.groups,
            page_head=lambda title, desc, canonical, schema: (
                "<head><title>" + title + "</title>"
                + '<script type="application/ld+json">' + json.dumps(schema) + "</script></head>"
            ),
            page_header=lambda active="": "<header></header>",
            page_footer=lambda: "<footer></footer>",
        )
        self.assertEqual(len(re.findall(r"<h1\b", result)), 1)
        self.assertEqual(result.count('class="topics-hub-card"'), 9)
        self.assertEqual(result.count('class="topics-hub-path"'), 3)
        self.assertEqual(result.count('class="topics-hub-card-foot"'), 9)
        self.assertNotIn('tracked signals', result)
        self.assertIn('/assets/topic-navigation.js', result)
        self.assertIn('id="browse-by-topic"', result)
        self.assertIn('id="start-here"', result)
        self.assertNotIn("__SUBJECT_CARDS__", result)
        for slug in self.slugs:
            self.assertIn(f'href="/topics/{slug}/"', result)

    def test_published_static_page_follows_generator_contract(self):
        html = (ROOT / "topics" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://sxf.si/topics/"', html)
        self.assertIn('<h1 id="topics-hub-title">Explore AI <span>topics.</span></h1>', html)
        self.assertEqual(len(re.findall(r"<h1\b", html)), 1)
        self.assertEqual(html.count('class="topics-hub-card"'), 9)
        self.assertNotIn('tracked signals', html)
        self.assertIn('/assets/topic-navigation.js', html)
        self.assertIn('href="/topics/" aria-current="page"', html)
        self.assertIn('id="topics-method-heading"', html)
        self.assertNotIn("FAQPage", html)
        self.assertNotIn("HowTo", html)
        scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertEqual(len(scripts), 1)
        graph = json.loads(scripts[0])["@graph"]
        self.assertEqual([node["@type"] for node in graph], ["CollectionPage", "ItemList", "BreadcrumbList"])
        self.assertEqual(graph[1]["numberOfItems"], 9)
        self.assertEqual(graph[0]["mainEntity"]["@id"], graph[1]["@id"])
        for slug in self.slugs:
            self.assertIn(f'href="/topics/{slug}/"', html)



    def test_backlinks_are_contextual_and_idempotent(self):
        spec = importlib.util.spec_from_file_location("topic_crosslinks", ROOT / "scripts" / "topic_crosslinks.py")
        assert spec and spec.loader
        crosslinks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(crosslinks)
        for route, (description, slugs) in crosslinks.CONTEXT_ROUTES.items():
            text = (ROOT / route).read_text(encoding="utf-8")
            self.assertEqual(text.count(crosslinks.MARKER), 1, route)
            self.assertEqual(text.count(crosslinks.SCRIPT), 1, route)
            self.assertEqual(crosslinks.enrich_topic_context(text, description, slugs), text)
            for slug in slugs:
                self.assertIn(f'href="/topics/{slug}/"', text)

    def test_topic_event_bridge_no_network_or_persistence(self):
        code = (ROOT / "assets" / "topic-navigation.js").read_text(encoding="utf-8")
        self.assertIn("sxf_topic_navigation", code)
        self.assertIn("window.dataLayer", code)
        for forbidden in ("sendBeacon", "fetch(", "localStorage", "document.cookie"):
            self.assertNotIn(forbidden, code)


if __name__ == "__main__":
    unittest.main()
