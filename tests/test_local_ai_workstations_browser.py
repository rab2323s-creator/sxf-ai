"""Chromium UI: 320..1440px, form interactions, links, no JS, and script errors."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
srv=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
Thread(target=srv.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  for width in (320,360,390,768,1024,1366,1440):
   page=browser.new_page(viewport={"width":width,"height":860})
   errors=[];page.on("pageerror",lambda er:errors.append(str(er)))
   page.goto(f"http://127.0.0.1:{srv.server_port}/guides/local-ai-workstations/",wait_until="networkidle")
   assert not errors,(width,errors)
   assert page.locator("main h1").count()==1
   assert page.locator("#lw-model option").count()==5
   assert page.locator("#lw-system option").count()==4
   page.locator("#lw-system").select_option("ultra")
   page.locator("#lw-model").select_option("qwen235")
   assert "Fits the illustrative memory screen" in page.locator("#lw-verdict").inner_text()
   page.locator("#lw-system").select_option("spark")
   assert "Over illustrative memory budget" in page.locator("#lw-verdict").inner_text()
   page.locator("#lw-model").select_option("qwen9")
   assert "Fits the illustrative memory screen" in page.locator("#lw-verdict").inner_text()
   page.locator("#lw-model").select_option("qwen122")
   page.locator("#lw-quant").select_option("8.5")
   assert "Over illustrative memory budget" in page.locator("#lw-verdict").inner_text()
   page.locator("#lw-quant").select_option("4.5")
   page.locator("#lw-reserve").select_option("24")
   assert page.locator("#lw-demand").inner_text().endswith("GB")
   assert page.locator('a[href="sxf-workstation-memory-screen.csv"]').count()>0
   assert page.locator(".lw-table").count()>=3
   overflow=page.evaluate("({scroll:document.documentElement.scrollWidth,viewport:innerWidth})")
   assert overflow["scroll"]<=width+2,(width,overflow)
   for img in page.locator("main img").all():assert img.evaluate("(e)=>e.complete && e.naturalWidth>0")
   print("PASS viewport",width)
   page.close()
  page=browser.new_page(java_script_enabled=False,viewport={"width":390,"height":844})
  page.goto(f"http://127.0.0.1:{srv.server_port}/guides/local-ai-workstations/",wait_until="domcontentloaded")
  assert page.locator("main h1").is_visible()
  assert page.locator(".lw-table table").count()>=3
  assert page.locator('a[download]').count()>=3
  browser.close()
  print("PASS no JS article and downloadable evidence")
finally:
 srv.shutdown();srv.server_close()
