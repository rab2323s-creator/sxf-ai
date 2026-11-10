"""Durable original Claude Sonnet 5 research, dated evidence, safe SEO and cost lab."""
from __future__ import annotations
import csv
import json
import re
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"data/model-page-content/claude-sonnet-5.html"
DATA=ROOT/"data/research/claude-sonnet-5-cache-reuse-2026-11.csv"
URL="https://sxf.si/models/claude-sonnet-5/"
DATASET="https://sxf.si/data/research/claude-sonnet-5-cache-reuse-2026-11.csv"
TITLE="Claude Sonnet 5: API Pricing, Benchmarks & Sonnet 5.5 | SXF"
DESCRIPTION="Claude Sonnet 5 API pricing, specs, 1M context, benchmarks and Sonnet 5.5 comparison. Test SXF's original 20-case prompt cache cost study."
SOURCES=[
 "https://platform.claude.com/docs/en/models/sonnet-5/overview",
 "https://platform.claude.com/docs/en/models/sonnet-5-5/overview",
 "https://platform.claude.com/docs/en/about-claude/pricing",
 "https://www.anthropic.com/news/claude-sonnet-5",
 "https://www.anthropic.com/news/claude-sonnet-5-5",
 "https://artificialanalysis.ai/models/comparisons/claude-sonnet-5-5-high-vs-claude-sonnet-5-high",
 DATASET]
FAQ=[
 ("What is Claude Sonnet 5?","Claude Sonnet 5 is Anthropic's June 30, 2026 balanced model for coding, agentic workflows, research and professional knowledge work. Its exact API model ID is claude-sonnet-5."),
 ("How much does Claude Sonnet 5 cost per million tokens?","Standard Claude Sonnet 5 API pricing is $2 uncached input, $0.20 cached input read and $10 output per million tokens, as rechecked on November 10, 2026. Special service options and tools can have separate fees."),
 ("Is Claude Sonnet 5 API pricing promotional?","No. Anthropic announced the $2 input and $10 output Standard rates as permanent on August 10, 2026. Published rates can still change in the future."),
 ("What is the Claude Sonnet 5 model ID?","Use claude-sonnet-5 as the versioned model ID in the Anthropic Messages API."),
 ("What is Claude Sonnet 5's context window?","Anthropic documents a 1,000,000-token context window and 128,000 maximum output tokens for Claude Sonnet 5. These are serving limits, not performance guarantees."),
 ("What is the Claude Sonnet 5 knowledge cutoff?","The official Sonnet 5 model card lists January 2026 as its knowledge cutoff. This is not the page update date."),
 ("How many parameters does Claude Sonnet 5 have?","Anthropic has not published a verified parameter count or downloadable weights for Claude Sonnet 5. Context tokens are not model parameters."),
 ("Is Claude Sonnet 5 open source?","No. Claude Sonnet 5 is a proprietary hosted Anthropic model; an official model-weights download is not provided."),
 ("What is the difference between Claude Sonnet 5 and 5.5?","Claude Sonnet 5 and 5.5 are distinct API model IDs. Sonnet 5.5 launched on September 28, 2026 and lists a newer knowledge cutoff and a lower cached-read rate than Sonnet 5."),
 ("Is Claude Sonnet 5 the latest Sonnet model?","No. Anthropic released Claude Sonnet 5.5 on September 28, 2026. Check the official model directory for the latest availability."),
 ("How much do Claude Sonnet 5 prompt cache writes cost?","Standard five-minute cache writes cost $2.50 and one-hour writes cost $4 per million input tokens; subsequent eligible cached reads cost $0.20 per million tokens."),
 ("When does Sonnet 5 prompt caching save money?","For identical eligible reusable prefixes, SXF's dated hypothetical pricing study finds a five-minute cache write plus one successful cached read costs less than two all-uncached calls. Real cache hits are not guaranteed."),
 ("Does Claude Sonnet 5 support images?","Yes. The official model specification documents text and image input with text output."),
 ("How to call Claude Sonnet 5 in Python?","Use the Anthropic Python SDK Messages API with model='claude-sonnet-5', a max_tokens value and a messages array, and keep ANTHROPIC_API_KEY in secure server environment variables."),
 ("Is Claude Sonnet 5 available in GitHub Copilot?","GitHub Copilot model availability and plan conditions are separate from Anthropic's direct API. Check GitHub's current model list rather than inferring access from the API model ID."),
 ("Did SXF independently benchmark Claude Sonnet 5?","SXF's original research is a 20-scenario reproducible billing simulation for prompt caching, not a live model inference or latency benchmark. Performance scores are explicitly attributed to Artificial Analysis."),
]
PREFIXES=(2048,16000,100000,500000)
CALLS=(1,2,3,10,100)

def current(model,date):
 rows=[r for r in model["pricing"]["standard"] if r["start"]<=date and (r.get("end") is None or date<=r["end"])]
 if len(rows)!=1:raise ValueError("Expected one active Standard tier for "+model["model_id"])
 return rows[0]

def rate_cost(rate,prefix,fresh,output,kind):
 if any(type(x)!=int or x<0 for x in (prefix,fresh,output)):raise ValueError("Invalid token count")
 if prefix+fresh>1000000 or output>128000:raise ValueError("Token limit exceeded")
 key={"uncached":"input","read":"cached_input","five":"cache_write_5m","hour":"cache_write_1h"}
 if kind not in key:raise ValueError("Unknown cost category")
 return (prefix*rate[key[kind]]+fresh*rate["input"]+output*rate["output"])/1e6

def scenarios(rate,prefix,fresh,output,n):
 return [n*rate_cost(rate,prefix,fresh,output,"uncached"),
         rate_cost(rate,prefix,fresh,output,"five")+(n-1)*rate_cost(rate,prefix,fresh,output,"read"),
         rate_cost(rate,prefix,fresh,output,"hour")+(n-1)*rate_cost(rate,prefix,fresh,output,"read")]

def replace_one(source,needle,replacement):
 value,n=re.subn(needle,lambda _:replacement,source,count=1,flags=re.S)
 if n!=1:raise ValueError("Claude Sonnet 5 render anchor changed: "+needle)
 return value

def enrich_claude_sonnet5_page(page,by_id):
 if 'id="sxf-sonnet5-research"' in page:raise ValueError("Duplicate original Sonnet 5 dossier")
 five,next_model=(by_id[k] for k in ("claude-sonnet-5","claude-sonnet-5-5"))
 date=max("2026-11-10",five["provenance"]["verified_at"],next_model["provenance"]["verified_at"])
 for m in (five,next_model):
  if (m["context_window"],m["max_output"])!=(1000000,128000):raise ValueError("Anthropic capacity changed; re-review the dossier")
  if m["pricing_basis"]["meter"]!="tokens":raise ValueError("Only token priced models")
 if five["knowledge_cutoff"]!="2026-01" or next_model["knowledge_cutoff"]!="2026-06":
  raise ValueError("Knowledge cutoff changed; verify primary source")
 a,b=current(five,date),current(next_model,date)
 for rate,expected in ((a,(2,.2,2.5,4,10)),(b,(2,.1,2.5,4,10))):
  if any(abs(rate[k]-v)>1e-8 for k,v in zip(("input","cached_input","cache_write_5m","cache_write_1h","output"),expected)):
   raise ValueError("Claude Sonnet pricing changed: research update required")
 with DATA.open(newline="",encoding="utf-8") as f:records=list(csv.DictReader(f))
 if len(records)!=20:raise ValueError("Missing 20-case SXF CSV")
 rows=[]
 for row,(prefix,n) in zip(records,((p,n) for p in PREFIXES for n in CALLS)):
  assert (row["scenario_id"],int(row["reused_prefix_tokens"]),int(row["fresh_input_per_request"]),
   int(row["output_per_request"]),int(row["requests"]))==(f"p{prefix}-n{n}",prefix,2000,4000,n)
  amounts=scenarios(a,prefix,2000,4000,n)+scenarios(b,prefix,2000,4000,n)
  computed=amounts+[amounts[0]-amounts[1],amounts[1]-amounts[4]]
  fields=("sonnet5_uncached_usd","sonnet5_cache5m_usd","sonnet5_cache1h_usd",
          "sonnet55_uncached_usd","sonnet55_cache5m_usd","sonnet55_cache1h_usd",
          "sonnet5_cache5m_savings_usd","sonnet55_read_savings_vs_sonnet5_usd")
  # Published CSV values use six decimal places: tolerate only half a micro-dollar.
  if any(abs(float(row[k])-v)>5.01e-7 for k,v in zip(fields,computed)):
   raise ValueError("Original Sonnet 5 dataset diverged from official rates")
  def visible_money(value):
   # Source CSV preserves six decimals; the reader-facing table stays legible.
   return "$"+(f"{value:,.2f}" if abs(value)>=0.01 else f"{value:,.4f}")
  rows.append("<tr><th scope='row'>"+f"{prefix:,}"+"</th><td>"+str(n)+"</td>"+
    "".join("<td>"+visible_money(v)+"</td>" for v in (amounts[0],amounts[1],amounts[2],amounts[0]-amounts[1]))+"</tr>")
 sample=scenarios(a,100000,2000,4000,10)
 markup=TEMPLATE.read_text(encoding="utf-8")
 def dollars(x):return "$"+f"{x:.2f}"
 tokens={"SOURCE_VERIFIED":five["provenance"]["verified_at"],"LAB_ROWS":"".join(rows),
  "FAQ_HTML":"".join("<details><summary>"+escape(q)+"</summary><p>"+escape(v)+"</p></details>" for q,v in FAQ),
  "EXAMPLE_NO":"$"+f"{sample[0]:.2f}","EXAMPLE_5M":"$"+f"{sample[1]:.2f}"}
 for name,rate in (("FIVE",a),("NEXT",b)):
  for suffix,key in (("INPUT","input"),("OUTPUT","output"),("CACHED","cached_input"),("WRITE5","cache_write_5m"),("WRITE1H","cache_write_1h")):
   tokens[name+"_"+suffix]=dollars(rate[key])
   tokens["RAW_"+name+"_"+suffix]=str(rate[key])
 for key,v in tokens.items():
  marker="{{"+key+"}}"
  if marker in markup:markup=markup.replace(marker,v)
 if "{{" in markup:raise ValueError("Unresolved research placeholders")
 if "**Assumptions:**" in markup:
  markup=markup.replace("**Assumptions:**","<strong>Assumptions:</strong>")
 match=re.search(r'<script type="application/ld\+json">(.+?)</script>',page,re.S)
 if not match:raise ValueError("Original model schema missing")
 schema=json.loads(match.group(1))
 article=next(n for n in schema["@graph"] if n["@type"]=="TechArticle")
 article.update({"headline":TITLE.replace(" | SXF",""),"description":DESCRIPTION,
  "dateModified":five["provenance"]["verified_at"],"mainEntityOfPage":URL,
  "citation":SOURCES})
 schema["@graph"].append({"@type":"FAQPage","@id":URL+"#faq",
  "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":answer}} for q,answer in FAQ]})
 schema["@graph"].append({"@type":"Dataset","@id":DATASET+"#dataset",
  "name":"SXF Claude Sonnet 5 vs 5.5 prompt cache economics: 20 reproducible scenarios",
  "description":"Reproducible Standard token-cost simulation comparing five-minute and one-hour cache writes, all-uncached runs and successful cached reads. Not a paid model performance test.",
  "url":DATASET,"datePublished":"2026-11-10",
  "creator":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
  "isBasedOn":"https://platform.claude.com/docs/en/about-claude/pricing",
  "measurementTechnique":"Deterministic token arithmetic under explicit cache-hit and fixed-token-count assumptions.",
  "distribution":{"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":DATASET}})
 page=replace_one(page,r'<script type="application/ld\+json">.+?</script>',
  '<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False,separators=(",",":")).replace("<",r"\u003c")+'</script>')
 for pattern,v in (
  (r"<title>.*?</title>","<title>"+escape(TITLE)+"</title>"),
  (r'<meta name="description" content="[^"]*" />','<meta name="description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<meta property="og:title" content="[^"]*" />','<meta property="og:title" content="'+escape(TITLE,quote=True)+'" />'),
  (r'<meta property="og:description" content="[^"]*" />','<meta property="og:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<meta name="twitter:title" content="[^"]*" />','<meta name="twitter:title" content="'+escape(TITLE,quote=True)+'" />'),
  (r'<meta name="twitter:description" content="[^"]*" />','<meta name="twitter:description" content="'+escape(DESCRIPTION,quote=True)+'" />'),
  (r'<body class="intel-page model-page">','<body class="intel-page model-page cs5-page">'),
 ):
  page=replace_one(page,pattern,v)
 page=replace_one(page,r'(?=<section class="model-change-watch shell")',markup+"\n      ")
 # Eliminate the redundant generic model fact sheet only for this researched route:
 # its source facts, vendor links and status are incorporated into the dossier.
 page=replace_one(page,
  r'<section class="model-reference model-reference-deep shell">[\s\S]*?(?=<section class="cs5-dossier shell")',
  "")
 page=replace_one(page,
  r'<h1>Claude Sonnet 5<br><span>verified model reference\.</span></h1>',
  '<h1>Claude Sonnet 5<br><span>API Pricing, Specs &amp; Benchmarks</span></h1>')
 page=replace_one(page,
  r'<p>Balanced Claude tier combining speed and intelligence for coding, agents, and production knowledge work\.</p>',
  '<p>Official model specifications, clear API pricing and an independently reproducible 20-scenario SXF cache-cost study.</p>')
 page=replace_one(page,
  r'(<section class="evaluation-model-bridge shell" data-model-evaluations="claude-sonnet-5")',
  '<section id="cs5-benchmark-observations" class="evaluation-model-bridge shell" data-model-evaluations="claude-sonnet-5"')

 page=replace_one(page,r'(?=</head>)','<link rel="stylesheet" href="/models/claude-sonnet-5/research.css?v=20261110-b" />\n      ')
 page=replace_one(page,r'(?=</body>)','<script defer src="/models/claude-sonnet-5/research.js?v=20261110-b"></script>')
 if page.count("<h1>")!=1 or "data-model-history" not in page:raise ValueError("Original reference and historical ledger must survive")
 return page
