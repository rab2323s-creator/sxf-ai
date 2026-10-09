"""Deterministic Open Source topic selection from the canonical archive.

The 21-day window is anchored to a persisted snapshot timestamp, not the
current clock, so render-only builds are reproducible.
"""
from __future__ import annotations

from datetime import timedelta


def select_open_source_signals(archive, *, as_of, days, matches_topic, source_by_name, parse_date):
    if as_of is None or as_of.tzinfo is None:
        raise ValueError("Open Source selection requires a timezone-aware timestamp")
    cutoff = as_of - timedelta(days=days)
    candidates = []
    for item in archive:
        published = parse_date(item.get("published", ""))
        if published is None or published < cutoff or published > as_of:
            continue
        if not item.get("url") or not item.get("signal_url"):
            continue
        config = source_by_name.get(item.get("source", ""), {})
        if config.get("status", "live") not in {"live", "canary"}:
            continue
        if matches_topic(item):
            candidates.append((published, item))

    candidates.sort(key=lambda pair: (pair[0], pair[1]["url"]), reverse=True)
    selected, seen = [], set()
    for _, item in candidates:
        url = item["url"]
        if url not in seen:
            selected.append(item)
            seen.add(url)
    return selected
