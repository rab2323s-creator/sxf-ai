"""Human approval ledger and candidate inbox for SXF news.

The automated relevance/importance models only recommend. New stories enter
the public archive solely after an exact identity match to a human approval.
The frozen legacy allowlist preserves already-published historical signals.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DECISIONS_VERSION = "sxf-editorial-decisions-v1"
INBOX_VERSION = "sxf-editorial-inbox-v1"
BASELINE_VERSION = "sxf-editorial-legacy-v1"
DECISION_STATES = {"approved", "rejected", "hold"}
INBOX_LIMIT = 500


class EditorialConfigError(ValueError):
    """Invalid editorial files must fail closed, not make new items public."""


def identity(row):
    return (row.get("url", ""), row.get("title", ""), row.get("source", ""))


def valid_http_url(value):
    if not isinstance(value, str):
        return False
    result = urlparse(value)
    return result.scheme == "https" and bool(result.netloc) and not result.username and not result.password


def read_decisions(path: Path):
    """Strictly validate; a typo must never turn off the human gate."""
    if not path.is_file():
        raise EditorialConfigError(f"Missing editorial decision ledger: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != DECISIONS_VERSION:
        raise EditorialConfigError("Unsupported editorial decision ledger version")
    entries = payload.get("decisions")
    if not isinstance(entries, list):
        raise EditorialConfigError("Editorial decisions must be an array")
    indexed = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise EditorialConfigError("Editorial decision must be an object")
        url, title, source = identity(entry)
        if (not valid_http_url(url) or not isinstance(title, str) or not title.strip()
                or not isinstance(source, str) or not source.strip()
                or entry.get("decision") not in DECISION_STATES
                or not isinstance(entry.get("reviewed_by"), str) or not entry["reviewed_by"].strip()
                or not isinstance(entry.get("reviewed_at"), str)):
            raise EditorialConfigError(f"Invalid editorial decision: {url!r}")
        try:
            datetime.fromisoformat(entry["reviewed_at"].replace("Z", "+00:00"))
        except (TypeError, ValueError):
            raise EditorialConfigError(f"Invalid approval timestamp: {url!r}") from None
        if url in indexed:
            raise EditorialConfigError(f"Duplicate editorial URL: {url}")
        indexed[url] = entry
    return indexed


def read_legacy_urls(path: Path):
    if not path.is_file():
        raise EditorialConfigError(f"Missing frozen legacy publication list: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != BASELINE_VERSION:
        raise EditorialConfigError("Unsupported legacy publication list version")
    urls = payload.get("urls")
    if not isinstance(urls, list) or len(set(urls)) != len(urls):
        raise EditorialConfigError("Legacy publication URLs must be a unique array")
    if not all(valid_http_url(url) for url in urls):
        raise EditorialConfigError("Invalid legacy publication URL")
    return frozenset(urls)


def exact_decision(row, decisions):
    """A changed title or publisher cannot inherit approval for the same URL."""
    entry = decisions.get(row.get("url", ""))
    if not entry or identity(entry) != identity(row):
        return None
    return entry["decision"]


def is_human_approved(row, decisions):
    return exact_decision(row, decisions) == "approved"


def publication_decision(row, decisions, legacy_urls, assess):
    """Return the usual NewsDecision without weakening its public contract."""
    from news_relevance import NewsDecision

    state = exact_decision(row, decisions)
    if state == "rejected":
        return NewsDecision("reject", "human_rejected")
    if state == "hold":
        return NewsDecision("review", "human_hold")
    if state == "approved":
        # New approvals must satisfy minimum SEO evidence before becoming public.
        if not row.get("seo_eligible", False):
            return NewsDecision("review", "human_approved_awaiting_quality")
        return NewsDecision("accept", "human_approved")
    if row.get("url") in legacy_urls:
        return assess(row.get("title", ""), row.get("summary", ""),
                      row.get("source", ""), row.get("url", ""))
    return NewsDecision("review", "awaiting_human_approval")


def load_inbox(path: Path):
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != INBOX_VERSION:
        raise EditorialConfigError("Unsupported editorial inbox version")
    items = payload.get("items")
    if not isinstance(items, list):
        raise EditorialConfigError("Editorial inbox items must be an array")
    return items


def build_inbox(existing, candidates, *, now, decisions, legacy_urls, assess,
                prepare, maximum=INBOX_LIMIT):
    """Merge candidate evidence without losing old pending decisions.

    New fetched content supersedes stale summary/quality data; existing
    candidates remain reviewable even if a feed drops an older article.
    """
    by_url = {}
    for row in existing:
        if not isinstance(row, dict) or not valid_http_url(row.get("url")):
            continue
        if row.get("url") in legacy_urls:
            continue
        by_url[row["url"]] = dict(row)
    for row in candidates:
        if not isinstance(row, dict) or not valid_http_url(row.get("url")):
            continue
        if not row.get("title") or not row.get("source") or not row.get("published"):
            continue
        if row["url"] in legacy_urls:
            continue
        before = by_url.get(row["url"], {})
        doc = dict(before)
        doc.update({k: row[k] for k in ("url", "title", "source", "published")})
        # Never erase a substantive summary with a later empty feed snippet.
        if row.get("summary"):
            doc["summary"] = row["summary"]
        elif not doc.get("summary"):
            doc["summary"] = ""
        doc["first_seen"] = before.get("first_seen") or now
        doc["last_seen"] = now
        by_url[row["url"]] = doc
    ordered = sorted(by_url.values(), key=lambda row: (row.get("published") or "", row["url"]), reverse=True)
    selected = []
    for row in ordered:
        verdict = assess(row["title"], row.get("summary", ""), row["source"], row["url"])
        quality = prepare([row])[0]
        # Shadow/other adapter data must retain the warning even when its
        # body is too thin for a public SEO page.
        row["editorial_status"] = verdict.status
        row["editorial_reason"] = verdict.reason
        row["seo_eligible"] = bool(quality.get("seo_eligible"))
        row["seo_quality_score"] = quality.get("seo_quality_score", 0)
        row["decision"] = exact_decision(row, decisions) or "pending"
        selected.append(row)
        if len(selected) >= maximum:
            break
    return selected


def approved_inbox_items(inbox, decisions, legacy_urls, prepare, parse_date, cutoff):
    """Re-ingest an approved, previously discovered story even if RSS moved on."""
    eligible = []
    for row in inbox:
        if row.get("url") in legacy_urls or not is_human_approved(row, decisions):
            continue
        published = parse_date(row.get("published", ""))
        if published is None or published < cutoff:
            continue
        prepared = prepare([row])[0]
        if not prepared.get("seo_eligible"):
            continue
        eligible.append({key: row.get(key) for key in
                         ("title", "url", "source", "published", "summary", "category", "tags")
                         if key in row})
    return eligible
