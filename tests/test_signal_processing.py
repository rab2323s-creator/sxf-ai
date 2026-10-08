#!/usr/bin/env python3
"""Isolated regression tests for extracted, dependency-injected signal processing."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from signal_processing import SignalProcessingContext, prepare_items, merge_archive, select_current_items, client_item, load_items


def context():
    def date(value):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
    def tag(_title, _source, _category):
        return ["models"]
    return SignalProcessingContext(
        clean_summary=lambda value: value.strip(),
        categorize=lambda _title, _source: "Models",
        classify_tags=tag,
        slug_aliases={"https://test.test/one": "approved-slug"},
        signal_slug=lambda _item: "generated-slug",
        base_url="https://sxf.si",
        signal_score=lambda _row: (90, ["release"]),
        seo_quality=lambda _row: (85, ["primary"]),
        seo_signal_eligible=lambda _row, score: score >= 50,
        editorial_units=lambda row: {"why_it_matters": row["title"]},
        valid_url=lambda url: isinstance(url, str) and url.startswith("https://"),
        parse_date=date,
        source_by_name={
            "A": {"status": "live", "max_current": 1},
            "Shadow": {"status": "shadow", "max_current": 0},
        },
        source_expansion_names={"Expansion"},
        source_expansion_max_current_per_source=1,
        source_expansion_max_current_total=1,
        max_items=5,
    )


def make_item(url, source="A", published=None):
    return {
        "url": url,
        "title": "Model launch",
        "source": source,
        "published": published or datetime.now(timezone.utc).isoformat(),
        "summary": "  Verified new model.  ",
    }


def main():
    ctx = context()
    one = make_item("https://test.test/one")
    original = dict(one)
    result = prepare_items([one], ctx)
    assert one == original, "Preparation must not mutate input records"
    assert result[0]["signal_url"] == "https://sxf.si/signals/approved-slug/"
    assert result[0]["seo_eligible"] is True
    assert result[0]["signal_score"] == 90
    assert client_item(result[0])["signal_url"] == result[0]["signal_url"]
    assert "editorial" not in client_item(result[0])

    old = dict(one, summary="Stored evidence", first_seen="2026-10-01T00:00:00Z")
    new = dict(one, summary="")
    merged = merge_archive([old], [new], ctx)
    assert len(merged) == 1
    assert merged[0]["summary"] == "Stored evidence"
    assert merged[0]["first_seen"] == old["first_seen"]
    assert merged[0]["signal_slug"] == "approved-slug"
    assert old["summary"] == "Stored evidence", "Archive merge must not mutate inputs"

    now = datetime.now(timezone.utc)
    rows = [
        make_item("https://test.test/one", "A"),
        make_item("https://test.test/two", "A"),
        make_item("https://test.test/shadow", "Shadow"),
        make_item("https://test.test/exp1", "Expansion"),
        make_item("https://test.test/exp2", "Expansion"),
        make_item("https://test.test/old", "Expansion", (now - timedelta(days=50)).isoformat()),
    ]
    picked = select_current_items(rows, now - timedelta(days=21), ctx)
    assert [item["url"] for item in picked] == ["https://test.test/one", "https://test.test/exp1"]

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "feed.json"
        assert load_items(path) == []
        path.write_text(json.dumps({"items": rows}))
        assert len(load_items(path)) == 6

    print("PASS: signal preprocessing, canonical aliases, archive history and source quotas")


if __name__ == "__main__":
    main()
