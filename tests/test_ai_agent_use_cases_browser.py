"""Desktop/mobile and no-JavaScript smoke tests for the SXF Agent Opportunity Atlas."""
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
    url = f"http://127.0.0.1:{server.server_port}/guides/ai-agent-use-cases/"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for width in (360, 390, 768, 1440):
                page = browser.new_page(viewport={"width": width, "height": 850})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(url, wait_until="networkidle")
                assert not errors, errors
                assert page.locator(".oa-case").count() == 50
                assert page.locator(".oa-case:visible").count() == 50
                assert "50 of 50" in page.locator("#oa-count").inner_text()
                assert page.locator("#oa-current").inner_text().startswith("$")
                assert page.locator("#oa-savings").inner_text().startswith("-$")
                page.locator("#oa-search").fill("does-not-exist-123")
                assert page.locator(".oa-case:visible").count() == 0
                assert page.locator("#oa-empty").is_visible()
                page.locator("#oa-reset").click()
                assert page.locator(".oa-case:visible").count() == 50
                page.locator("#oa-accept").fill("101")
                assert page.locator("#oa-validation").is_visible()
                assert page.locator("#oa-savings").inner_text() == "—"
                page.locator("#oa-accept").fill("70")
                assert not page.locator("#oa-validation").is_visible()
                page.locator("#oa-risk").select_option("high")
                assert 0 < page.locator(".oa-case:visible").count() < 50
                page.locator("#oa-clear").click()
                page.locator(".oa-evaluate").first.click()
                assert "Enter your own company data" in page.locator("#oa-selected").inner_text()
                widths = page.evaluate("({scroll: document.documentElement.scrollWidth, view: innerWidth})")
                assert widths["scroll"] <= width + 2, (width, widths)
                print("PASS: Atlas responsive viewport", width)
                page.close()
            no_js = browser.new_page(java_script_enabled=False)
            no_js.goto(url, wait_until="domcontentloaded")
            assert no_js.locator(".oa-case").count() == 50
            assert no_js.locator(".oa-case:visible").count() == 50
            browser.close()
            print("PASS: Atlas works without JavaScript")
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    run()
