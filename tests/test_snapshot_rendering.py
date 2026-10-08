#!/usr/bin/env python3
"""Regression checks for offline rendering and published route synchronization."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update_news.py"
SNAPSHOT_PATHS = (
    ROOT / "data" / "archive.json",
    ROOT / "data" / "news.json",
    ROOT / "data" / "source-shadow.json",
    ROOT / "data" / "model-history.json",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated_manifest():
    files = list(ROOT.rglob("*.html")) + [ROOT / "sitemap.xml", ROOT / "_redirects"]
    return {
        str(path.relative_to(ROOT)): digest(path)
        for path in files
        if path.is_file() and ".git" not in path.parts
    }


def parity_test():
    """A second render from unchanged input must produce byte-identical artifacts."""
    before_files = generated_manifest()
    before_data = {str(path): digest(path) for path in SNAPSHOT_PATHS}
    subprocess.run(
        [sys.executable, str(SCRIPT), "--render-only"], check=True, cwd=ROOT,
    )
    after_files = generated_manifest()
    after_data = {str(path): digest(path) for path in SNAPSHOT_PATHS}
    modified = sorted(k for k in before_files.keys() | after_files.keys()
                      if before_files.get(k) != after_files.get(k))
    assert not modified, f"Offline rebuild changed HTML/SEO artifacts: {modified[:30]}"
    assert before_data == after_data, "Render-only changed persisted feed data"
    print(f"PASS: {len(before_files)} generated files identical after offline rebuild")


def unit_test():
    """An approved slug change updates only route fields and never collects feeds."""
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("feed_snapshot_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    url = "https://example.test/signal"
    prior = "https://sxf.si/signals/old-name/"
    updated = "https://sxf.si/signals/new-name/"
    metadata = {"updated_at": "2026-10-08T10:00:00Z", "source_health": {"ok": True}}
    archive_row = {
        "url": url, "signal_slug": "old-name", "signal_url": prior,
        "title": "Sample AI launch", "category": "Models", "source": "OpenAI",
        "published": "2026-10-08T10:00:00Z", "summary": "Relevant description",
    }
    public_row = {
        "url": url, "signal_url": prior, "title": archive_row["title"],
        "published": archive_row["published"],
    }
    with tempfile.TemporaryDirectory() as tmp:
        module.ARCHIVE_OUT = Path(tmp) / "archive.json"
        module.OUT = Path(tmp) / "news.json"
        module.SLUG_ALIASES = {url: "new-name"}
        archive_payload = {**metadata, "items": [archive_row]}
        news_payload = {**metadata, "items": [public_row]}
        module.ARCHIVE_OUT.write_text(json.dumps(archive_payload), encoding="utf-8")
        module.OUT.write_text(json.dumps(news_payload), encoding="utf-8")

        visits = []
        module.render_site = lambda archive, current: visits.append((archive, current))
        module.fetch = lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Offline build must not fetch sources")
        )
        module.run_source_adapter = module.fetch

        module.render_from_snapshots()
        assert visits[0][0][0]["signal_url"] == prior
        assert json.loads(module.ARCHIVE_OUT.read_text()) == archive_payload
        assert json.loads(module.OUT.read_text()) == news_payload

        module.render_from_snapshots(sync_aliases=True)
        assert visits[-1][0][0]["signal_url"] == updated
        assert visits[-1][1][0]["signal_url"] == updated
        archive_after = json.loads(module.ARCHIVE_OUT.read_text())
        news_after = json.loads(module.OUT.read_text())
        assert archive_after["items"][0]["signal_slug"] == "new-name"
        assert archive_after["items"][0]["signal_url"] == updated
        assert news_after["items"][0]["signal_url"] == updated
        assert archive_after["updated_at"] == metadata["updated_at"]
        assert archive_after["source_health"] == metadata["source_health"]

        first_archive_hash = digest(module.ARCHIVE_OUT)
        first_news_hash = digest(module.OUT)
        module.render_from_snapshots(sync_aliases=True)
        assert digest(module.ARCHIVE_OUT) == first_archive_hash
        assert digest(module.OUT) == first_news_hash

    print("PASS: offline rendering and alias synchronization are safe and idempotent")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parity", action="store_true")
    args = parser.parse_args()
    if args.parity:
        parity_test()
    else:
        unit_test()


if __name__ == "__main__":
    main()
