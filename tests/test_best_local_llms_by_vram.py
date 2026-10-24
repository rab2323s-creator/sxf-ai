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
    # Reviewed measured evidence is visible but cannot silently replace estimates.
    for snippet in ('id="measured-evidence"', '64.23 generated tokens/second',
                    'highest observed', 'entire-GPU', 'reported by Ollama',
                    'original ZIP is not publicly hosted', 'qwen3-vl:4b-instruct',
                    'not</em> verified', 'not</strong> GPU usage',
                    'The original ZIP is not publicly hosted'):
        assert snippet.lower() in html.lower(), snippet
    assert 'href="#measured-evidence"' in html
    assert 'github.com/rab2323s-creator/sxf-ai/blob/main/docs/benchmarks/tesla-t4-qwen3-vl-4b-instruct-2026-10-24.md' in html
    assert json.loads((ROOT / "data/local-llm-benchmarks.json").read_text())["measurements"] == []
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
    assert 'id="vram-search"' in html and 'id="vram-mode"' in html
    assert "178 GGUF single-file variants" in html and "13 Ollama tags" in html
    assert (ROOT / "data/local-llm-sources.json").is_file()
    assert (ROOT / "scripts/update_local_llm_catalog.py").is_file()
    result = subprocess.run(
        ["node", "-e", """
          const s=require('./tools/local-llm-vram-finder/selector.js');
          const list=s.validate(require('./data/local-llm-catalog.json'));
          if(list.length!==191)throw Error('Expected reviewed 191 source variants');
          for(const m of list){
            for(const workload of m.workloads){
              for(const ctx of [4096,8192,16384,32768]){
                const same=s.evaluate(16,workload,ctx,[m])[0];
                const reverse=s.hardwareFor(m,ctx,workload);
                if(!same||same.planning!==reverse.planning)throw Error('Forward/reverse mismatch '+m.id);
              }
            }
          }
          if(s.evaluate(8,'invalid',8192,list).length)throw Error('bad task');
          if(!s.search('coder','all',list).length)throw Error('search missing');
          const families=s.groupFamilies(s.evaluate(16,'chat',8192,list));
          if(families.some(g=>!g.variants.length))throw Error('empty family');
          const vision=list.find(m=>m.format==='GGUF'&&m.workloads.includes('vision'));
          if(!s.visionEvidence(vision).includes('NOT validated'))throw Error('Missing vision caveat');
          const low=list.find(m=>m.quantization==='Q2_K');
          const q4=list.find(m=>m.quantization==='Q4_K_M');
          if(!(s.quantRank(low)>s.quantRank(q4)))throw Error('low-bit quality caution');
          const coding=s.groupFamilies(s.evaluate(16,'coding',8192,list).filter(m=>m.status!=='out'));
          const conditional=coding.find(g=>g.primary.quantization==='Q2_K');
          if(!conditional||!s.screeningAssessment(conditional,'gpu','coding').label.startsWith('Conditional'))throw Error('Low-bit labeled as preferred');
          const ordinary=coding.find(g=>!g.quantWarning);
          if(!ordinary||!s.screeningAssessment(ordinary,'gpu','coding').label.includes('Memory candidate'))throw Error('Memory-only candidate label missing');
          const visionGroups=s.groupFamilies(s.evaluate(24,'vision',4096,list));
          const visionCandidate=visionGroups.find(g=>g.primary.format==='GGUF'&&!g.quantWarning);
          if(!visionCandidate||!s.screeningAssessment(visionCandidate,'gpu','vision').label.includes('Needs validation'))throw Error('Unverified vision not flagged');
          const reverse=s.screeningAssessment(ordinary,'model','coding');
          if(!reverse.label.includes('Estimated GPU tier'))throw Error('Reverse must disclose estimate');
          const measurable={modelId:list[0].id,gpu:'Test-only GPU',runtime:'test',quantization:list[0].tag,measuredAt:'2026-10-24',sourceUrl:'https://example.org/evidence',tokensPerSecond:12.5,contextTokens:4096,concurrency:1,evidenceType:'measured',reviewStatus:'draft-not-published'};
          const draft=s.joinBenchmarks(list,{schemaVersion:1,measurements:[measurable]});
          if(draft[0].measurements.length!==0)throw Error('Unapproved evidence leaked');
          const approved=s.joinBenchmarks(list,{schemaVersion:1,measurements:[{...measurable,reviewStatus:'approved'}]});
          if(approved[0].measurements.length!==1)throw Error('Approved measured evidence hidden');
          console.log('PASS: v3.1 conditional, vision, reverse and memory-only evidence labels');
          console.log('PASS: v3 all forward/reverse estimates, family grouping, vision and quantization caveats');
        """], cwd=ROOT, capture_output=True, text=True, check=True
    )
    print(result.stdout.strip())
    print("PASS: VRAM guide SEO, HTML, design and cross-page integration")

if __name__ == "__main__":
    main()
