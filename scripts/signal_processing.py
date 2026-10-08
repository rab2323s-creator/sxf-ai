"""Pure feed processing and selection logic, separated from site rendering.

Every site-specific dependency is supplied via SignalProcessingContext.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SignalProcessingContext:
    clean_summary: object
    categorize: object
    classify_tags: object
    slug_aliases: object
    signal_slug: object
    base_url: object
    signal_score: object
    seo_quality: object
    seo_signal_eligible: object
    editorial_units: object
    valid_url: object
    parse_date: object
    source_by_name: object
    source_expansion_names: object
    source_expansion_max_current_per_source: object
    source_expansion_max_current_total: object
    max_items: object


def prepare_items(items, context: SignalProcessingContext):
    clean_summary = context.clean_summary
    categorize = context.categorize
    classify_tags = context.classify_tags
    slug_aliases = context.slug_aliases
    signal_slug = context.signal_slug
    base_url = context.base_url
    signal_score = context.signal_score
    seo_quality = context.seo_quality
    seo_signal_eligible = context.seo_signal_eligible
    editorial_units = context.editorial_units

    prepared = []
    for item in items:
        row = dict(item)
        row["summary"] = clean_summary(row.get("summary", ""))
        row["category"] = categorize(row["title"], row["source"])
        row["tags"] = classify_tags(row["title"], row["source"], row["category"])
        row["signal_slug"] = slug_aliases.get(row["url"]) or row.get("signal_slug") or signal_slug(row)
        row["signal_url"] = f'{base_url}/signals/{row["signal_slug"]}/'
        score, factors = signal_score(row)
        row["signal_score"] = score
        row["score_factors"] = factors
        quality_score, quality_factors = seo_quality(row)
        row["seo_quality_score"] = quality_score
        row["seo_quality_factors"] = quality_factors
        row["seo_eligible"] = seo_signal_eligible(row, quality_score)
        row["editorial"] = editorial_units(row)
        prepared.append(row)
    return prepared


def load_items(path):
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("items", []) if isinstance(payload, dict) else []
    except Exception:
        return []


def merge_archive(existing_items, incoming_items, context: SignalProcessingContext):
    valid_url = context.valid_url
    categorize = context.categorize
    classify_tags = context.classify_tags
    clean_summary = context.clean_summary
    parse_date = context.parse_date

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    by_url = {item.get("url"): dict(item) for item in existing_items if valid_url(item.get("url", ""))}

    for incoming in incoming_items:
        url = incoming["url"]
        previous = by_url.get(url, {})
        merged = dict(previous)
        merged.update(incoming)
        if not merged.get("summary") and previous.get("summary"):
            merged["summary"] = previous["summary"]
            merged["summary_origin"] = previous.get("summary_origin", "")
        merged["category"] = categorize(merged["title"], merged["source"])
        merged["tags"] = classify_tags(merged["title"], merged["source"], merged["category"])
        merged["first_seen"] = previous.get("first_seen") or now_iso

        before = {
            "title": previous.get("title"),
            "source": previous.get("source"),
            "published": previous.get("published"),
            "category": previous.get("category"),
            "summary": clean_summary(previous.get("summary", "")),
            "tags": previous.get("tags", []),
        }
        after = {
            "title": merged.get("title"),
            "source": merged.get("source"),
            "published": merged.get("published"),
            "category": merged.get("category"),
            "summary": clean_summary(merged.get("summary", "")),
            "tags": merged.get("tags", []),
        }
        merged["modified_at"] = now_iso if before != after else previous.get("modified_at", now_iso)
        merged["last_seen"] = now_iso
        by_url[url] = merged

    valid = []
    for item in by_url.values():
        if not valid_url(item.get("url", "")):
            continue
        if parse_date(item.get("published", "")) is None:
            continue
        if not item.get("first_seen"):
            item["first_seen"] = now_iso
        if not item.get("modified_at"):
            item["modified_at"] = now_iso
        valid.append(item)
    valid.sort(key=lambda x: parse_date(x["published"]), reverse=True)
    return prepare_items(valid, context)


def client_item(item):
    return {
        "title": item["title"],
        "url": item["url"],
        "signal_url": item["signal_url"],
        "source": item["source"],
        "published": item["published"],
        "category": item["category"],
        "tags": item.get("tags", []),
        "signal_score": item.get("signal_score", 0),
    }


def select_current_items(archive, cutoff, context: SignalProcessingContext):
    parse_date = context.parse_date
    source_by_name = context.source_by_name
    source_expansion_names = context.source_expansion_names
    source_expansion_max_current_per_source = context.source_expansion_max_current_per_source
    source_expansion_max_current_total = context.source_expansion_max_current_total
    max_items = context.max_items

    selected = []
    expansion_counts = {name: 0 for name in source_expansion_names}
    expansion_total = 0

    for item in archive:
        published = parse_date(item.get("published", ""))
        if published is None or published < cutoff:
            continue

        source = item.get("source", "")
        source_config = source_by_name.get(source, {})
        status = source_config.get("status", "live")
        if status in {"shadow", "disabled"}:
            continue

        max_current = source_config.get("max_current", max_items)
        source_selected = sum(1 for selected_item in selected if selected_item.get("source") == source)
        if source_selected >= max_current:
            continue

        if source in source_expansion_names:
            if expansion_counts[source] >= source_expansion_max_current_per_source:
                continue
            if expansion_total >= source_expansion_max_current_total:
                continue
            expansion_counts[source] += 1
            expansion_total += 1

        selected.append(item)
        if len(selected) >= max_items:
            break

    return selected
