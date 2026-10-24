#!/usr/bin/env python3
"""Desktop/mobile Chromium tests for the local-model selector and static fallback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(ROOT)),
    )
    Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/tools/local-llm-vram-finder/"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width, height in ((360, 780), (390, 844), (768, 1024), (1440, 900)):
                page = browser.new_page(viewport={"width": width, "height": height})
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                response = page.goto(url, wait_until="domcontentloaded")
                assert response and response.status == 200
                page.locator(".vram-result").first.wait_for(timeout=15000)
                assert page.locator("h1").count() == 1
                assert page.locator(".vram-table tbody tr").count() == 13
                assert page.locator("#vram-count").inner_text().startswith("2 planning candidates")

                page.locator("#vram-search").fill("")
                page.locator("#vram-capacity").select_option("8")
                assert page.locator("#vram-count").inner_text().startswith("1 planning candidate")
                assert "qwen2.5-coder:7b" in page.locator("#vram-results").inner_text()

                page.locator("#vram-capacity").select_option("24")
                page.locator("#vram-workload").select_option("vision")
                page.locator("#vram-context").select_option("4096")
                assert page.locator("#vram-result").count() == 0  # not a valid element
                assert page.locator(".vram-result").count() >= 2
                assert "Gemma" in page.locator("#vram-results").inner_text()

                page.locator("#vram-capacity").select_option("8")
                page.locator("#vram-context").select_option("32768")
                assert page.locator(".vram-result").count() == 0
                assert "No catalog matches" in page.locator("#vram-results").inner_text()

                page.locator("#vram-mode").select_option("model")
                page.locator("#vram-search").fill("qwen")
                assert "model variant" in page.locator("#vram-count").inner_text()
                assert "Nearest listed GPU size" in page.locator("#vram-results").inner_text()
                page.locator("#vram-search").fill("model-that-does-not-exist")
                assert "No catalog matches" in page.locator("#vram-results").inner_text()

                # Input changes should not trigger JS errors or viewport-wide scrolling.
                assert not errors, (width, errors)
                extent = page.evaluate("({ width: innerWidth, document: document.documentElement.scrollWidth })")
                assert extent["document"] <= width + 2, (width, extent)
                page.screenshot(path=str(ROOT / f"local-vram-{width}-test.png"), full_page=True)
                print(f"PASS: local LLM selector mobile/desktop {width}px", flush=True)
                page.close()

            without_js = browser.new_page(java_script_enabled=False)
            response = without_js.goto(url, wait_until="domcontentloaded")
            assert response and response.status == 200
            assert without_js.locator(".vram-table tbody tr").count() == 13
            assert without_js.locator("#quick-picks .vram-pick").count() == 5
            assert without_js.locator("h1").count() == 1
            print("PASS: local LLM guide has indexable static fallback without JavaScript")
            without_js.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    run()
