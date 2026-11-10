#!/usr/bin/env python3
"""Real Chromium 320px–1440px Claude Sonnet 5 research and calculator QA."""
from __future__ import annotations
import json,sys
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from claude_sonnet5_model_page import enrich_claude_sonnet5_page
models={m["model_id"]:m for m in json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))["models"]}
source=(ROOT/"models/claude-sonnet-5/index.html").read_text(encoding="utf-8")
html=source if 'id="sxf-sonnet5-research"' in source else enrich_claude_sonnet5_page(source,models)
class Preview(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split("?")[0].rstrip("/")=="/models/claude-sonnet-5":
   data=html.encode("utf-8")
   self.send_response(200)
   self.send_header("Content-Type","text/html; charset=utf-8")
   self.send_header("Content-Length",str(len(data)))
   self.end_headers()
   self.wfile.write(data)
   return
  return super().do_GET()
def main():
 server=ThreadingHTTPServer(("127.0.0.1",0),partial(Preview,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
   try:
    for width,height in [(320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1024,768),(1440,900)]:
     page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
     errors=[]
     page.on("pageerror",lambda error: errors.append(str(error)))
     page.goto("http://127.0.0.1:"+str(server.server_port)+"/models/claude-sonnet-5/",wait_until="networkidle")
     assert page.locator("body.cs5-page").count()==1
     assert page.locator("h1").inner_text().strip().startswith("Claude Sonnet 5")
     assert "API Pricing" in page.locator("h1").inner_text()
     assert page.locator(".model-reference-deep").count()==0
     assert page.locator("#sxf-sonnet5-research").count()==1
     assert page.locator(".cs5-scroll").count()>=3
     metrics=page.evaluate("""() => {const rect=e=>{const b=e.getBoundingClientRect();return {left:b.left,right:b.right,sw:e.scrollWidth,cw:e.clientWidth}};return {width:document.documentElement.scrollWidth,blocks:[...document.querySelectorAll('.cs5-dossier,.cs5-hero,.cs5-intro,.cs5-specs,.cs5-panel,.cs5-scroll,.cs5-code,.cs5-tool,.cs5-cards article,.cs5-findings article')].map(rect),offenders:[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,cls:typeof e.className==='string'?e.className.slice(0,85):'',...rect(e)})).filter(e=>e.right>innerWidth+2||e.left< -2).slice(0,14)};}""")
     assert metrics["width"]<=width+2,f"Document horizontal overflow {width}px {metrics}"
     assert all(b["left"]>=-2 and b["right"]<=width+2 for b in metrics["blocks"]),f"Research component overflow {width}px {metrics}"
     assert not errors,(width,errors)
     assert "$2.44" in page.locator('[data-cost="five-uncached"]').inner_text()
     assert "$0.87" in page.locator('[data-cost="five-cached"]').inner_text()
     assert "$0.78" in page.locator('[data-cost="next-cached"]').inner_text()
     page.locator('#cs5-price-tool [name="ttl"]').select_option("hour")
     assert "$1.02" in page.locator('[data-cost="five-cached"]').inner_text()
     page.locator('#cs5-price-tool [name="calls"]').fill("1")
     assert page.locator('[data-cost="saving"]').inner_text().startswith("$-")
     page.locator(".cs5-faq summary").first.click()
     assert page.locator(".cs5-faq details").first.evaluate("(e)=>e.open")
     print("PASS Claude Sonnet 5 Chromium",width,"px: no drift, calculator and FAQ working")
     page.close()
   finally:browser.close()
 finally:
  server.shutdown()
  server.server_close()
if __name__=="__main__":main()
