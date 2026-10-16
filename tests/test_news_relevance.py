#!/usr/bin/env python3
"""Offline regression tests for the proposed SXF AI news relevance gate."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from news_relevance import assess_news, primary_category, substantive_summary

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

    def test_summary_boilerplate(self):
        self.assertEqual(substantive_summary("We’re on a journey to advance and democratize artificial intelligence through open source and open science."), "")
        self.assertNotEqual(substantive_summary("A major new AI model was released."), "")

if __name__ == "__main__":
    unittest.main()
