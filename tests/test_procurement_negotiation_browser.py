#!/usr/bin/env python3
"""Real Chromium responsive and calculator smoke test for the SXF procurement guide."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
ROUTE='/guides/ai-procurement-negotiation-software/'
def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
            try:
                for width,height in ((320,720),(360,780),(390,844),(430,932),(768,1024),(1024,768),(1440,900)):
                    page=browser.new_page(viewport={'width':width,'height':height})
                    errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto(f'http://127.0.0.1:{server.server_port}'+ROUTE,wait_until='networkidle',timeout=30000)
                    assert page.locator('main h1').count()==1
                    assert page.locator('.proc-faq').count()==8
                    m=page.evaluate("""() => ({width:document.documentElement.scrollWidth,vp:document.documentElement.clientWidth,panels:[...document.querySelectorAll('.guide-article-hero,.guide-answer,.guide-reading,.proc-lab,.proc-grid,.proc-flow')].map(e=>{const r=e.getBoundingClientRect();return [r.left,r.right]})})""")
                    assert m['width']<=width+2,(width,'document horizontal overflow',m)
                    assert all(a>=-3 and b<=width+3 for a,b in m['panels']),(width,'panel overflow',m)
                    assert '1,849' in page.locator('#proc-out-net').inner_text()
                    page.locator('#proc-spend').fill('10000000')
                    assert '$91,301' in page.locator('#proc-out-net').inner_text(),(width,page.locator('#proc-out-net').inner_text())
                    page.locator('#proc-price').fill('-5')
                    assert page.locator('#proc-net-card').evaluate('(e)=>e.classList.contains("negative")')
                    page.locator('.proc-faq summary').first.click()
                    assert page.locator('.proc-faq').first.evaluate('(e)=>e.open')
                    assert not errors,(width,errors)
                    print('PASS procurement Chromium',width,flush=True)
                    page.close()
                nojs=browser.new_page(viewport={'width':390,'height':844},java_script_enabled=False)
                nojs.goto(f'http://127.0.0.1:{server.server_port}'+ROUTE,wait_until='domcontentloaded')
                assert '1,849' in nojs.locator('#proc-out-net').inner_text()
                assert nojs.locator('main h1').count()==1
                nojs.close()
                print('PASS procurement no-JavaScript fallback',flush=True)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
if __name__=='__main__':
    main()
