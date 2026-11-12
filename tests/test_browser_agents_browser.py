#!/usr/bin/env python3
"""Real responsive Chromium checks, no-JS fallback, FAQ and scenario calculator."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
ROUTE="/guides/ai-browser-agents-comparison/"
def main():
 server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
   try:
    for width,height in ((320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1024,768),(1440,900)):
     page=browser.new_page(viewport={"width":width,"height":height})
     errors=[];page.on("pageerror",lambda err:errors.append(str(err)))
     page.goto("http://127.0.0.1:"+str(server.server_port)+ROUTE,wait_until="networkidle",timeout=30000)
     assert page.locator("main h1").count()==1
     assert page.locator(".ba-faq").count()==11
     assert page.locator(".ba-table-wrap").count()>=4
     m=page.evaluate("""() => ({doc:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,
     blocks:[...document.querySelectorAll('.guide-article-hero,.guide-answer,.guide-reading,.ba-lab,.ba-summary,.ba-results,.ba-flow,.ba-resources,.ba-cards,.ba-related')].map(e=>{let r=e.getBoundingClientRect();return [r.left,r.right]})})""")
     assert m["doc"]<=width+2,(width,"horizontal drift",m)
     assert all(l>=-3 and r<=width+3 for l,r in m["blocks"]),(width,"layout overflow",m)
     assert "$402.50" in page.locator("#ba-out-total").inner_text()
     assert "$0.50" in page.locator("#ba-out-success-cost").inner_text()
     page.locator("#ba-tasks").fill("2000")
     assert "$785.00" in page.locator("#ba-out-total").inner_text()
     page.locator("#ba-success").fill("0")
     assert "No completed tasks" in page.locator("#ba-out-success-cost").inner_text()
     page.locator(".ba-faq summary").first.click()
     assert page.locator(".ba-faq").first.evaluate("(e)=>e.open")
     assert not errors,(width,errors)
     print("PASS SXF browser guide Chromium",width,"px",flush=True);page.close()
    plain=browser.new_page(viewport={"width":390,"height":844},java_script_enabled=False)
    plain.goto("http://127.0.0.1:"+str(server.server_port)+ROUTE,wait_until="domcontentloaded")
    assert "$402.50" in plain.locator("#ba-out-total").inner_text()
    assert plain.locator("main h1").count()==1
    print("PASS SXF browser guide no-JS fallback",flush=True)
    plain.close()
   finally:browser.close()
 finally:server.shutdown();server.server_close()
if __name__=="__main__":main()
