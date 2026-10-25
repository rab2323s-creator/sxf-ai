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
                assert "model famil" in page.locator("#vram-count").inner_text()
                assert page.locator("#vram-capacity").is_visible()
                assert page.locator("#vram-capacity-field").is_visible()
                assert not page.locator("#vram-finder").evaluate("(el) => el.classList.contains('vram-reverse-mode')")
                assert page.locator(".vram-decision").count() >= 1
                assert 1 <= page.locator(".vram-result").count() <= 8
                if page.locator("#vram-show-more").is_visible():
                    page.locator("#vram-show-more").click()
                    assert page.locator(".vram-result").count() > 8

                page.locator("#vram-search").fill("")
                page.locator("#vram-capacity").select_option("8")
                assert "model famil" in page.locator("#vram-count").inner_text()
                assert page.locator(".vram-result").count() >= 1

                page.locator("#vram-capacity").select_option("24")
                page.locator("#vram-workload").select_option("vision")
                page.locator("#vram-context").select_option("4096")
                assert page.locator("#vram-result").count() == 0  # not a valid element
                assert page.locator(".vram-result").count() >= 2
                assert page.locator("#vram-reviewed-evidence").is_hidden()
                page.locator("#vram-search").fill("qwen3-vl")
                page.locator("#vram-reviewed-evidence").wait_for(state="visible", timeout=10000)
                case_text = page.locator("#vram-reviewed-evidence").inner_text()
                assert "64.23" in case_text and "qwen3-vl:4b-instruct" in case_text
                assert "not model-only VRAM" in case_text
                page.locator("#vram-context").select_option("8192")
                assert "Different context selected" in page.locator("#vram-reviewed-evidence").inner_text()
                page.locator("#vram-search").fill("qwen3-vl:4b")
                assert page.locator("#vram-reviewed-evidence").is_hidden()
                page.locator("#vram-search").fill("qwen3-vl:8b")
                assert page.locator("#vram-reviewed-evidence").is_hidden()
                page.locator("#vram-search").fill("gemma")
                assert "Gemma" in page.locator("#vram-results").inner_text()

                page.locator("#vram-capacity").select_option("8")
                page.locator("#vram-context").select_option("32768")
                page.locator("#vram-search").fill("model-that-does-not-exist")
                assert page.locator(".vram-result").count() == 0
                assert "No matching models" in page.locator("#vram-results").inner_text()

                page.locator("#vram-mode").select_option("model")
                assert page.locator("#vram-capacity-field").is_hidden()
                assert page.locator("#vram-capacity").is_hidden()
                assert page.locator("#vram-search").is_visible()
                assert page.locator("#vram-finder").evaluate("(el) => el.classList.contains('vram-reverse-mode')")
                assert page.locator("#vram-context").is_visible()
                assert page.locator("#vram-workload").is_visible()
                assert page.locator("#vram-capacity").input_value() == "8"  # hidden value is preserved
                cols = page.locator("#vram-finder").evaluate("(el) => getComputedStyle(el).gridTemplateColumns.split(' ').length")
                assert cols == (1 if width <= 650 else 2), (width, cols)
                page.locator("#vram-workload").select_option("chat")
                page.locator("#vram-search").fill("qwen")
                assert "model famil" in page.locator("#vram-count").inner_text()
                assert "Nearest listed GPU tier" in page.locator("#vram-results").inner_text()
                page.locator("#vram-search").fill("model-that-does-not-exist")
                assert "No matching models" in page.locator("#vram-results").inner_text()

                assert page.locator(".vram-variants").count() >= 0
                page.locator("#vram-mode").select_option("gpu")
                assert page.locator("#vram-capacity").is_visible()
                assert page.locator("#vram-capacity-field").is_visible()
                assert page.locator("#vram-capacity").input_value() == "8"
                assert not page.locator("#vram-finder").evaluate("(el) => el.classList.contains('vram-reverse-mode')")
                cols = page.locator("#vram-finder").evaluate("(el) => getComputedStyle(el).gridTemplateColumns.split(' ').length")
                assert cols == (1 if width <= 650 else 3), (width, cols)
                page.locator("#vram-workload").select_option("coding")
                page.locator("#vram-context").select_option("8192")
                page.locator("#vram-capacity").select_option("16")
                page.locator("#vram-search").fill("")
                assert "conditional: aggressive quantization" in page.locator("#vram-results").inner_text().lower()
                assert "Why shown:" in page.locator("#vram-results").inner_text()
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
            assert without_js.locator("#vram-capacity").is_visible()
            assert without_js.locator("#vram-workload").is_visible()
            assert without_js.locator("#vram-context").is_visible()
            assert without_js.locator("h1").count() == 1
            print("PASS: local LLM guide has indexable static fallback without JavaScript")
            without_js.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    run()
