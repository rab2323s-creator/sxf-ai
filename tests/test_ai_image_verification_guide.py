#!/usr/bin/env python3
"""Offline SEO, source, accessibility and cross-link regression for the public AI image guide."""
import ast
import json
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
SLUG = "how-to-tell-if-an-image-is-ai-generated"
URL = "https://sxf.si/guides/" + SLUG + "/"
PAGE = ROOT / "guides" / SLUG / "index.html"
JS = PAGE.parent / "evidence-ladder.js"

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.h1=0
        self.sections=set()
        self.main=0
        self.titles=[]
        self.paired=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.ids.append(a["id"])
        if tag=="h1": self.h1+=1
        if tag=="main": self.main+=1
        if tag=="section" and "id" in a: self.sections.add(a["id"])
        if tag=="a" and "href" in a:self.links.append(a["href"])
        if tag=="label" and "for" in a:self.paired.append(a["for"])

def main():
    h=PAGE.read_text(encoding="utf-8")
    p=Audit();p.feed(h)
    assert p.h1==1 and p.main==1
    assert h.count("</body>")==1 and h.count("</html>")==1
    assert len(set(p.ids))==len(p.ids), "Duplicate ids"
    assert all(field in p.ids for field in p.paired)
    assert len(p.paired)==4
    assert h.count("<details>")==7
    assert all(i in p.sections for i in ("short-answer","seven-checks","evidence-ladder","interpret","detectors","faq","sources"))
    assert 'rel="canonical" href="' + URL + '"' in h
    assert 'name="robots" content="index,follow' in h
    assert 'application/ld+json' in h
    s=h.split('<script type="application/ld+json">',1)[1].split("</script>",1)[0]
    graph=json.loads(s)["@graph"]
    assert {"WebPage","Article","BreadcrumbList","FAQPage"}.issubset({v["@type"] for v in graph})
    assert any(v["@type"]=="Article" and v["mainEntityOfPage"]["@id"]==URL+"#webpage" for v in graph)
    assert len([v for v in graph if v["@type"]=="FAQPage"][0]["mainEntity"])==7
    assert h.count("class=\"img-method\"")==7
    assert "not a trained image classifier" in h
    for domain in ("support.google.com","help.openai.com","contentcredentials.org","openai.com/verify"):
        assert domain in h, domain
    script=JS.read_text(encoding="utf-8")
    assert "fetch(" not in script and "XMLHttpRequest" not in script
    assert "navigator.clipboard" in script and 'observation==="negative"' in script
    assert 'src="/guides/'+SLUG+'/evidence-ladder.js"' in h
    for path in ["guides/index.html","scripts/update_news.py","sitemap.xml"]:
        assert "/guides/"+SLUG+"/" in (ROOT/path).read_text(encoding="utf-8"), path
    for path in ["guides/why-does-chatgpt-make-things-up/index.html","guides/ai-deception-alignment-faking/index.html"]:
        assert "/guides/"+SLUG+"/" in (ROOT/path).read_text(encoding="utf-8"), path
    index=(ROOT/"guides/index.html").read_text(encoding="utf-8")
    assert "SXF's original interactive Evidence Ladder" in index
    print("PASS: image guide SEO, primary sources, cross-links, sitemap, generator parity and tool UI contracts")

if __name__=="__main__":
    main()
