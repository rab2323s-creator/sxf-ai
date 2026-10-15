"""Desktop, tablet and mobile layout smoke tests for the Research hub."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Serve over HTTP so root-absolute image URLs behave like production.
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        test_viewports(server)
    finally:
        server.shutdown()
        server.server_close()


def test_viewports(server):
    url = f"http://127.0.0.1:{server.server_port}/research/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width, height, name in [(360, 780, "mobile-360"), (390, 844, "mobile-390"), (768, 1024, "tablet"), (1440, 900, "desktop")]:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(url, wait_until="domcontentloaded")
            page.locator("#research-heading").wait_for()
            assert page.locator("h1").count() == 1
            assert page.locator(".research-featured-card").count() == 3
            page.wait_for_function("() => [...document.querySelectorAll('.research-featured-image img')].length === 3 && [...document.querySelectorAll('.research-featured-image img')].every(img => img.complete)", timeout=15000)
            image_status = page.locator(".research-featured-image img").evaluate_all(
                "(imgs) => imgs.map(img => ({src: img.currentSrc, naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight}))"
            )
            assert all(img["naturalWidth"] > 0 and img["naturalHeight"] > 0 for img in image_status), (
                f"Broken featured research images at {name}: {image_status}"
            )
            assert page.locator(".research-jump-links a").count() == 4
            assert page.locator(".research-faq-item").count() == 3
            metrics = page.evaluate("""() => {
              const main=document.querySelector('#research-main');
              const rect=main.getBoundingClientRect();
              const cards=[...document.querySelectorAll('.research-featured-card')].map(el=>el.getBoundingClientRect());
              const hero=document.querySelector('.research-hero').getBoundingClientRect();
              const jump=document.querySelector('.research-jump').getBoundingClientRect();
              return {scrollWidth:document.documentElement.scrollWidth,viewport:window.innerWidth,
                mainWidth:rect.width, cards:cards.map(x=>({width:x.width,left:x.left,right:x.right})),
                heroHeight:hero.height, jumpHeight:jump.height};
            }""")
            assert metrics["scrollWidth"] <= width + 2, f"Horizontal document overflow at {name}: {metrics}"
            assert all(c["width"] >= 220 and c["left"] >= -2 and c["right"] <= width+2 for c in metrics["cards"]), f"Clipped research cards at {name}: {metrics}"
            assert metrics["jumpHeight"] >= 48, f"Navigation links too small at {name}: {metrics}"
            assert metrics["heroHeight"] < (650 if width <= 390 else 830), f"Overly tall hero at {name}: {metrics}"
            page.locator(".research-faq-item").first.locator("summary").click()
            assert page.locator(".research-faq-item").first.evaluate("(el)=>el.open")
            page.locator(".research-jump-links a[href='#signals']").click()
            assert page.evaluate("location.hash") == "#signals"
            page.screenshot(path=str(ROOT / ("research-" + name + "-test.png")), full_page=True)
            print(f"PASS: {name} viewport={width} no horizontal overflow, clear cards/navigation, compact hero, working details and anchors")
            page.close()
        browser.close()

if __name__ == "__main__":
    main()
