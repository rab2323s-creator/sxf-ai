#!/usr/bin/env python3
"""Editorial importance gate: reject noise without losing material AI developments."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from news_importance import assess_editorial_news, assess_importance
from news_relevance import partition_news_rows


class EditorialImportanceTests(unittest.TestCase):
    def decision(self, title, source="OpenAI", summary=""):
        return assess_editorial_news(title, summary, source).status

    def test_meaningful_news(self):
        samples = [
            ("Introducing GPT-6.1 Terra", "OpenAI"),
            ("Build specialized multimodal models with LFM3", "Hugging Face"),
            ("How we detect frontier model misalignment", "OpenAI"),
            ("The sleep framework: A new way for LLMs to retain knowledge in continual learning", "Google Research"),
            ("Bringing foundational models to the front lines of TB screening", "Google Research"),
            ("Claude Haiku 5.5 in GitHub Copilot", "GitHub"),
            ("GPT-6.1 Terra in GitHub Copilot", "GitHub"),
            ("Upcoming deprecation of selected GitHub Copilot models", "GitHub"),
            ("NVIDIA Nemotron 3.5 Embed, Rerank, and Parse: Advancing Agents with World-Class Retrieval Models", "Hugging Face"),
        ]
        for title, source in samples:
            with self.subTest(title=title):
                self.assertEqual(self.decision(title, source), "accept")

    def test_ambiguous_and_promotional_hold_for_review(self):
        samples = [
            ("How Fanatics and OpenAI streamline the fan experience", "OpenAI"),
            ("Credit Saison achieves 954% ROI in a ChatGPT Enterprise pilot", "OpenAI"),
            ("What FDE means at OpenAI", "OpenAI"),
            ("The future of the firm", "OpenAI"),
            ("Working with academic communities to build scientific understanding", "OpenAI"),
            ("Our newest AI Quest: Mapping the human brain", "Google AI"),
            ("Global default for Copilot features generally available", "GitHub"),
            ("ChatGPT’s expanding world of work", "OpenAI"),
        ]
        for title, source in samples:
            with self.subTest(title=title):
                self.assertEqual(self.decision(title, source), "review")

    def test_relevance_rejects_remain_rejected(self):
        self.assertEqual(self.decision("Xcode 27 runner image generally available", "GitHub"), "reject")
        self.assertEqual(self.decision("Search and filter for budgets now available", "GitHub"), "reject")

    def test_reviewed_primary_source_exceptions_stay_intact(self):
        from editorial_review import REVIEWED_NEWS
        for url, row in REVIEWED_NEWS.items():
            with self.subTest(url=url):
                self.assertEqual(
                    assess_editorial_news(row["title"], "", row["source"], url).status,
                    row["status"],
                )

    def test_ingestion_never_auto_publishes_review(self):
        rows = [
            {"title": "Introducing GPT-6.1 Terra", "summary": "", "source": "OpenAI", "url": "https://example.org/model"},
            {"title": "How Fanatics and OpenAI streamline the fan experience", "summary": "", "source": "OpenAI", "url": "https://example.org/promo"},
            {"title": "Search and filter for budgets now available", "summary": "", "source": "GitHub", "url": "https://example.org/unrelated"},
        ]
        approved, review, rejected = partition_news_rows(rows, assess_editorial_news)
        self.assertEqual([x["url"] for x in approved], ["https://example.org/model"])
        self.assertEqual([x["url"] for x in review], ["https://example.org/promo"])
        self.assertEqual([x["url"] for x in rejected], ["https://example.org/unrelated"])


if __name__ == "__main__":
    unittest.main()
