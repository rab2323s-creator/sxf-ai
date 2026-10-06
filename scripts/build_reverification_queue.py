#!/usr/bin/env python3
"""Build deterministic SXF model reverification queue from canonical provenance."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "model-pricing.json"
OUTPUT_PATH = ROOT / "data" / "model-reverification.json"

POLICY = {
    "preview": 7,
    "current_official_paid": 30,
    "current_other": 45,
    "legacy": 90,
    "deprecated": 180,
}

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATUS_RANK = {"overdue": 0, "due": 1, "fresh": 2}


class FreshnessError(ValueError):
    pass


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise FreshnessError(f"Cannot load {path.relative_to(ROOT)}: {exc}") from exc


def parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise FreshnessError(f"{label} must be YYYY-MM-DD") from exc


def review_interval(model: dict) -> tuple[str, int]:
    lifecycle = model["lifecycle"]["status"]
    if lifecycle == "preview":
        return "preview", POLICY["preview"]
    if lifecycle == "current":
        if model.get("pricing_status") == "official-paid":
            return "current_official_paid", POLICY["current_official_paid"]
        return "current_other", POLICY["current_other"]
    if lifecycle == "legacy":
        return "legacy", POLICY["legacy"]
    if lifecycle == "deprecated":
        return "deprecated", POLICY["deprecated"]
    raise FreshnessError(f"{model['model_id']}: unsupported lifecycle {lifecycle!r}")


def status_for(anchor: date, due: date) -> str:
    if due < anchor:
        return "overdue"
    if due == anchor:
        return "due"
    return "fresh"


def priority_for(model: dict, status: str) -> str:
    lifecycle = model["lifecycle"]["status"]
    if lifecycle == "preview" and status in {"due", "overdue"}:
        return "critical"
    if lifecycle == "current" and model.get("pricing_status") == "official-paid" and status in {"due", "overdue"}:
        return "high"
    if lifecycle == "current":
        return "medium"
    return "low"


def source_urls(model: dict) -> list[str]:
    evidence = model.get("provenance", {}).get("evidence", {})
    keys = ("model_identity", "pricing", "context_window", "lifecycle", "capabilities", "access")
    return sorted({evidence[key] for key in keys if evidence.get(key)})


def build_queue(catalog: dict) -> dict:
    anchor = parse_date(catalog["source_verified"], "catalog.source_verified")
    items = []
    for model in catalog["models"]:
        verified = parse_date(model["provenance"]["verified_at"], f"{model['model_id']}.verified_at")
        if verified > anchor:
            raise FreshnessError(f"{model['model_id']}: verified_at cannot be after source_verified")
        policy_key, interval = review_interval(model)
        due = verified + timedelta(days=interval)
        status = status_for(anchor, due)
        age = (anchor - verified).days
        overdue_days = max(0, (anchor - due).days)
        item = {
            "model_id": model["model_id"],
            "provider": model["provider"],
            "model": model["model"],
            "lifecycle_status": model["lifecycle"]["status"],
            "pricing_status": model["pricing_status"],
            "verified_at": verified.isoformat(),
            "age_days": age,
            "policy": policy_key,
            "review_interval_days": interval,
            "due_at": due.isoformat(),
            "status": status,
            "priority": priority_for(model, status),
            "overdue_days": overdue_days,
            "review_scope": ["identity", "pricing", "specs", "lifecycle"],
            "source_urls": source_urls(model),
        }
        items.append(item)

    items.sort(key=lambda item: (
        STATUS_RANK[item["status"]],
        PRIORITY_RANK[item["priority"]],
        item["due_at"],
        item["provider"].lower(),
        item["model_id"],
    ))

    summary = {
        "total": len(items),
        "fresh": sum(item["status"] == "fresh" for item in items),
        "due": sum(item["status"] == "due" for item in items),
        "overdue": sum(item["status"] == "overdue" for item in items),
        "critical": sum(item["priority"] == "critical" for item in items),
        "high": sum(item["priority"] == "high" for item in items),
    }

    return {
        "schema_version": "1.0",
        "as_of": anchor.isoformat(),
        "policy": {
            "preview_days": POLICY["preview"],
            "current_official_paid_days": POLICY["current_official_paid"],
            "current_other_days": POLICY["current_other"],
            "legacy_days": POLICY["legacy"],
            "deprecated_days": POLICY["deprecated"],
            "publication_policy": "Reverification queue is advisory; source changes create candidates and never auto-publish.",
        },
        "summary": summary,
        "items": items,
    }


def rendered(queue: dict) -> str:
    return json.dumps(queue, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        catalog = load_json(CATALOG_PATH)
        queue = build_queue(catalog)
        expected = rendered(queue)
        if args.check:
            actual = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
            if actual != expected:
                raise FreshnessError("data/model-reverification.json is stale. Run: python scripts/build_reverification_queue.py")
            print(
                f"Reverification queue OK: {queue['summary']['total']} models / "
                f"{queue['summary']['overdue']} overdue / {queue['summary']['due']} due"
            )
            return 0
        OUTPUT_PATH.write_text(expected, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
        return 0
    except FreshnessError as exc:
        print(f"freshness error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
