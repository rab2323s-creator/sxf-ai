"""Durable GPT-5.6 Sol original source-backed SEO and reproducible cache-cost dossier."""
from __future__ import annotations
import csv,json,re
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"data/model-page-content/gpt-5-6-sol.html"
CSV_PATH=ROOT/"data/research/gpt56-sol-cache-economics-2026-11.csv"
URL="https://sxf.si/models/gpt-5-6-sol/"
DATASET="https://sxf.si/data/research/gpt56-sol-cache-economics-2026-11.csv"
TITLE="GPT-5.6 Sol: API Pricing, Benchmarks & GPT-6 Comparison | SXF"
DESCRIPTION=("GPT-5.6 Sol API pricing, 1.05M context, benchmarks and GPT-6/6.1 comparison. "
             "Try SXF's original 20-case prompt caching cost experiment and calculator.")
SOURCES=[
 "https://developers.openai.com/api/docs/models/gpt-5.6-sol",
 "https://developers.openai.com/api/docs/pricing",
 "https://developers.openai.com/api/docs/guides/prompt-caching",
 "https://openai.com/index/gpt-5-6/",
 "https://developers.openai.com/api/docs/models/gpt-6-sol",
 "https://developers.openai.com/api/docs/models/gpt-6.1-sol", DATASET]
FAQ=[
 ("What is GPT-5.6 Sol?","GPT-5.6 Sol is OpenAI's July 9, 2026 flagship model for complex professional work, coding, research and agentic workflows. The API model ID is gpt-5.6-sol."),
 ("Is GPT-5.6 the same model as GPT-5.6 Sol?","The gpt-5.6 API alias currently routes requests to the gpt-5.6-sol model. Use the exact ID for reproducible API calls."),
 ("How much does GPT-5.6 Sol cost?","As of November 10, 2026, promotional Standard short-context pricing is $4 uncached input, $0.40 cached read and $20 output per million text tokens. Promotional prices are published through November 30, 2026."),
 ("When does GPT-5.6 Sol promotional pricing end?","OpenAI publishes the current GPT-5.6 Sol promotional pricing through November 30, 2026. Recheck pricing before estimating requests beyond that date."),
 ("What is the GPT-5.6 Sol context window?","GPT-5.6 Sol documents 1,050,000 context tokens and up to 128,000 output tokens. Maximum capacity does not guarantee perfect recall."),
 ("What is GPT-5.6 Sol's knowledge cutoff?","OpenAI lists February 16, 2026 as the GPT-5.6 Sol knowledge cutoff."),
 ("What reasoning effort does GPT-5.6 Sol support?","GPT-5.6 Sol supports none, low, medium, high, xhigh and max, with medium as default."),
 ("Does GPT-5.6 Sol process images?","Yes. The official model card lists text and image input with text output."),
 ("How much does GPT-5.6 Sol prompt caching cost?","For short-context Standard requests, a cached read is $0.40, a 30-minute cache write is $5 and a 12-hour cache write is $10 per million tokens. Long-context requests have higher rates."),
 ("When does GPT-5.6 Sol long-context pricing start?","Prompts exceeding 272,000 input tokens use 2x input and cache rates and 1.5x output rates across the entire request. Exactly 272,000 uses short-context rates."),
 ("Is GPT-5.6 Sol cheaper than GPT-6 Sol?","At current short-context Standard rates, GPT-5.6 Sol lists $4 uncached input and $20 output versus GPT-6 Sol's $2 input and $10 output. Task-level value depends on output quality."),
 ("Is GPT-5.6 Sol the same as GPT-6.1 Sol?","No. gpt-5.6-sol and gpt-6.1-sol are different model IDs and generations with different prices and reasoning/tool capabilities."),
 ("How do I use the GPT-5.6 Sol API?","Send a Responses API request with model gpt-5.6-sol and a documented reasoning effort like medium; keep credentials in environment variables."),
 ("Is GPT-5.6 Sol available to every ChatGPT user?","ChatGPT plan availability differs from API availability. Consult the current plan documentation; the API ID does not imply it appears on every ChatGPT plan."),
 ("What did SXF independently test for GPT-5.6 Sol?","SXF calculated 20 hypothetical prompt-cache pricing scenarios using official API token rates and published a CSV. This is arithmetic billing research, not independent model-inference testing."),
 ("Are GPT-5.6 Sol benchmarks from SXF?","No. Model performance numbers are attributed to OpenAI's July 2026 launch tables; SXF's original contribution is separately labelled reproducible cost research."),
]
PREFIXES=(10000,100000,260000,300000)
CALLS=(1,2,3,10,100)
def active(model,date):
 values=[r for r in model["pricing"]["standard"] if r["start"]<=date and (not r.get("end") or date<=r["end"])]
 if len(values)!=1:raise ValueError("Exactly one active GPT-5.6 Sol pricing row required")
 return values[0]
def money(v):
 return "$"+f"{v:.4f}".rstrip("0").rstrip(".")
def cost(model,date,prefix,new,output,kind):
 if any(not isinstance(x,int) or x<0 for x in (prefix,new,output)):raise ValueError("Token counts must be nonnegative integers")
 if prefix+new>model["context_window"] or output>model["max_output"]:raise ValueError("Token limits exceeded")
 r=active(model,date)
 lc=model["pricing"]["long_context"]
 long=prefix+new>lc["threshold_input_tokens"]
 m=lc["multipliers"] if long else {k:1 for k in ("input","cached_input","cache_write","output")}
 kinds={"no":("input",1),"read":("cached_input",1),"write30":("cache_write",1),"write12":("cache_write",2)}
 if kind not in kinds:raise ValueError("Unknown cache type")
 key,factor=kinds[kind]
 return (prefix*r[key]*factor*m[key]+new*r["input"]*m["input"]+output*r["output"]*m["output"])/1_000_000
def scenarios(model,date,prefix,new,output,n):
 return (n*cost(model,date,prefix,new,output,"no"),
         cost(model,date,prefix,new,output,"write30")+(n-1)*cost(model,date,prefix,new,output,"read"),
         cost(model,date,prefix,new,output,"write12")+(n-1)*cost(model,date,prefix,new,output,"read"))
def replace_one(page,pattern,value):
 result,n=re.subn(pattern,lambda _:value,page,count=1,flags=re.S)
 if n!=1:raise ValueError("GPT-5.6 Sol generator anchor missing: "+pattern)
 return result
def enrich_gpt56_sol_page(page, models_by_id):
 if 'id="sxf-gpt56-sol-research"' in page:raise ValueError("Duplicate GPT-5.6 Sol research")
 model,g6,g61=(models_by_id[k] for k in ("gpt-5.6-sol","gpt-6-sol","gpt-6.1-sol"))
 date=max("2026-11-10",*(m["provenance"]["verified_at"] for m in (model,g6,g61)))
 for item in (model,g6,g61):
  if (item["context_window"],item["max_output"])!=(1050000,128000):raise ValueError("Model context changed; review required")
  lc=item["pricing"]["long_context"]
  if lc["threshold_input_tokens"]!=272000 or lc["multipliers"]!={"input":2,"cached_input":2,"cache_write":2,"output":1.5}:
   raise ValueError("Long-context contract changed; review required")
 r=active(model,date)
 if any(abs(r[k]-v)>1e-9 for k,v in (("input",4),("cached_input",.4),("cache_write",5),("output",20))):
  raise ValueError("Promotional GPT-5.6 Sol prices changed; review this study")
 if model["knowledge_cutoff"]!="2026-02-16" or model["reasoning"]["default"]!="medium":
  raise ValueError("GPT-5.6 Sol documentation changed")
 with CSV_PATH.open(newline="",encoding="utf-8") as stream:records=list(csv.DictReader(stream))
 if len(records)!=20:raise ValueError("Wrong GPT-5.6 Sol CSV row count")
 rows=[]
 for rec,(prefix,n) in zip(records,((p,i) for p in PREFIXES for i in CALLS)):
  if (rec["case_id"],int(rec["prefix_tokens"]),int(rec["new_tokens_each"]),int(rec["output_tokens_each"]),int(rec["requests"]))!=(
   f"prefix-{prefix}-calls-{n}",prefix,2000,4000,n):
   raise ValueError("SXF research scenario metadata or inputs changed")
  a,b,c=scenarios(model,date,prefix,2000,4000,n)
  if rec["price_tier"]!=("long" if prefix+2000>272000 else "short") or any(abs(float(rec[k])-v)>1e-8 for k,v in (
   ("uncached_total_usd",a),("cache_30m_usd",b),("cache_12h_usd",c),
   ("saving_30m_usd",a-b),("saving_12h_usd",a-c))):
   raise ValueError("Original CSV study fails price recomputation")
  rows.append("<tr><th scope='row'>"+f"{prefix:,}"+"</th><td>"+str(n)+"</td><td>$"+f"{a:.6f}"+"</td><td>$"+f"{b:.6f}"+"</td><td>$"+f"{c:.6f}"+"</td><td>$"+f"{a-b:.6f}"+"</td></tr>")
 ten=scenarios(model,date,100000,2000,4000,10)
 boundary_at=cost(model,date,272000,0,4000,"no")
 boundary_above=cost(model,date,272001,0,4000,"no")
 text=CONTENT.read_text(encoding="utf-8")
 tokens={"LAB_ROWS":"".join(rows),"FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(a)+"</p></details>" for q,a in FAQ),
 "TEN_NO":"$"+f"{ten[0]:.6f}","TEN_30":"$"+f"{ten[1]:.6f}","TEN_12":"$"+f"{ten[2]:.6f}",
 "TEN_SAVING":"$"+f"{ten[0]-ten[1]:.6f}","BOUNDARY_AT":"$"+f"{boundary_at:.6f}","BOUNDARY_ABOVE":"$"+f"{boundary_above:.6f}"}
 for label,record in (("SOL",model),("G6",g6),("G61",g61)):
  p=active(record,date)
  for suffix,key in (("INPUT","input"),("CACHED","cached_input"),("OUTPUT","output")):tokens[label+"_"+suffix]=money(p[key])
  if label=="SOL":
   for suffix,value in (("WRITE30",p["cache_write"]),("WRITE12",2*p["cache_write"]),
    ("LONG_INPUT",2*p["input"]),("LONG_CACHED",2*p["cached_input"]),
    ("LONG_WRITE30",2*p["cache_write"]),("LONG_WRITE12",4*p["cache_write"]),("LONG_OUTPUT",1.5*p["output"])):tokens["SOL_"+suffix]=money(value)
   for suffix,key in (("INPUT","input"),("CACHED","cached_input"),("WRITE30","cache_write"),("OUTPUT","output")):tokens["RATE_"+suffix]=str(p[key])
   tokens["RATE_WRITE12"]=str(p["cache_write"]*2)
 for key,value in tokens.items():
  marker="{{"+key+"}}"
  if marker in text:text=text.replace(marker,value)
 if "{{" in text:raise ValueError("Unresolved source placeholders")
 source=re.search(r'<script type="application/ld\+json">(.+?)</script>',page,re.S)
 if not source:raise ValueError("Original JSON-LD missing")
 schema=json.loads(source.group(1))
 article=next(x for x in schema["@graph"] if x["@type"]=="TechArticle")
 article.update({"headline":TITLE.replace(" | SXF",""),"description":DESCRIPTION,
  "dateModified":date,"mainEntityOfPage":URL,"citation":SOURCES,"isPartOf":{"@id":"https://sxf.si/#website"}})
 schema["@graph"].append({"@type":"FAQPage","@id":URL+"#faq",
   "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]})
 schema["@graph"].append({"@type":"Dataset","@id":DATASET+"#dataset",
   "name":"SXF GPT-5.6 Sol original prompt cache economics — 20 scenarios",
   "description":"Twenty fixed hypothetical Standard API billing scenarios. Comparison of uncached requests with 30-minute and 12-hour cache-write pricing; not a model-performance test.",
   "url":DATASET,"datePublished":"2026-11-10",
   "creator":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
   "isBasedOn":"https://developers.openai.com/api/docs/pricing",
   "measurementTechnique":"Deterministic calculations of documented per-million token rates and long-context multipliers.",
   "distribution":{"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":DATASET}})
 page=replace_one(page,r'<script type="application/ld\+json">.+?</script>',
  '<script type="application/ld+json">'+json.dumps(schema,separators=(",",":"),ensure_ascii=False).replace("<",r"\u003c")+'</script>')
 for pat,value in (
  (r'<title>.*?</title>',"<title>"+escape(TITLE)+"</title>"),
  (r'<meta name="description" content="[^"]*" />','<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<meta property="og:title" content="[^"]*" />','<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
  (r'<meta property="og:description" content="[^"]*" />','<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<meta name="twitter:title" content="[^"]*" />','<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
  (r'<meta name="twitter:description" content="[^"]*" />','<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<body class="intel-page model-page">','<body class="intel-page model-page g56-page">')):
  page=replace_one(page,pat,value)
 page=replace_one(page,r'(?=<section class="model-change-watch shell")',text+"\n      ")
 page=replace_one(page,r"(?=</head>)",'<link rel="stylesheet" href="/models/gpt-5-6-sol/research.css?v=20261110-a" />\n      ')
 page=replace_one(page,r"(?=</body>)",'<script src="/models/gpt-5-6-sol/research.js?v=20261110-a" defer></script>')
 if page.count("<h1>")!=1 or "data-model-history" not in page:raise ValueError("Model page context/history regressed")
 return page
