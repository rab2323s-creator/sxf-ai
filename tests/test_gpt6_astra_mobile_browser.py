"""Chromium mobile overflow regression for the GPT-6 Astra research page."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            try:
                for width,height in ((320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1280,900)):
                    page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
                    errors=[]
                    page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(f"http://127.0.0.1:{server.server_port}/models/gpt-6-astra/",wait_until="networkidle",timeout=30000)
                    assert page.locator("body.astra-research-page").count()==1, f"Missing responsive scope at {width}"
                    assert page.locator("#sxf-astra-study").count()==1
                    assert page.locator(".astra-scroll").count()==3
                    page.locator(".astra-calculator [data-tokens='input']").fill("272001")
                    page.locator(".astra-calculator [data-tokens='cached']").fill("0")
                    page.locator(".astra-calculator [data-tokens='output']").fill("4000")
                    assert "$5.74002" in page.locator("[data-result='astra']").inner_text()
                    assert not errors, f"JavaScript error at {width}: {errors}"
                    metrics=page.evaluate("""() => {
                        const vp=document.documentElement.clientWidth;
                        const main=document.querySelector('main').getBoundingClientRect();
                        const shells=[...document.querySelectorAll('main > .shell, #sxf-astra-study, .astra-panel, .astra-study-head')];
                        const containers=[...document.querySelectorAll('.astra-scroll, .astra-code')];
                        const rect=e=>{const r=e.getBoundingClientRect();return {tag:e.tagName,className:e.className,left:r.left,right:r.right,width:r.width,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth}};
                        return {vp,doc:document.documentElement.scrollWidth,main:rect(document.querySelector('main')),
                            cards:shells.map(rect),scrollables:containers.map(rect)};
                    }""")
                    assert metrics["doc"]<=width+2, f"Document horizontal overflow at {width}: {metrics}"
                    assert all(c["left"]>=-2 and c["right"]<=width+2 for c in metrics["cards"]), f"Main research content exceeds viewport {width}: {metrics}"
                    assert all(c["left"]>=-2 and c["right"]<=width+2 for c in metrics["scrollables"]), f"Scrollable pane extends beyond viewport {width}: {metrics}"
                    assert all(c["scrollWidth"]>=c["clientWidth"] for c in metrics["scrollables"])
                    page.locator(".astra-faq summary").first.click()
                    assert page.locator(".astra-faq details").first.evaluate("(el)=>el.open"),f"FAQ not usable {width}"
                    print(f"PASS Astra mobile at {width}px: no document overflow; tables contained, calculator and FAQ functional")
                    page.close()
            finally:browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    main()
