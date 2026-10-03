#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_ai_auto_enrichment import select_candidate, within_limits


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def candidate(title, priority=190, hours_old=4, evidence_hash="a" * 64):
    now = datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)
    return {
        "title": title,
        "priority_score": priority,
        "evidence_hash": evidence_hash,
        "signal_slug": "legacy-slug",
        "signal_url": "https://sxf.si/signals/legacy-slug/",
        "evidence": {
            "signal": {
                "title": title,
                "url": "https://example.com/source",
                "published": (now - timedelta(hours=hours_old)).isoformat().replace("+00:00", "Z"),
            }
        },
    }


def trial():
    return {
        "max_age_hours": 48,
        "min_priority_score": 175,
        "max_attempts_per_day": 3,
        "max_published_per_day": 3,
        "max_published_per_month": 60,
        "max_monthly_estimated_cost_usd": 5,
    }


def main():
    now = datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)

    hot = candidate("Introducing GPT-7 Sol API")
    picked = select_candidate([hot], [], {"attempts": []}, trial(), now)
    expect(picked is hot, "fresh release/model candidate should pass preflight")

    stale = candidate("Introducing GPT-7 Sol API", hours_old=60)
    expect(select_candidate([stale], [], {"attempts": []}, trial(), now) is None, "stale candidate must be skipped")

    roundup = candidate("GPT-7 model guide")
    expect(select_candidate([roundup], [], {"attempts": []}, trial(), now) is None, "model guide must be blocked")

    weak = candidate("Introducing GPT-7 Sol API", priority=150)
    expect(select_candidate([weak], [], {"attempts": []}, trial(), now) is None, "weak priority must be skipped")

    attempted_state = {"attempts": [{"evidence_hash": "a" * 64, "date": "2026-10-03"}]}
    expect(select_candidate([hot], [], attempted_state, trial(), now) is None, "same evidence must not spend twice")

    reviewed = [{"source_url": "https://example.com/source"}]
    expect(select_candidate([hot], reviewed, {"attempts": []}, trial(), now) is None, "published source must not reprocess")

    expect(within_limits({"attempts": [], "published": []}, trial(), now), "empty state should be within limits")
    full = {
        "attempts": [{"date": "2026-10-03", "estimated_cost_usd": 0.02} for _ in range(3)],
        "published": [],
    }
    expect(not within_limits(full, trial(), now), "daily attempt cap must stop API usage")

    print("AI hot-news auto enrichment tests passed")


if __name__ == "__main__":
    main()
