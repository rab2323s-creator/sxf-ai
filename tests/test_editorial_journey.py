#!/usr/bin/env python3
"""Owner-approval journey using a real RSS parser and the production decision gate.

Only fixture news and a temporary ledger are written; no production approvals.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
from editorial_approval import (build_inbox, read_decisions, publication_decision,
                                rejection_fingerprint, DecisionLedger,
                                read_legacy_indexable_urls)
from news_relevance import NewsDecision


def main():
    timestamp = datetime.now(timezone.utc)
    date = timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = f"""<rss><channel><item>
    <title>Routine operating updates</title>
    <link>https://blogs.microsoft.com/blog/sxf-fixture-owner-approval/</link>
    <pubDate>{date}</pubDate>
    <description>Documented change with clear source links, expected rollout dates and sufficient technical context to assess editorial quality.</description>
    </item></channel></rss>"""
    excluded = []
    accepted, metrics = update_news.parse_feed_with_metrics("Microsoft", rss, rejected_rows=excluded)
    assert accepted == [] and metrics["relevance_rejection_count"] == 1
    assert len(excluded) == 1 and excluded[0]["rejection_stage"] == "source_topic"
    story = excluded[0]
    assess = lambda *args: NewsDecision("review", "manual_review")
    prepare = lambda rows: [{**row, "seo_eligible": True, "seo_quality_score": 90} for row in rows]
    now = timestamp.isoformat()
    pending = build_inbox([], excluded, now=now, decisions=DecisionLedger({}),
                          legacy_urls=set(), assess=assess, prepare=prepare)
    assert len(pending) == 1 and pending[0]["decision"] == "pending"
    assert publication_decision({**story, "seo_eligible": True}, DecisionLedger({}),
                                set(), assess).status == "review"
    with TemporaryDirectory() as directory:
        path = Path(directory) / "decisions.json"
        def ledger(entries, rejected=()):
            path.write_text(json.dumps({"version": "sxf-editorial-decisions-v1",
                "decisions": entries, "rejected_fingerprints": list(rejected)}))
            return read_decisions(path)
        base = {"url": story["url"], "title": story["title"],
                "source": story["source"], "reviewed_by": "github:owner",
                "reviewed_at": now}
        hold = ledger([{**base, "decision": "hold"}])
        assert publication_decision({**story, "seo_eligible": True}, hold,
                                    set(), assess).status == "review"
        old = {**story, "published": (timestamp-timedelta(days=20)).isoformat()}
        held = build_inbox([old], [], now=now, decisions=hold, legacy_urls=set(),
                           assess=assess, prepare=prepare)
        assert len(held) == 1 and held[0]["decision"] == "hold"
        approved = ledger([{**base, "decision": "approved"}])
        assert publication_decision({**story, "seo_eligible": True}, approved,
                                    set(), assess).status == "accept"
        assert publication_decision({**story, "seo_eligible": False}, approved,
                                    set(), assess).status == "review"
        assert build_inbox(pending, [], now=now, decisions=approved,
                           legacy_urls=set(), assess=assess, prepare=prepare) == []
        rejected = ledger([], [rejection_fingerprint(story["url"])])
        assert publication_decision({**story, "seo_eligible": True}, rejected,
                                    set(), assess).status == "reject"
        assert build_inbox(pending, [], now=now, decisions=rejected,
                           legacy_urls=set(), assess=assess, prepare=prepare) == []
    frozen = read_legacy_indexable_urls(ROOT / "data" / "editorial-legacy-indexable.json")
    assert len(frozen) == 89, "Frozen historical indexable routes changed"
    print("PASS: source-filtered RSS -> pending -> held -> approved with SEO gate -> rejected")


if __name__ == "__main__":
    main()
