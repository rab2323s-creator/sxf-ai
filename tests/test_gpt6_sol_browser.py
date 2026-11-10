#!/usr/bin/env python3
"""Real Chromium desktop/mobile coverage for the original GPT-6 Sol research page."""
from __future__ import annotations
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from gpt6_sol_model_page import enrich_gpt6_sol_page

catalog=json.loads((ROOT/"data/model-pricing.json").read_text(encoding="utf-8"))
by_id={item["model_id"]:item for item in catalog["models"]}
source=(ROOT/"models/gpt-6-sol/index.html").read_text(encoding="utf-8")
html=source if 'id="sxf-sol-dossier"' in source else enrich_gpt6_sol_page(source,by_id)

class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0].rstrip("/") == "/models/gpt-6-sol":
            data=html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(PreviewHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
            try:
                for width,height in [(320,720),(360,780),(375,812),(390,844),(430,932),(768,1024),(1024,768),(1440,900)]:
                    page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
                    errors=[]
                    page.on("pageerror",lambda error: errors.append(str(error)))
                    page.goto("http://127.0.0.1:"+str(server.server_port)+"/models/gpt-6-sol/",wait_until="networkidle")
                    assert page.locator("body.sol-research-page").count()==1
                    assert page.locator("#sxf-sol-dossier").count()==1
                    assert page.locator(".sol-table-wrap").count()>=3
                    metrics=page.evaluate("""() => {
                        const viewport=document.documentElement.clientWidth;
                        const rect=e=>{const b=e.getBoundingClientRect();return {left:b.left,right:b.right,width:b.width,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth};};
                        return {viewport,doc:document.documentElement.scrollWidth,
                           panels:[...document.querySelectorAll('.sol-dossier,.sol-panel,.sol-lead,.sol-lead-copy,.sol-identity,.sol-table-wrap,.sol-code,.sol-calculator,.sol-finding')].map(rect),
                           scrollables:[...document.querySelectorAll('.sol-table-wrap,.sol-code')].map(rect)};
                    }""")
                    assert metrics["doc"]<=width+2, f"Horizontal document overflow at {width}px: {metrics}"
                    assert all(e["left"]>=-2 and e["right"]<=width+2 for e in metrics["panels"]),f"Panel overflow at {width}px: {metrics}"
                    assert all(e["scrollWidth"]>=e["clientWidth"] for e in metrics["scrollables"])
                    assert page.locator("#sol-cost-calculator [name='new']").is_visible()
                    page.locator("#sol-cost-calculator [name='new']").fill("272001")
                    page.locator("#sol-cost-calculator [name='cached']").fill("0")
                    page.locator("#sol-cost-calculator [name='output']").fill("4000")
                    assert "$1.148004" in page.locator('[data-result="sol"]').inner_text(),(width,page.locator('[data-result="sol"]').inner_text())
                    page.locator("#sol-cost-calculator [name='new']").fill("12000")
                    page.locator("#sol-cost-calculator [name='cached']").fill("200000")
                    assert "$20.00" in page.locator('[data-result="difference"]').inner_text(),width
                    page.locator("#sol-faq summary").first.click()
                    assert page.locator("#sol-faq details").first.evaluate("(e)=>e.open")
                    assert not errors,(width,errors)
                    print(f"PASS Sol Chromium {width}px: no page drift; research panels contained; calculator and FAQ functional",flush=True)
                    page.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    main()
