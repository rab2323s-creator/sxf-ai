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
    for width,height in ((1440,900),(1024,768),(768,1024),(430,932),(390,844),(375,812),(320,740)):
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
        # Uploaded diagrams retain their natural aspect ratio and never exceed their article column.
        image_paths = {
            "cost-image-hero": "/guides/ai-agent-cost/images/ai-agent-cost-breakdown.webp",
            "cost-image-flow": "/guides/ai-agent-cost/images/ai-agent-roi-workflow.webp",
        }
        for figure_id, expected_src in image_paths.items():
            figure = page.locator(f"#{figure_id}")
            image = figure.locator("img")
            link = figure.locator(".econ-figure-zoom")
            image.scroll_into_view_if_needed()
            image.evaluate("(image) => image.decode()")
            assert image.get_attribute("src") == expected_src
            assert image.get_attribute("width") == "1672"
            assert image.get_attribute("height") == "941"
            assert link.get_attribute("href") == expected_src
            assert link.get_attribute("target") == "_blank"
            assert link.get_attribute("rel") == "noopener noreferrer"
            geometry = image.evaluate("""(image) => {
                const r = image.getBoundingClientRect();
                const column = document.querySelector('.econ-content').getBoundingClientRect();
                return {left:r.left,right:r.right,width:r.width,height:r.height,
                        columnLeft:column.left,columnRight:column.right,
                        naturalWidth:image.naturalWidth,naturalHeight:image.naturalHeight}
            }""")
            assert geometry["naturalWidth"] == 1672, (width, figure_id, geometry)
            assert geometry["naturalHeight"] == 941, (width, figure_id, geometry)
            assert geometry["right"] <= geometry["columnRight"] + 1, (width, figure_id, geometry)
            assert geometry["left"] >= geometry["columnLeft"] - 1, (width, figure_id, geometry)
            assert abs(geometry["width"]/geometry["height"] - 1672/941) < .015, (width, figure_id, geometry)
        assert page.locator(".econ-original-figure").count() == 2
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
