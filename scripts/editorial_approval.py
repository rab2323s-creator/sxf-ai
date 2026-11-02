"""Human approval ledger and candidate inbox for SXF news.

The automated relevance/importance models only recommend. New stories enter
the public archive solely after an exact identity match to a human approval.
The frozen legacy allowlist preserves already-published historical signals.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

DECISIONS_VERSION = "sxf-editorial-decisions-v1"
INBOX_VERSION = "sxf-editorial-inbox-v1"
BASELINE_VERSION = "sxf-editorial-legacy-v1"
INDEX_BASELINE_VERSION = "sxf-editorial-legacy-indexable-v1"
DECISION_STATES = {"approved", "hold"}
INBOX_LIMIT = 500
INBOX_MAX_AGE_HOURS = 168


class EditorialConfigError(ValueError):
    """Invalid editorial files must fail closed, not make new items public."""


def rejection_fingerprint(url):
    """One-way URL identifier only: do not retain rejected title or summary."""
    if not valid_http_url(url):
        raise EditorialConfigError("Cannot fingerprint invalid URL")
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def is_rejected(row, decisions):
    return rejection_fingerprint(row.get("url", "")) in getattr(decisions, "rejected_fingerprints", frozenset())


class DecisionLedger(dict):
    """Approval decisions plus content-free rejected URL fingerprints."""

    def __init__(self, entries, rejected_fingerprints=()):
        super().__init__(entries)
        self.rejected_fingerprints = frozenset(rejected_fingerprints)


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
    hashes = payload.get("rejected_fingerprints", [])
    if (not isinstance(hashes, list) or len(hashes) != len(set(hashes)) or
            not all(isinstance(value, str) and len(value) == 64 and
                    all(c in "0123456789abcdef" for c in value) for value in hashes)):
        raise EditorialConfigError("Rejected fingerprints must be unique SHA-256 strings")
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
    # A URL cannot simultaneously be blocked and approved/held. Reject
    # reversal must clear its fingerprint in the same GitHub CAS write.
    if any(rejection_fingerprint(url) in hashes for url in indexed):
        raise EditorialConfigError("Conflicting approval/hold and rejected fingerprint")
    return DecisionLedger(indexed, hashes)


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


def read_legacy_indexable_urls(path: Path):
    if not path.is_file():
        raise EditorialConfigError(f"Missing historical indexable baseline: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != INDEX_BASELINE_VERSION:
        raise EditorialConfigError("Invalid historical indexable baseline")
    urls = payload.get("urls")
    if (not isinstance(urls, list) or len(urls) != len(set(urls))
            or not all(valid_http_url(url) for url in urls)):
        raise EditorialConfigError("Invalid historical indexable source URLs")
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
    if is_rejected(row, decisions):
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
                prepare, maximum=INBOX_LIMIT, window_hours=INBOX_MAX_AGE_HOURS):
    """Retain rejected and held rows for reversible, auditable owner decisions.

    Rejected stories stay private to the noindex admin inbox; they NEVER
    enter the publication feed. The normal quota and age window only limit
    undecided stories, not owner decisions. The ledger remains authoritative.
    """
    observed = datetime.fromisoformat(now.replace("Z", "+00:00"))
    cutoff = observed - timedelta(hours=window_hours)
    by_url = {}
    for row in list(existing) + list(candidates):
        if not isinstance(row, dict) or not valid_http_url(row.get("url")):
            continue
        url = row["url"]
        state = exact_decision(row, decisions)
        rejected = is_rejected(row, decisions)
        if url in legacy_urls or state == "approved":
            continue
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            continue
        if not isinstance(row.get("source"), str) or not row["source"].strip():
            continue
        try:
            published = datetime.fromisoformat(row["published"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if (published.tzinfo is None or published > observed + timedelta(hours=1)
                or (published < cutoff and state != "hold" and not rejected)):
            continue
        old = by_url.get(url, {})
        doc = dict(old)
        for key in ("url", "title", "source", "published"):
            doc[key] = row[key]
        if row.get("summary"):
            doc["summary"] = row["summary"]
        elif not doc.get("summary"):
            doc["summary"] = ""
        for key in ("rejection_stage", "rejection_reason"):
            if row.get(key):
                doc[key] = row[key]
        doc["first_seen"] = old.get("first_seen") or row.get("first_seen") or now
        doc["last_seen"] = now
        doc["decision"] = "rejected" if rejected else (state or "pending")
        by_url[url] = doc
    selected = []
    pending_count = 0
    for row in sorted(by_url.values(), key=lambda r:
                      (r["decision"] != "pending", r["published"], r["url"]), reverse=True):
        # Keep all owner-reviewed Hold/Reject records even when the fresh
        # pending queue is full. This supports reversal months later.
        if row["decision"] == "pending":
            if pending_count >= maximum:
                continue
            pending_count += 1
        verdict = assess(row["title"], row.get("summary", ""), row["source"], row["url"])
        quality = prepare([row])[0]
        row["editorial_status"] = verdict.status
        row["editorial_reason"] = verdict.reason
        row["seo_eligible"] = bool(quality.get("seo_eligible"))
        row["seo_quality_score"] = quality.get("seo_quality_score", 0)
        selected.append(row)
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


def enforce_noindex_on_html(html):
    """Safely normalize legacy Signal heads for both search crawlers.

    Historic routes have inconsistent markup; reject duplicate directives
    while adding missing directives. Keep pages fetchable for deindexing.
    """
    if len(re.findall(r"<head\b[^>]*>", html, flags=re.I)) != 1:
        raise EditorialConfigError("Legacy Signal HTML must contain one <head>")
    if len(re.findall(r"</head\s*>", html, flags=re.I)) != 1:
        raise EditorialConfigError("Legacy Signal HTML must contain one </head>")

    for name in ("robots", "googlebot"):
        # Match a full meta element, then examine its attributes. Older pages
        # can use single quotes, reorder the attributes, or lack content.
        tags = []
        for tag in re.finditer(r"<meta\b[^>]*>", html, flags=re.I):
            if re.search(r"\bname\s*=\s*(['\"])" + re.escape(name) + r"\1", tag.group(), flags=re.I):
                tags.append(tag)
        if len(tags) > 1:
            raise EditorialConfigError(f"Duplicate {name} directives in legacy Signal HTML")
        if not tags:
            html = re.sub(r"</head\s*>",
                f'<meta name="{name}" content="noindex,follow" />\n</head>',
                html, count=1, flags=re.I)
            continue
        tag = tags[0]
        old_tag = tag.group()
        content_attribute = re.compile(r"\bcontent\s*=\s*(['\"])[^'\"]*\1", flags=re.I)
        new_tag, replacements = content_attribute.subn('content="noindex,follow"', old_tag)
        if replacements != 1:
            # Existing malformed/attribute-less directives become canonical.
            new_tag = f'<meta name="{name}" content="noindex,follow" />'
        html = html[:tag.start()] + new_tag + html[tag.end():]
    return html

def retire_unapproved_signal_routes(directory, allowed_slugs):
    """Keep existing URLs crawlable as noindex to support search deindexing."""
    count = 0
    for page in sorted(directory.glob("*/index.html")):
        if page.parent.name in allowed_slugs:
            continue
        original = page.read_text(encoding="utf-8")
        updated = enforce_noindex_on_html(original)
        if original != updated:
            page.write_text(updated, encoding="utf-8")
            count += 1
    return count
