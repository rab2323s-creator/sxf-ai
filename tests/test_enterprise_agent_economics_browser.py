#!/usr/bin/env python3
"""Real Chromium desktop/mobile tests for SXF enterprise agent economics.
Requires python -m pip install playwright and python -m playwright install chromium.
Uses a local static server; no public or paid network access.
"""
from __future__ import annotations

import functools
import http.server
import pathlib
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f"http://127.0.0.1:{server.server_port}/guides/ai-agent-cost/"

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    for width,height in ((1440,900),(390,844),(320,740)):
        page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.goto(url,wait_until="domcontentloaded",timeout=30000)
        page.locator('#studyStatus[data-state="ready"]').wait_for(timeout=20000)
        assert page.title().startswith("AI Agent Cost in 2026:"),page.title()
        assert page.locator("h1").count()==1
        assert page.locator("main section").count()>=12
        assert page.locator('#studyYear').inner_text()=="$122,414"
        assert page.locator('#studyROI').inner_text()=="82.9%"
        assert page.locator('#studyUnit').inner_text()=="$1.24"
        if page.evaluate("document.documentElement.scrollWidth>window.innerWidth"):
            offenders=page.evaluate("""() => [...document.querySelectorAll('body *')].map(el=>({tag:el.tagName,cls:typeof el.className==='string'?el.className:'',id:el.id,left:Math.round(el.getBoundingClientRect().left),right:Math.round(el.getBoundingClientRect().right)})).filter(o=>o.right>innerWidth+1 || o.left < -1).slice(0,35)""")
            print("DIAGNOSTIC OVERFLOW",width,"document",page.evaluate("document.documentElement.scrollWidth"),"offenders",offenders,flush=True)
            page.screenshot(path=str(ROOT/f"econ-study-{width}-overflow.png"),full_page=True)
        assert not page.evaluate("document.documentElement.scrollWidth>window.innerWidth"),"Horizontal overflow: "+str(width)
        page.locator('#studyCase').select_option('documents')
        assert page.locator('#studyROI').inner_text()=="-2.8%"
        assert page.locator('#studyYear').inner_text()=="$164,281"
        page.locator('#studyCase').select_option('research')
        assert page.locator('#studyROI').inner_text()=="-37.8%"
        page.locator('#studyYear').inner_text()=="$240,640"
        page.locator('#studySuccess').fill("0")
        assert page.locator('#studyUnit').inner_text()=="N/A"
        assert page.locator('#studyCaptured').inner_text()=="$0"
        page.locator('#studyCase').select_option('support')
        page.locator('#studySuccess').fill("100")
        assert page.locator('#studyAccepted').inner_text()=="10,000"
        assert page.locator('link[rel="canonical"]').get_attribute("href")=="https://sxf.si/guides/ai-agent-cost/"
        assert not errors,(width,errors)
        page.screenshot(path=str(ROOT/f"econ-study-{width}-test.png"),full_page=True)
        print(f"PASS: real Chromium finance, layout, metadata, sensitivity at {width}px")
        page.close()
    browser.close()
server.shutdown()
print("PASS: Enterprise economics browser QA complete")
