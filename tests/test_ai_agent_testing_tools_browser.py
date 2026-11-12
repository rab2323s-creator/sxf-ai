"""Responsive/mobile, interactive and no-JS smoke test for AI agent testing guide."""
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
   page=browser.new_page(viewport={"width":width,"height":850})
   errors=[];page.on("pageerror",lambda err:errors.append(str(err)))
   page.goto(f"http://127.0.0.1:{srv.server_port}/guides/ai-agent-testing-tools/",wait_until="networkidle")
   assert not errors,(width,errors)
   assert page.locator("main h1").count()==1
   assert page.locator("#tt-case option").count()==12
   assert page.locator("#tt-case-panel").inner_text().find("Phantom refund")>=0
   assert "FAIL" in page.locator(".tt-verdict").inner_text()
   page.locator("#tt-case").select_option("01")
   assert "PASS" in page.locator(".tt-verdict").inner_text()
   page.locator("#tt-case").select_option("12")
   assert "No leaked secret: fail" in page.locator("#tt-case-panel").inner_text()
   box=page.evaluate("({scroll:document.documentElement.scrollWidth,viewport:innerWidth})")
   assert box["scroll"] <= width+2,(width,box)
   assert page.locator(".tt-table-scroll").first.evaluate("(e)=>e.scrollWidth>=e.clientWidth")
   page.close()
   print("PASS: guide viewport",width)
  nojs=browser.new_page(java_script_enabled=False,viewport={"width":390,"height":850})
  nojs.goto(f"http://127.0.0.1:{srv.server_port}/guides/ai-agent-testing-tools/",wait_until="domcontentloaded")
  assert nojs.locator("main h1").count()==1
  assert nojs.locator("#tt-case-panel").is_visible()
  assert nojs.locator('a[href="fixtures.csv"]').count()>=1
  browser.close()
  print("PASS: no-JavaScript reading and download available")
finally:
 srv.shutdown();srv.server_close()
