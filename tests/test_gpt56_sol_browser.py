#!/usr/bin/env python3
"""GPT-5.6 Sol eight-size real Chromium responsiveness and lab calculator smoke."""
from __future__ import annotations
import json,sys
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from gpt56_sol_model_page import enrich_gpt56_sol_page
models={m["model_id"]:m for m in json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))["models"]}
source=(ROOT/"models/gpt-5-6-sol/index.html").read_text(encoding="utf-8")
html=source if 'id="sxf-gpt56-sol-research"' in source else enrich_gpt56_sol_page(source,models)
class PreviewHandler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split("?")[0].rstrip("/")=="/models/gpt-5-6-sol":
   data=html.encode("utf-8")
   self.send_response(200)
   self.send_header("Content-Type","text/html; charset=utf-8")
   self.send_header("Content-Length",str(len(data)))
   self.end_headers()
   self.wfile.write(data)
   return
  super().do_GET()
def main():
 server=ThreadingHTTPServer(("127.0.0.1",0),partial(PreviewHandler,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
   try:
    for width,height in ((320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1024,768),(1440,900)):
     page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
     errors=[]
     page.on("pageerror",lambda error:errors.append(str(error)))
     page.goto("http://127.0.0.1:"+str(server.server_port)+"/models/gpt-5-6-sol/",wait_until="networkidle",timeout=30000)
     assert page.locator("body.g56-page").count()==1
     assert page.locator("#sxf-gpt56-sol-research").count()==1
     assert page.locator(".g56-scroll").count()>=3
     metrics=page.evaluate("""() => {
      const vp=document.documentElement.clientWidth;
      const rect=e=>{const b=e.getBoundingClientRect();return {left:b.left,right:b.right,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth};};
      return {vp,doc:document.documentElement.scrollWidth,
       blocks:[...document.querySelectorAll('.g56-dossier,.g56-feature,.g56-panel,.g56-glance,.g56-feature-copy,.g56-scroll,.g56-code,.g56-form,.g56-cards article,.g56-findings article')].map(rect)};
     }""")
     assert metrics["doc"]<=width+2,f"Document has horizontal drift at {width}: {metrics}"
     assert all(b["left"]>=-2 and b["right"]<=width+2 for b in metrics["blocks"]),f"Research overflow at {width}: {metrics}"
     assert not errors,(width,errors)
     assert "$4.880000" in page.locator('[data-result="uncached"]').inner_text()
     assert "$1.740000" in page.locator('[data-result="thirty"]').inner_text()
     page.locator('#g56-cache-calculator [name="prefix"]').fill("272001")
     page.locator('#g56-cache-calculator [name="new"]').fill("0")
     page.locator('#g56-cache-calculator [name="calls"]').fill("1")
     assert "Long >272K" in page.locator('[data-result="tier"]').inner_text()
     page.locator(".g56-faq summary").first.click()
     assert page.locator(".g56-faq details").first.evaluate("(node)=>node.open")
     print("PASS GPT-5.6 Sol Chromium",width,"px: no document overflow; lab calculator and FAQ functional",flush=True)
     page.close()
   finally:browser.close()
 finally:
  server.shutdown()
  server.server_close()
if __name__=="__main__":main()
