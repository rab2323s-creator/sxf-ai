#!/usr/bin/env python3
"""Real Chromium smoke and edge-case tests for the SXF Compare V2 UI.

Requires: pip install playwright && python -m playwright install chromium
Runs entirely against a local static server, without external web traffic.
"""
from __future__ import annotations
import functools
import http.server
import pathlib
import threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/compare/"

def check(page, desc):
    page.locator("#compareBuilderResults .compare-builder-summary").wait_for(timeout=15000)
    assert page.locator("#compareBuilderError").is_hidden(), desc

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    for width, height in ((1440, 900), (375, 812)):
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        check(page, f"initial rendering at {width}")
        page.locator("#compareModelB").select_option("claude-opus-5-5")
        page.locator('[data-compare-preset="coding"]').click()
        page.locator('[data-compare-preset="coding"][aria-pressed="true"]').wait_for()
        check(page, "coding preset")
        page.locator("#compareEvidence .compare-evidence-card").first.wait_for(timeout=15000)
        summary = page.locator("#compareBuilderResults .compare-builder-summary").inner_text()
        assert "$82" in summary and "$162" in summary, (width, summary)
        assert "requests/month" in summary, summary
        assert page.locator("#compareEvidence .compare-evidence-card").count() >= 1
        assert page.locator("#compareEvidence").get_by_text("Different evaluated configurations", exact=False).count() >= 1
        page.locator("#compareMonthlyRequests").fill("2000")
        assert "$164" in page.locator("#compareBuilderResults .compare-builder-summary").inner_text()
        page.locator("#compareInputTokens").fill("-1")
        page.locator("#compareBuilderError").wait_for(state="visible")
        assert page.locator("#compareBuilderResults .compare-builder-summary").count() == 0
        page.locator("#compareInputTokens").fill("20000")
        check(page, "restored valid input")
        page.locator("#compareModelA").select_option("claude-opus-5-5")
        page.locator("#compareBuilderError").wait_for(state="visible")
        assert "different models" in page.locator("#compareBuilderError").inner_text()
        page.locator("#compareModelA").select_option("gpt-6-sol")
        check(page, "different models restored")
        page.locator("#compareInputTokens").fill("1060000")
        assert page.locator(".compare-engine-cautions").get_by_text("exceeds").count() >= 1
        assert "unavailable" in page.locator("#compareBuilderResults .compare-builder-summary").inner_text().lower()
        page.locator("#compareInputTokens").fill("2000")
        page.locator("#compareCachedTokens").fill("0")
        page.locator("#compareOutputTokens").fill("600")
        page.locator("#compareModelB").select_option("embed-v4.0")
        check(page, "missing comparable Standard pricing")
        assert "unavailable" in page.locator("#compareBuilderResults .compare-builder-summary").inner_text().lower()
        assert not errors, (width, errors)
        page.screenshot(path=str(ROOT / f"compare-{width}-test.png"), full_page=True)
        print(f"PASS: Chromium interactive compare, evidence, costs, validations at {width}px")
        page.close()
    browser.close()
server.shutdown()
print("PASS: Compare browser smoke tests complete")
