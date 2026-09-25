#!/usr/bin/env python3
from __future__ import annotations
import email.utils,json,re,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data"/"news.json"
SOURCES=[("OpenAI","https://openai.com/news/rss.xml"),("Google AI","https://blog.google/technology/ai/rss/"),("Hugging Face","https://huggingface.co/blog/feed.xml"),("GitHub","https://github.blog/changelog/feed/")]
USER_AGENT="SXF-AI-Radar/1.0 (+https://sxf.si/)";MAX_ITEMS=80;MAX_AGE_DAYS=21
def text(node,*names):
    for name in names:
        found=node.find(name)
        if found is not None and found.text:return found.text.strip()
    return ""
def clean_title(title):return re.sub(r"\s+"," ",title).strip()[:240]
def parse_date(value):
    if not value:return datetime.now(timezone.utc)
    try:
        d=email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:pass
    try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:return datetime.now(timezone.utc)
def categorize(title,source):
    t=title.lower()
    if any(k in t for k in ["open source","open-source","github","weights","checkpoint"]):return "Open Source"
    if any(k in t for k in ["model","gpt","gemini","claude","llm","vision","reasoning","multimodal","embedding"]):return "Models"
    if any(k in t for k in ["research","paper","study","benchmark","evaluation","science","safety"]):return "Research"
    return "Tools"
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def parse_feed(source,body):
    root=ET.fromstring(body);rows=[]
    for item in root.findall(".//item"):
        title=clean_title(text(item,"title"));link=text(item,"link");published=text(item,"pubDate","date")
        if title and link:rows.append((title,link,published))
    if not rows:
        for entry in root.findall(".//{*}entry"):
            title=clean_title(text(entry,"{*}title"));link=""
            for ln in entry.findall("{*}link"):
                href=ln.attrib.get("href","");rel=ln.attrib.get("rel","alternate")
                if href and rel in ("alternate",""):link=href;break
            published=text(entry,"{*}published","{*}updated")
            if title and link:rows.append((title,link,published))
    return [{"title":title,"url":link,"source":source,"published":parse_date(published).isoformat().replace("+00:00","Z"),"category":categorize(title,source)} for title,link,published in rows]
def valid_url(url):
    p=urlparse(url);return p.scheme in ("http","https") and bool(p.netloc)
def main():
    items=[];errors=[]
    for source,url in SOURCES:
        try:items.extend(parse_feed(source,fetch(url)))
        except Exception as exc:errors.append(f"{source}: {exc}")
    cutoff=datetime.now(timezone.utc)-timedelta(days=MAX_AGE_DAYS);dedup={}
    for item in items:
        if not valid_url(item["url"]):continue
        dt=parse_date(item["published"])
        if dt<cutoff:continue
        key=re.sub(r"\W+","",item["title"].lower())[:140]
        current=dedup.get(key)
        if current is None or dt>parse_date(current["published"]):dedup[key]=item
    final=sorted(dedup.values(),key=lambda x:parse_date(x["published"]),reverse=True)[:MAX_ITEMS]
    if not final and errors and OUT.exists():
        try:final=json.loads(OUT.read_text(encoding="utf-8")).get("items",[])
        except Exception:pass
    payload={"updated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"items":final,"feed_errors":errors}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {len(final)} items. Errors: {len(errors)}")
if __name__=="__main__":main()