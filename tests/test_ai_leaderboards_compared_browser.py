"""SXF responsive leaderboard comparison: Chromium smoke and no-JS fallback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
srv=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
Thread(target=srv.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True)
  for width in (320,360,390,768,1024,1366,1440):
   p=b.new_page(viewport={"width":width,"height":860})
   errors=[];p.on("pageerror",lambda e:errors.append(str(e)))
   p.goto(f"http://127.0.0.1:{srv.server_port}/guides/ai-leaderboards-compared/",wait_until="networkidle")
   assert not errors,(width,errors)
   assert p.locator("main h1").count()==1
   assert p.locator("#lb-case option").count()==12
   assert "REJECT" in p.locator(".lb-outcome").inner_text()
   p.locator("#lb-case").select_option("10")
   assert "CONDITIONALLY VALID" in p.locator(".lb-outcome").inner_text()
   p.locator("#lb-case").select_option("05")
   assert "uncertainty" in p.locator(".lb-outcome").inner_text()
   p.locator("#lb-case").select_option("11")
   assert "CONDITIONALLY VALID" in p.locator(".lb-outcome").inner_text()
   assert p.locator('a[href="sxf-leaderboard-claim-audit.csv"]').count()>=1
   assert p.locator(".lb-table").count()>=3
   p.locator("main img").first.scroll_into_view_if_needed()
   p.wait_for_function("() => {const e=document.querySelector(\'main img\'); return e && e.complete && e.naturalWidth > 0}",timeout=10000)
   size=p.evaluate("({scroll:document.documentElement.scrollWidth,viewport:innerWidth})")
   assert size["scroll"]<=width+2,(width,size)
   print("PASS: AI leaderboard guide Chromium",width)
   p.close()
  p=b.new_page(java_script_enabled=False,viewport={"width":390,"height":850})
  p.goto(f"http://127.0.0.1:{srv.server_port}/guides/ai-leaderboards-compared/",wait_until="domcontentloaded")
  assert p.locator("main h1").is_visible()
  assert p.locator(".lb-table table").count()>=3
  assert p.locator("#lb-case-result").is_visible()
  assert p.locator('a[download]').count()>=2
  b.close()
  print("PASS: no-JavaScript reading and downloads")
finally:
 srv.shutdown();srv.server_close()
