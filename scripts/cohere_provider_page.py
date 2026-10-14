"""Source-backed Cohere provider guide surviving scheduled site generation."""
import json
import re
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRAGMENT=ROOT/"data/provider-page-content/cohere-seo.html"
URL="https://sxf.si/providers/cohere/"
TITLE="Cohere AI Models (2026): Command, Embed, Rerank & Pricing | SXF"
DESCRIPTION="Compare 10 Cohere AI models: Command A+, Embed 5 Pro/Fast, Rerank 4, Parse 5 and North. Explore pricing units, API examples, model specs and RAG workflows."
FAMILIES={
    "command-a-plus-05-2026":("Command","Enterprise chat, reasoning and agents","Text"),
    "command-a-reasoning-08-2025":("Command","Long-context reasoning and agents","Text"),
    "embed-v4.0":("Embed","Text and image embedding vectors","Vectors"),
    "embed-v5.0-pro":("Embed","Multimodal retrieval, quality focus","Vectors"),
    "embed-v5.0-fast":("Embed","Multimodal retrieval, latency focus","Vectors"),
    "rerank-v4.0-pro":("Rerank","Higher-quality document reranking","Ranked items"),
    "rerank-v4.0-fast":("Rerank","Lower-latency document reranking","Ranked items"),
    "parse-v5.0":("Parse","Document extraction and layout","Structured text"),
    "north-mini-code-1-0":("North","Coding agents and repo analysis","Text"),
    "north-small-translate-1-0":("North","Multilingual translation","Text"),
}
SOURCES=[
"https://docs.cohere.com/v1/docs/models",
"https://docs.cohere.com/docs/command-a-plus",
"https://docs.cohere.com/docs/cohere-embed",
"https://docs.cohere.com/docs/rerank",
"https://docs.cohere.com/docs/parse",
"https://cohere.com/pricing",
"https://docs.cohere.com/docs/model-vault/standard/pricing",
"https://docs.cohere.com/v2/docs/rag-complete-example",
]
FAQ=[
("What AI models does Cohere offer?","Cohere offers Command models for generation and agents, Embed for vector search, Rerank for ordering search results, Parse for document extraction, and North models for specialized coding and translation tasks. This SXF directory tracks 10 Cohere model pages as of October 2026."),
("Which Cohere model should I use for a chatbot?","Use a Command chat model such as Command A+ if it meets your language, tool, latency and deployment requirements. Embed and Rerank serve supporting retrieval tasks rather than replacing the answer-generation model."),
("What is the difference between Cohere Embed and Rerank?","Embed creates vectors so a search system can retrieve semantically similar items. Rerank takes a query and an existing set of candidate documents and orders those candidates by relevance. They are often used together."),
("What is Cohere Command A+?","Command A+ is a Cohere multimodal enterprise chat and agent model. The official model card lists 128K context, 64K maximum output, tool use, multilingual support, citations and structured outputs. Its API ID is command-a-plus-05-2026."),
("Is Cohere API access free?","Cohere provides free trial API keys with usage and rate limits; trial access is not unrestricted production access. Production API billing and dedicated Model Vault commitments depend on the model, plan and serving channel."),
("How does Cohere Rerank pricing work?","Hosted reranking is measured in search units: one query with up to 100 ranked documents is one search, while long documents may be split into additional chunks. The exact current per-search price depends on the plan; Model Vault uses a separate per-instance rate."),
("How much does Cohere Model Vault cost?","Published examples include $3 per hour for Embed 5 Pro Small, $5 per hour for Rerank 4 Pro Medium and $4 per hour for Parse 5 Medium, per dedicated instance. These are not per-token API rates; confirm current commitment and region terms."),
("Which model is better, Embed 5 Pro or Embed 5 Fast?","Cohere positions Embed 5 Pro for retrieval quality and Embed 5 Fast for lower latency and higher throughput. Cohere documents a shared embedding space between Pro and Fast. The best choice depends on your evaluation set and operating requirements."),
("When should I use Cohere Parse 5?","Use Parse 5 to extract text, tables, forms and layout information from PDFs, slides and images before indexing enterprise documents. It produces document representations and does not replace a chat model or vector search system."),
("Can I use Cohere models with Python?","Yes. Install the cohere package, authenticate with an API key and use cohere.ClientV2 with the Chat, Embed, Rerank or Parse endpoints. Models and supported API features can differ by endpoint and deployment."),
("Can Cohere models run privately?","Cohere offers dedicated Model Vault and private deployment options for supported models. Availability, capacity, terms and whether open weights can be self-hosted must be verified for the specific model and deployment region."),
]

def enrich_cohere_provider(page, models):
    if page.count("</main>")!=1: raise ValueError("Cohere provider main count")
    catalog={m["model_id"]:m for m in models}
    if set(catalog)!=set(FAMILIES): raise ValueError("Cohere model lineup changed; update guide")
    rows=[]
    for m in models:
        family,purpose,output=FAMILIES[m["model_id"]]
        context=f'{int(m["context_window"]):,}' if m.get("context_window") is not None else "Not published"
        rows.append("<tr><th scope='row'><a href='"+escape(m["sxf_url"],quote=True)+"'>"+escape(m["model"])+"</a></th><td>"+escape(family)+"</td><td>"+escape(purpose)+"</td><td>"+context+" tokens</td><td>"+escape(output)+"</td></tr>")
    fragment=FRAGMENT.read_text(encoding="utf-8")
    fragment=fragment.replace("{{TRACKED_COUNT}}",str(len(models))).replace("{{MODEL_ROWS}}","\n".join(rows))
    if "{{" in fragment: raise ValueError("Unresolved Cohere guide placeholder")
    page=page.replace('<section class="model-reference model-reference-deep shell">',fragment+'\n<section class="model-reference model-reference-deep shell" id="cohere-model-directory">',1)
    page=page.replace("</head>",'<link rel="stylesheet" href="/providers/cohere/reference.css" />\n</head>',1)
    safe_title,safe_desc=escape(TITLE,quote=True),escape(DESCRIPTION,quote=True)
    page=re.sub(r'<title>.*?</title>','<title>'+safe_title+'</title>',page,count=1,flags=re.S)
    page=re.sub(r'(<meta name="description" content=")[^"]*(")',lambda m:m[1]+safe_desc+m[2],page,count=1)
    for p,v in (("og:title",safe_title),("twitter:title",safe_title),("og:description",safe_desc),("twitter:description",safe_desc)):
        page=re.sub(r'(<meta (?:property|name)="'+re.escape(p)+r'" content=")[^"]*(")',lambda m:m[1]+v+m[2],page,count=1)
    page=page.replace("Verified model portfolio.</span>","Command, Embed, Rerank &amp; more.</span>",1)
    page=page.replace("calculator-priced</span>","tracked with verified provenance</span>",1)
    page=page.replace("<strong>0</strong><span>tracked with verified provenance</span>","<strong>"+str(len(models))+"</strong><span>model pages linked</span>",1)
    breadcrumb={"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},{"@type":"ListItem","position":2,"name":"Providers","item":"https://sxf.si/providers/"},{"@type":"ListItem","position":3,"name":"Cohere","item":URL}]}
    graph=[
        {"@type":"CollectionPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,"inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"},"about":{"@type":"Organization","name":"Cohere","url":"https://cohere.com/"},"breadcrumb":{"@id":URL+"#breadcrumb"},"mainEntity":{"@id":URL+"#model-list"}},
        {"@type":"ItemList","@id":URL+"#model-list","name":"Cohere AI models tracked by SXF","numberOfItems":len(models),"itemListElement":[{"@type":"ListItem","position":i+1,"name":m["model"],"url":"https://sxf.si"+m["sxf_url"]} for i,m in enumerate(models)]},
        {"@type":"TechArticle","@id":URL+"#guide","headline":"Cohere AI Models: Command, Embed, Rerank, Parse and North","url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},"description":DESCRIPTION,"dateModified":"2026-10-15","author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"citation":SOURCES,"inLanguage":"en"},
        breadcrumb,
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]},
    ]
    schema=json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False)
    page,count=re.subn(r'<script type="application/ld\+json">.*?</script>',lambda _: '<script type="application/ld+json">'+schema+'</script>',page,count=1,flags=re.S)
    if count!=1: raise ValueError("Missing Cohere provider JSON-LD")
    return page
