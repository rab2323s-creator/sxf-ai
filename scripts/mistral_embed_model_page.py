"""Durable source-grounded Mistral Embed page SEO enrichment.

The catalog retains ownership of official pricing, primary model identity and
append-only history. Regenerated HTML receives the authored research layer.
"""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"data/model-page-content/mistral-embed-seo.html"
URL="https://sxf.si/models/mistral-embed/"
TITLE="Mistral Embed: API Pricing, 1024 Dimensions & RAG | SXF"
DESCRIPTION=("Mistral Embed guide: $0.10/1M tokens, 8K context, 1024-dimension "
             "vectors, Python API, cosine similarity, RAG costs and SXF embedding calculator.")
SOURCES=[
    "https://docs.mistral.ai/models/mistral-embed-23-12",
    "https://docs.mistral.ai/studio/search/search-toolkit/concepts/embedding-model",
    "https://docs.mistral.ai/inference/embeddings/text_embeddings",
    "https://docs.mistral.ai/api/endpoint/embeddings",
    "https://docs.mistral.ai/inference/quickstarts/create-embeddings",
    "https://docs.mistral.ai/inference/embeddings/code_embeddings",
    "https://docs.mistral.ai/models/codestral-embed-25-05",
    "https://docs.mistral.ai/inference/embeddings",
]
FAQ=[
    ("What is the Mistral Embed model ID?",
     "The versioned model card is mistral-embed-2312, while Mistral's Python and REST API examples use mistral-embed."),
    ("What is the price of Mistral Embed?",
     "The Standard rate is $0.10 per million input tokens, with no separately published text-generation output rate. Vector storage and RAG answer generation are additional costs."),
    ("How many dimensions does Mistral Embed produce?",
     "Mistral's Search Toolkit documents a 1024-dimension cosine-distance configuration for mistral-embed. Check response array length on your endpoint before creating an index."),
    ("What is the Mistral Embed context limit?",
     "The official Mistral Embed model card lists an 8000-token input context. Split longer documents into chunks."),
    ("Can Mistral Embed generate chat answers?",
     "No. It produces numerical embeddings from input text. Use a separate language model for generation."),
    ("Is Mistral Embed open source?",
     "The cited release is a hosted Premier embedding API, not a downloadable open-weights release."),
    ("How does Mistral Embed compare with Codestral Embed?",
     "Mistral Embed targets general text, while Codestral Embed targets code retrieval and has distinct dimensions, features and pricing. Evaluate quality on your data."),
    ("Can Mistral Embed be used with a vector database?",
     "Yes. Store the vectors with the correct dimensions, distance function, IDs and access permissions; use the same compatible embedding model for queries and documents."),
]
CAVEATS='<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'

def once(page:str,old:str,new:str,label:str)->str:
    n=page.count(old)
    if n!=1: raise ValueError(f"Mistral Embed {label}: expected one occurrence, got {n}")
    return page.replace(old,new,1)

def meta(page:str,key:str,value:str)->str:
    kind="property" if key.startswith("og:") else "name"
    pattern=r'(<meta '+kind+r'="'+re.escape(key)+r'" content=")[^"]*(")'
    updated,n=re.subn(pattern,lambda m:m.group(1)+escape(value,quote=True)+m.group(2),page,count=1)
    if n!=1: raise ValueError(f"Missing {key}")
    return updated

def enrich_mistral_embed_page(page:str)->str:
    if page.count('rel="canonical" href="'+URL+'"')!=1:
        raise ValueError("Mistral Embed unexpected canonical URL")
    editorial=CONTENT.read_text(encoding="utf-8").strip()
    if editorial.count("data-membed-guide")!=1 or editorial.count('id="membed-faq"')!=1:
        raise ValueError("Original research source missing")
    page=once(page,"<title>Mistral Embed — API Specs, Context &amp; Pricing | SXF / AI</title>",
              "<title>"+escape(TITLE)+"</title>","SEO title")
    for key,value in (("description",DESCRIPTION),("og:title",TITLE),("og:description",DESCRIPTION),
                      ("twitter:title",TITLE),("twitter:description",DESCRIPTION)):
        page=meta(page,key,value)
    page=once(page,'<h1>Mistral Embed<br><span>verified model reference.</span></h1>',
              '<h1>Mistral Embed<br><span>API, $0.10 pricing, 1024-d RAG vectors.</span></h1>',"H1")
    page=once(page,
              '<p>Mistral GA text embedding model for retrieval, semantic search, clustering, classification, and similarity workflows.</p>',
              '<p>Mistral Embed API for semantic search and RAG: 8K context, 1024-d vectors, $0.10/1M tokens, Python, cosine similarity and original SXF cost analysis.</p>',
              "hero")
    page=once(page,'<div><strong>Not published</strong><span>max output</span></div>',
              '<div><strong>1,024</strong><span>Search Toolkit vector dimensions</span></div>',"hero vector size")
    page=once(page,'<div><span>MAX OUTPUT</span><strong>Not published</strong></div>',
              '<div><span>OUTPUT</span><strong>Embedding vectors</strong><small>not generated chat tokens</small></div>',"output")
    page=once(page,'<div><span>KNOWLEDGE CUTOFF</span><strong>Not published</strong></div>',
              '<div><span>MODEL STATUS</span><strong>GA Premier</strong><small>hosted embedding API</small></div>',"model status")
    page=once(page,
              '<article><span>REASONING</span><h3>Not published</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
              '<article><span>VECTOR MODEL</span><h3>1024-d cosine retrieval</h3><p>Generates numerical embeddings rather than text or reasoning. Mistral documents 1,024-d cosine vectors for its Mistral Embed Search Toolkit preset.</p></article>',
              "non-chat model")
    page=once(page,
              '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
              '<p>Mistral Embed charges $0.10 per million input tokens, not output tokens. SXF keeps it outside the generative token calculator and provides a specialist embedding, reindexing and vector-storage estimator below.</p>',
              "pricing explanation")
    page=once(page,CAVEATS,editorial+"\n\n        "+CAVEATS,"editorial insertion")
    page=once(page,"</head>",'<link rel="stylesheet" href="/assets/mistral-embed-guide.css" />\n    </head>',"CSS")
    page=once(page,"</body>",'<script src="/assets/mistral-embed-cost.js" defer></script>\n    </body>',"calculator")
    m=re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)',page,re.S)
    if not m: raise ValueError("Structured data missing")
    schema=json.loads(m.group(2))
    article=next((x for x in schema["@graph"] if x.get("@type")=="TechArticle"),None)
    if not article: raise ValueError("TechArticle missing")
    article.update({
      "headline":TITLE.removesuffix(" | SXF"),"description":DESCRIPTION,
      "dateModified":"2026-11-08","citation":SOURCES,
      "mainEntityOfPage":{"@type":"WebPage","@id":URL},
      "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
      "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
      "keywords":["Mistral Embed","mistral-embed","mistral-embed-2312",
                  "Mistral Embed pricing","Mistral Embed dimensions",
                  "Mistral Embed Python API","Mistral embedding 1024",
                  "Mistral Embed vector database","Mistral Embed RAG"],
    })
    schema["@graph"].append({
      "@type":"FAQPage","@id":URL+"#faq","url":URL+"#membed-faq",
      "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}
                    for q,a in FAQ],
    })
    return page[:m.start(2)]+json.dumps(schema,ensure_ascii=False,separators=(",",":"))+page[m.end(2):]
