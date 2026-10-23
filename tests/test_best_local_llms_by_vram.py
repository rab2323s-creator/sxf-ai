#!/usr/bin/env python3
"""Regression contract for the editorial local LLM by VRAM guide."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tools/local-llm-vram-finder/index.html"
CSS = PAGE.parent / "guide.css"
JS = PAGE.parent / "selector.js"
CANONICAL = "https://sxf.si/tools/local-llm-vram-finder/"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.images = []
    def handle_starttag(self, tag, attrs):
        p = dict(attrs)
        if p.get("id"): self.ids.add(p["id"])
        if tag == "a": self.links.append(p.get("href", ""))
        if tag == "img": self.images.append(p)

def main():
    html = PAGE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    parsed = PageParser()
    parsed.feed(html)
    assert '<link rel="canonical" href="' + CANONICAL + '">' in html
    assert '<meta name="robots" content="index,follow' in html
    assert '<html lang="en">' in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert '<title>Local LLM VRAM Finder' in html
    assert "schema.org" in html and '"TechArticle"' in html
    for id_ in ("quick-picks", "model-finder", "comparison", "memory", "setup", "questions", "sources-title"):
        assert id_ in parsed.ids, id_
    for url in ("https://ollama.com/library/qwen3/tags",
                "https://ollama.com/library/gemma3/tags",
                "https://docs.ollama.com/context-length"):
        assert url in parsed.links, url
    assert "download sizes" in html.lower()
    assert "not measured peak VRAM" in html
    assert "noindex" not in html
    assert "@media(max-width:650px)" in css
    assert "prefers-reduced-motion" in css
    assert "evaluate(" in js and "textContent" in js
    assert "innerHTML" in js and "esc(" in js
    tools_hub = (ROOT / "tools/index.html").read_text(encoding="utf-8")
    assert 'href="/tools/local-llm-vram-finder/"' in tools_hub
    assert 'guides/best-local-llms-by-vram' not in tools_hub
    assert not (ROOT / 'guides/best-local-llms-by-vram').exists()
    sitemap = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    assert CANONICAL in sitemap
    assert 'https://sxf.si/guides/best-local-llms-by-vram/' not in sitemap
    result = subprocess.run(
        ["node", "-e", """
          const s=require('./tools/local-llm-vram-finder/selector.js');
          if(s.MODELS.length!==13)throw Error('Model count');
          for(const m of s.MODELS){
            if(!(m.size>0) || !s.SOURCES[m.source])throw Error(m.tag);
          }
          if(s.evaluate(8,'coding',8192).some(m=>m.status==='out'))throw Error('bad filter');
          if(!s.evaluate(16,'coding',8192).some(m=>m.tag==='qwen2.5-coder:14b'))throw Error('14b missing');
          if(s.evaluate(8,'invalid',8192).length)throw Error('invalid workload');
          if(s.evaluate(16,'vision',8192).some(m=>!m.use.includes('vision')))throw Error('cross-task result');
          console.log('PASS: selector contracts');
        """], cwd=ROOT, capture_output=True, text=True, check=True
    )
    print(result.stdout.strip())
    print("PASS: VRAM guide SEO, HTML, design and cross-page integration")

if __name__ == "__main__":
    main()
