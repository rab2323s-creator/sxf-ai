#!/usr/bin/env python3
"""Offline regressions: fail-closed human approval, no auto-publishing."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from editorial_approval import (
    DECISIONS_VERSION, BASELINE_VERSION, INBOX_VERSION, EditorialConfigError,
    approved_inbox_items, build_inbox, exact_decision, publication_decision,
    read_decisions, read_legacy_urls,
)
from news_relevance import NewsDecision


def item(url="https://example.org/launch", title="Introducing Frontier AI 4",
         source="Anthropic", summary="A primary-source AI model release with a long technical summary."):
    return {
        "url": url, "title": title, "source": source, "summary": summary,
        "published": datetime.now(timezone.utc).isoformat(),
    }


def assess(*args):
    return NewsDecision("accept", "automated_accept")


def prepare(rows):
    return [{**row, "seo_eligible": len(row.get("summary", "")) >= 45,
             "seo_quality_score": 74} for row in rows]


def parse_date(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def main():
    row = item()
    assert publication_decision({**row, "seo_eligible": True}, {}, set(), assess).status == "review"
    assert publication_decision(row, {}, {row["url"]}, assess).status == "accept"
    ledger = {row["url"]: {**row, "decision": "approved"}}
    assert exact_decision(row, ledger) == "approved"
    assert exact_decision({**row, "title": "Unverified change"}, ledger) is None
    assert publication_decision({**row, "seo_eligible": True}, ledger, set(), assess).status == "accept"
    assert publication_decision({**row, "seo_eligible": False}, ledger, set(), assess).status == "review"
    for state, expected in (("hold", "review"),):
        ledger[row["url"]]["decision"] = state
        assert publication_decision({**row, "seo_eligible": True}, ledger, {row["url"]}, assess).status == expected
    ledger[row["url"]]["decision"] = "approved"

    inbox = build_inbox([], [row], now=datetime.now(timezone.utc).isoformat(),
                        decisions={}, legacy_urls=set(), assess=assess, prepare=prepare)
    assert len(inbox) == 1 and inbox[0]["decision"] == "pending"
    assert inbox[0]["editorial_status"] == "accept", "Filter accept is a recommendation, not publication"
    again = build_inbox(inbox, [{**row, "summary": ""}], now=datetime.now(timezone.utc).isoformat(),
                        decisions=ledger, legacy_urls=set(), assess=assess, prepare=prepare)
    assert again == [], "Approved stories leave the temporary inbox immediately"
    assert build_inbox([], [row], now=datetime.now(timezone.utc).isoformat(),
                       decisions={}, legacy_urls={row["url"]}, assess=assess, prepare=prepare) == []
    cutoff = datetime.now(timezone.utc) - timedelta(days=35)
    assert len(approved_inbox_items(inbox, ledger, set(), prepare, parse_date, cutoff)) == 1
    assert approved_inbox_items(inbox, ledger, {row["url"]}, prepare, parse_date, cutoff) == []
    assert approved_inbox_items(inbox, {}, set(), prepare, parse_date, cutoff) == []
    thin = [{**row, "summary": "Too short"}]
    assert approved_inbox_items(thin, ledger, set(), prepare, parse_date, cutoff) == []

    with TemporaryDirectory() as folder:
        root = Path(folder)
        decisions = root / "decisions.json"
        baseline = root / "baseline.json"
        decisions.write_text(json.dumps({"version": DECISIONS_VERSION, "decisions": [
            {**row, "decision": "approved", "reviewed_by": "github:editor",
             "reviewed_at": "2026-11-02T10:00:00Z"}]}))
        baseline.write_text(json.dumps({"version": BASELINE_VERSION, "urls": [row["url"]]}))
        assert read_decisions(decisions)[row["url"]]["decision"] == "approved"
        assert row["url"] in read_legacy_urls(baseline)
        decisions.write_text(json.dumps({"version": DECISIONS_VERSION, "decisions": [
            {**row, "decision": "approved", "reviewed_by": "github:editor",
             "reviewed_at": "2026-11-02T10:00:00Z"}] * 2}))
        try:
            read_decisions(decisions)
        except EditorialConfigError:
            pass
        else:
            raise AssertionError("Duplicate decisions must fail closed")
        decisions.unlink()
        try:
            read_decisions(decisions)
        except EditorialConfigError:
            pass
        else:
            raise AssertionError("Missing ledger must fail closed")

    live_decisions = read_decisions(ROOT / "data" / "editorial-decisions.json")
    baseline = read_legacy_urls(ROOT / "data" / "editorial-legacy-published.json")
    archive = json.loads((ROOT / "data" / "archive.json").read_text(encoding="utf-8"))
    feed = json.loads((ROOT / "data" / "news.json").read_text(encoding="utf-8"))
    archive_by_url = {row["url"]: row for row in archive["items"]}
    assert all(
        row["url"] in baseline or (
            exact_decision(row, live_decisions) == "approved"
            and archive_by_url.get(row["url"], {}).get("seo_eligible") is True
        )
        for row in feed["items"]
    ), "Current feed must be grandfathered or explicitly human-approved and SEO-qualified"
    assert all(row["url"] in {x["url"] for x in archive["items"]} for row in feed["items"])
    assert all(entry["decision"] in {"approved", "hold"} for entry in live_decisions.values()), "Only explicit owner decisions are allowed"
    assert not live_decisions.rejected_fingerprints, "No unexplained rejection fingerprints in curated launch"
    from editorial_approval import DecisionLedger, rejection_fingerprint
    rejected = DecisionLedger({}, {rejection_fingerprint(row["url"])})
    assert publication_decision(row, rejected, set(), assess).status == "reject"
    retained = build_inbox([], [row], now=datetime.now(timezone.utc).isoformat(),
                           decisions=rejected, legacy_urls=set(), assess=assess, prepare=prepare)
    assert len(retained) == 1 and retained[0]["decision"] == "rejected"
    assert publication_decision({**row, "seo_eligible": True}, rejected, set(), assess).status == "reject"
    print("PASS: human approval, stale identity, holds, quality checks, legacy feed")


if __name__ == "__main__":
    main()
