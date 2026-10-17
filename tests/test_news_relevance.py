#!/usr/bin/env python3
"""Offline regression tests for the proposed SXF AI news relevance gate."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from news_relevance import assess_news, primary_category, substantive_summary, partition_news_rows
from editorial_review import REVIEWED_NEWS, CATEGORY_CORRECTIONS, reviewed_category

class NewsRelevanceTests(unittest.TestCase):
    def test_reject_unrelated_github(self):
        titles = [
            "Download GitHub Code Quality license usage as a CSV",
            "Email notifications for repository push events have been retired",
            "GitHub Actions workflow lockfiles in public preview",
            "GitHub App improvements for least privilege and management",
            "Search and filter for budgets now available",
            "Stacked pull requests generally available",
            "Xcode 27 runner image generally available",
            "Open source license compliance generally available",
            "CodeQL 2.27.2 improves C++, Go, Rust, and JavaScript analysis",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertEqual(assess_news(title, "", "GitHub").status, "reject")

    def test_accept_ai_github(self):
        titles = [
            "AI Scan for pull requests generally available",
            "Claude Haiku 5.5 in GitHub Copilot",
            "Gemini 4 Argon in GitHub Copilot",
            "GitHub Copilot weekly releases",
            "Agentic autofix for code scanning alerts",
            "Upcoming deprecation of selected GitHub Copilot models",
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertEqual(assess_news(title, "", "GitHub").status, "accept")

    def test_review_indirect_ai_context(self):
        self.assertEqual(assess_news("Secret scanning blocks Anthropic keys by default",
                                     "Detects Anthropic API keys in pushes.", "GitHub").status, "review")

    def test_research_and_community(self):
        self.assertEqual(assess_news("Scaling Indic Pretraining: 2.8 Trillion Tokens and an Open Data Generation Pipeline",
                                     "", "Hugging Face").status, "accept")
        self.assertEqual(assess_news("Impactful scheduling for GPU clusters",
                                     "", "Hugging Face").status, "review")
        self.assertEqual(assess_news("Putting Earth AI to work: Geospatial agents",
                                     "", "Google Research").status, "accept")

    def test_classification(self):
        self.assertEqual(primary_category("Apertus 1.5 Release Notes", "Hugging Face"), "Models")
        self.assertEqual(primary_category("Welcome open-weight model", "Hugging Face"), "Open Source")
        self.assertEqual(primary_category("Gemini 4 Argon in GitHub Copilot", "GitHub"), "Tools")

    def test_current_selector_rechecks_old_archive_rows(self):
        from datetime import datetime, timezone, timedelta
        from types import SimpleNamespace
        from signal_processing import select_current_items
        now = datetime.now(timezone.utc)
        def item(title, source="GitHub"):
            return {"title": title, "summary": "", "source": source,
                    "url": "https://example.test/" + str(len(title)),
                    "published": now.isoformat(), "relevance_status": "accept"}
        ctx = SimpleNamespace(
            parse_date=lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")),
            source_by_name={"GitHub": {"status": "live", "max_current": 10}},
            source_expansion_names=set(),
            source_expansion_max_current_per_source=10,
            source_expansion_max_current_total=10,
            max_items=10, assess_news=assess_news,
        )
        selected = select_current_items([
            item("Search and filter for budgets now available"),
            item("Gemini 4 Argon in GitHub Copilot"),
        ], now - timedelta(days=21), ctx)
        self.assertEqual([x["title"] for x in selected],
                         ["Gemini 4 Argon in GitHub Copilot"])

    def test_discovery_filters_legacy_snapshot_items(self):
        import ast
        # Static guard: every discovery render must use the common gate, while
        # historic articles and existing SEO routes are still generated.
        src = (Path(__file__).resolve().parents[1] / "scripts" / "update_news.py").read_text()
        self.assertIn("items = discoverable_news(items)", src)
        self.assertIn("current = discoverable_news(current)", src)
        self.assertIn("discoverable_news(archive), as_of=", src)
        self.assertIn("for item in legacy_items:", src)
        ast.parse(src)

    def test_ingestion_gate_never_archives_rejected_or_review_rows(self):
        rows = [
            {"title": "GitHub Copilot adds a new AI coding model", "summary": "", "source": "GitHub", "url": "https://x.test/ai"},
            {"title": "Xcode 27 runner image generally available", "summary": "", "source": "GitHub", "url": "https://x.test/noise"},
            {"title": "Secret scanning blocks Anthropic keys by default", "summary": "", "source": "GitHub", "url": "https://x.test/review"},
        ]
        accepted, review, rejected = partition_news_rows(rows)
        self.assertEqual([x["url"] for x in accepted], ["https://x.test/ai"])
        self.assertEqual([x["url"] for x in review], ["https://x.test/review"])
        self.assertEqual([x["url"] for x in rejected], ["https://x.test/noise"])
        self.assertEqual(len(rows), 3)

    def test_all_eighteen_reviewed_records(self):
        self.assertEqual(len(REVIEWED_NEWS), 18)
        self.assertEqual(sum(x["status"] == "accept" for x in REVIEWED_NEWS.values()), 16)
        self.assertEqual(sum(x["status"] == "reject" for x in REVIEWED_NEWS.values()), 2)
        for url, item in REVIEWED_NEWS.items():
            with self.subTest(url=url):
                actual = assess_news(item["title"], "", item["source"], url)
                self.assertEqual(actual.status, item["status"])
                self.assertEqual(actual.reason, "individually_reviewed_source")
                if item["status"] == "accept":
                    self.assertEqual(reviewed_category(item["title"], item["source"]), item["category"])
                self.assertNotEqual(assess_news(item["title"] + " changed", "", item["source"], url).reason,
                                    "individually_reviewed_source")

    def test_manual_overrides_do_not_admit_unrelated_news(self):
        self.assertEqual(assess_news("Open source license compliance generally available", "", "GitHub").status, "reject")
        self.assertEqual(assess_news("Xcode 27 runner image generally available", "", "GitHub").status, "reject")
        self.assertEqual(len(CATEGORY_CORRECTIONS), 5)
        self.assertEqual(reviewed_category("Granite Switch 4.1: Chat, Decisions, and Speech from One Endpoint", "Hugging Face"), "Models")

    def test_summary_boilerplate(self):
        self.assertEqual(substantive_summary("We’re on a journey to advance and democratize artificial intelligence through open source and open science."), "")
        self.assertNotEqual(substantive_summary("A major new AI model was released."), "")

if __name__ == "__main__":
    unittest.main()
