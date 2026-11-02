#!/usr/bin/env python3
"""Offline Chromium E2E editorial dashboard with a mocked GitHub API.

Never uses real credentials or modifies live GitHub data.
"""
from __future__ import annotations
import base64
import json
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = "https://example.org/sxf-editorial-browser-fixture"
STORY = {
    "url": URL, "title": "Source-verified frontier model API launch",
    "source": "OpenAI", "summary": "A sufficiently evidenced technical release",
    "published": "2026-11-02T10:00:00Z", "seo_eligible": True,
    "editorial_status": "review", "decision": "pending",
}
THIN = {
    **STORY, "url": URL + "-thin", "title": "Brief unverified headline",
    "seo_eligible": False,
}


def main():
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            return

    ledger = {"version": "sxf-editorial-decisions-v1",
              "decisions": [], "rejected_fingerprints": []}
    inbox = {"version": "sxf-editorial-inbox-v1", "items": [STORY, THIN]}
    written = []
    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 partial(Handler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("dialog", lambda d: d.accept())

            def mock_raw(route):
                route.fulfill(status=200, content_type="application/json",
                              headers={"Access-Control-Allow-Origin": "*"},
                              body=json.dumps(inbox))

            def mock_api(route):
                req = route.request
                headers = {"Access-Control-Allow-Origin": "*",
                           "Access-Control-Allow-Headers": "*",
                           "Access-Control-Allow-Methods": "GET, PUT, OPTIONS"}
                if req.method == "OPTIONS":
                    return route.fulfill(status=204, headers=headers)
                if req.url.rstrip("/").endswith("/user"):
                    result = {"login": "editor-fixture"}
                elif req.method == "PUT":
                    body = req.post_data_json
                    assert body["sha"] == "test-sha" + str(len(written))
                    assert body["branch"] == "main"
                    updated = json.loads(base64.b64decode(body["content"]))
                    assert updated["version"] == "sxf-editorial-decisions-v1"
                    written.append(updated)
                    ledger.clear()
                    ledger.update(updated)
                    result = {"content": {"sha": "test-sha" + str(len(written))}}
                else:
                    result = {"content": base64.b64encode(
                        (json.dumps(ledger)+"\\n").encode()).decode(),
                        "sha": "test-sha" + str(len(written))}
                route.fulfill(status=200, content_type="application/json",
                              headers=headers, body=json.dumps(result))

            page.route("https://raw.githubusercontent.com/**", mock_raw)
            page.route("https://api.github.com/**", mock_api)
            page.goto(f"http://127.0.0.1:{server.server_port}/admin/",
                      wait_until="networkidle")
            page.locator("#filter").select_option("all")
            assert page.locator(".story").count() == 2
            assert page.locator(".approve").first.is_disabled()
            page.locator("#token").fill("fixture-token-only")
            page.locator("#connect").click()
            page.get_by_text("Connected as editor-fixture", exact=False).wait_for()
            assert page.locator(".approve").first.is_enabled()
            page.locator(".approve").nth(1).click()
            page.get_by_text("Approval blocked:", exact=False).wait_for()
            assert not written, "SEO-ineligible story must never be approved"
            page.locator(".hold").first.click()
            page.get_by_text("Decision: hold", exact=True).first.wait_for()
            assert written[-1]["decisions"][0]["decision"] == "hold"
            page.locator(".approve").first.click()
            page.get_by_text("Decision: approved", exact=True).first.wait_for()
            assert written[-1]["decisions"][0]["decision"] == "approved"
            page.locator(".reject").first.click()
            page.get_by_text("Decision: rejected", exact=True).first.wait_for()
            assert len(written[-1]["rejected_fingerprints"]) == 1
            assert written[-1]["decisions"] == []
            page.reload(wait_until="networkidle")
            page.locator("#filter").select_option("all")
            # The ledger requires re-authentication after browser refresh,
            # so re-connect to verify persisted rejected fingerprint display.
            page.locator("#token").fill("fixture-token-only")
            page.locator("#connect").click()
            page.get_by_text("Decision: rejected", exact=True).first.wait_for()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("PASS: browser Accept/Hold/Reject, SEO denial, reload, ledger persistence")


if __name__ == "__main__":
    main()
