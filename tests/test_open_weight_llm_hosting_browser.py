#!/usr/bin/env python3
"""Real Chromium mobile/desktop calculator, FAQ, overflow and JS-off QA."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
route="/guides/open-weight-llm-hosting/"
def main():
 server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(root)))
 Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True,args=["--no-sandbox"])
   try:
    for width,height in ((320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1024,768),(1440,900)):
     p=b.new_page(viewport={"width":width,"height":height})
     errors=[];p.on("pageerror",lambda err:errors.append(str(err)))
     p.goto("http://127.0.0.1:"+str(server.server_port)+route,wait_until="networkidle",timeout=30000)
     assert p.locator("main h1").count()==1
     assert p.locator(".host-faq").count()==9
     m=p.evaluate("""() => ({width:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,boxes:[...document.querySelectorAll('.guide-article-hero,.guide-answer,.guide-reading,.host-lab,.host-facts,.host-output,.host-cards,.host-related')].map(e=>{const r=e.getBoundingClientRect();return [r.left,r.right]})})""")
     assert m["width"]<=width+2,(width,"page overflow",m)
     assert all(l>=-3 and r<=width+3 for l,r in m["boxes"]),(width,"panel overflow",m)
     assert "$30.00" in p.locator("#host-result-token").inner_text()
     assert "$743.82" in p.locator("#host-result-gpu").inner_text()
     p.locator("#host-requests").fill("200000")
     assert "$60.00" in p.locator("#host-result-token").inner_text()
     p.locator("#host-hours").fill("1")
     assert "$6.20" in p.locator("#host-result-gpu").inner_text()
     p.locator(".host-faq summary").first.click()
     assert p.locator(".host-faq").first.evaluate("(e)=>e.open")
     assert not errors,(width,errors)
     print("PASS hosting Chromium",width,flush=True);p.close()
    plain=b.new_page(viewport={"width":390,"height":844},java_script_enabled=False)
    plain.goto("http://127.0.0.1:"+str(server.server_port)+route,wait_until="domcontentloaded")
    assert "$30.00" in plain.locator("#host-result-token").inner_text()
    plain.close()
    print("PASS hosting no-JS default",flush=True)
   finally:b.close()
 finally:server.shutdown();server.server_close()
if __name__=="__main__":main()
