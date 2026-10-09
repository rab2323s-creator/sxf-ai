#!/usr/bin/env python3
"""Open Source topic precision, archive selection, and generated parity."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news as site  # noqa: E402
from open_source_signals import select_open_source_signals  # noqa: E402

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


def sample(title, *, source="Hugging Face", category="Tools", age=3, summary=""):
    slug = title.lower().replace(" ", "-")
    return dict(title=title, source=source, category=category,
                url="https://example.test/" + slug,
                signal_url="https://sxf.si/signals/" + slug + "/",
                published=(NOW-timedelta(days=age)).isoformat(),
                summary=summary, tags=[])


def main():
    topic = next(t for t in site.TOPICS if t["slug"] == "open-source-ai")
    hf = sample("Open-sourcing AstaBrief model for developers")
    gh = sample("Discover local models in GitHub Copilot CLI", source="GitHub")
    older = sample("Transformers now runs llama.cpp quants", age=17)
    multi = sample("Open-source coding agent framework", source="GitHub")
    for row in (hf, gh, older, multi):
        assert site.topic_matches(row, topic), row["title"]
    assert site.topic_matches(multi, next(t for t in site.TOPICS if t["slug"] == "coding-ai"))
    assert multi["category"] == "Tools", "Topic membership must not rewrite primary category"

    negatives = (
        sample("Repository permissions update", source="GitHub"),
        sample("GitHub release notes for account settings", source="GitHub"),
        sample("Unrelated product launch", summary="Open source and open science."),
        sample("Open TTS Leaderboard", summary="Open source and open science."),
        sample("Local sandboxing for GitHub Copilot", source="GitHub"),
    )
    for row in negatives:
        assert not site.topic_matches(row, topic), row["title"]

    # "quant" can refer to quantitative finance, not model quantization.
    jump = sample(
        "How Jump Trading is scaling quant research with ChatGPT",
        source="OpenAI", category="Research",
        summary="Financial quantitative research using ChatGPT.",
    )
    jump["tags"] = ["Open Source AI"]  # Simulate an obsolete archive tag.
    assert not site.topic_matches(jump, topic)
    assert "Open Source AI" not in site.classify_tags(
        jump["title"], jump["source"], jump["category"])
    finance = sample("Quant trading strategy updates", source="GitHub")
    assert not site.topic_matches(finance, topic)
    assert site.categorize(finance["title"], finance["source"]) != "Open Source"

    actual_quantization = sample("GGUF quantization support in local inference",
                                 source="Hugging Face")
    assert site.topic_matches(actual_quantization, topic)

    # The older signal is outside the first 80 but still within the 21-day policy.
    archive = ([sample("Unrelated update " + str(i), source="GitHub", age=1)
                for i in range(80)]
               + [older, hf, gh, multi, dict(older),
                  sample("Very old open-source weights", age=22),
                  sample("Future open-source weights", age=-1),
                  sample("Shadow open-source weights", source="Hidden")])
    sources = dict(site.SOURCE_BY_NAME)
    sources["Hidden"] = {"status": "shadow"}
    selected = select_open_source_signals(
        archive, as_of=NOW, days=21,
        matches_topic=lambda x: site.topic_matches(x, topic),
        source_by_name=sources, parse_date=site.parse_date)
    urls = [x["url"] for x in selected]
    assert older["url"] in urls
    assert len(urls) == len(set(urls)) == 4
    assert urls == [x["url"] for x in sorted(
        selected, key=lambda x: (x["published"], x["url"]), reverse=True)]
    assert all(x["category"] == "Tools" for x in selected)

    feed = json.loads((ROOT / "data/open-source.json").read_text(encoding="utf-8"))
    news = json.loads((ROOT / "data/news.json").read_text(encoding="utf-8"))
    full = json.loads((ROOT / "data/archive.json").read_text(encoding="utf-8"))
    expected = site.open_source_current_signals(full["items"], feed["updated_at"])
    assert [x["url"] for x in feed["items"]] == [x["url"] for x in expected]
    assert not any("Jump Trading" in x["title"] for x in expected), (
        "Quantitative-finance signals must never enter Open Source"
    )
    assert news["updated_at"] == feed["updated_at"]
    html = (ROOT / "open-source/index.html").read_text(encoding="utf-8")
    block = html.split("<!-- SXF:SECTION_FEED_START -->", 1)[1].split(
        "<!-- SXF:SECTION_FEED_END -->", 1)[0]
    assert block.count('class="intel-card"') == len(expected)
    assert f'<strong id="sectionCount">{len(expected)}</strong>' in html
    print("PASS: Open Source topic precision, 21-day archive selection, deduplication, "
          f"category preservation and {len(expected)} matching HTML cards")


if __name__ == "__main__":
    main()
