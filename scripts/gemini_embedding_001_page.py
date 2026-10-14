"""Persistent, source-backed SEO enhancement for Gemini Embedding 001."""
import json
import re
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRAGMENT=ROOT/"data/model-page-content/gemini-embedding-001-seo.html"
URL="https://sxf.si/models/gemini-embedding-001/"
TITLE="Gemini Embedding 001: Pricing, API, Dimensions & RAG | SXF / AI"
DESCRIPTION="Gemini Embedding 001 guide: $0.15/1M pricing, 2,048-token input limit, 768 vs 3072 dimensions, Python API, task types, RAG and Gemini Embedding 2 comparison."

def enrich_gemini_embedding_001(page,model):
    if page.count("</main>") != 1:
        raise ValueError("Gemini Embedding 001 page expected exactly one main")
    if abs(float(model["pricing"]["standard"][-1]["input"])-0.15)>0.0000001:
        raise ValueError("Embedding pricing reference changed; review editorial costs")
    if int(model["context_window"])!=2048:
        raise ValueError("Embedding context changed; review editorial limits")
    fragment=FRAGMENT.read_text(encoding="utf-8")
    if fragment.count('data-ge001-editorial=')!=1:
        raise ValueError("Gemini Embedding editorial missing or duplicate")
    page=page.replace("</main>",fragment+"\n</main>",1)
    page=page.replace("</head>",'<link rel="stylesheet" href="/models/gemini-embedding-001/reference.css" />\n</head>',1)
    page=page.replace("</body>",'<script defer src="/models/gemini-embedding-001/reference.js"></script>\n</body>',1)
    st,sd=escape(TITLE,quote=True),escape(DESCRIPTION,quote=True)
    page=re.sub(r'<title>.*?</title>','<title>'+st+'</title>',page,count=1,flags=re.S)
    page=re.sub(r'(<meta name="description" content=")[^"]*(")',lambda m:m[1]+sd+m[2],page,count=1)
    for prop,value in (("og:title",st),("twitter:title",st),("og:description",sd),("twitter:description",sd)):
        page=re.sub(r'(<meta (?:property|name)="'+re.escape(prop)+r'" content=")[^"]*(")',lambda m:m[1]+value+m[2],page,count=1)
    page=page.replace("verified model reference.</span>","pricing, vectors &amp; Python API.</span>",1)
    faq_pairs=[
        ("What is Gemini Embedding 001 used for?","Gemini Embedding 001 converts text into numerical vectors for semantic search, RAG document retrieval, clustering, classification and similarity. It does not generate conversational text."),
        ("How much does Gemini Embedding 001 cost?","Google lists $0.15 per million input text tokens on the paid Standard Gemini API tier and $0.075 per million on Batch. An eligible free tier also exists. These are embedding input charges, not generative output-token charges."),
        ("Is Gemini Embedding 001 free?","Google lists a free Gemini API tier for this model, subject to limits and data-use terms. Production paid usage is charged by input tokens. Check the official pricing page for your account and serving route."),
        ("What is the maximum Gemini Embedding 001 input size?","Google documents a limit of 2,048 input tokens per text. Chunk longer documents before embedding them and preserve metadata to reconnect retrieved results with the source."),
        ("How many dimensions does Gemini Embedding 001 return?","The default embedding vector has 3,072 dimensions. Google recommends evaluating 768, 1,536 or 3,072 dimensions depending on the desired storage and retrieval-quality trade-off."),
        ("Does Gemini Embedding 001 support images or video?","No. Gemini Embedding 001 is text-only. Google's newer Gemini Embedding 2 supports embedding text, images, video, audio and PDFs in a unified multimodal vector space."),
        ("How do I use Gemini Embedding 001 in Python?","Install the google-genai SDK, provide GEMINI_API_KEY, then call client.models.embed_content with model gemini-embedding-001 and an optional EmbedContentConfig specifying task_type and output_dimensionality."),
        ("Which task types should I use for RAG search?","Use RETRIEVAL_DOCUMENT when indexing source passages and RETRIEVAL_QUERY for the user's search text. Embed both sides with the same model and dimensionality and evaluate ranking quality."),
        ("Do I need to normalize 768-dimensional Gemini Embedding 001 vectors?","Yes. Google recommends manual normalization for Embedding 001 vectors truncated below the default 3,072 dimensions before cosine or dot-product comparisons. Gemini Embedding 2 automatically normalizes shortened vectors."),
        ("Can I mix Gemini Embedding 001 and Gemini Embedding 2 vectors?","No. Google states their embedding spaces are incompatible. Migrating requires re-embedding the stored corpus and query vectors and validating a separate index."),
        ("What is the difference between embedding and text-generation models?","An embedding model returns a fixed-length vector representing text meaning, useful for search and similarity. A generative Gemini model produces text or other content; RAG commonly combines vector retrieval with a separate generator."),
    ]
    sources=["https://ai.google.dev/gemini-api/docs/models/gemini-embedding-001","https://ai.google.dev/gemini-api/docs/embeddings","https://ai.google.dev/gemini-api/docs/pricing","https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2"]
    graph=[
        {"@type":"WebPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,"inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"},"mainEntity":{"@id":URL+"#article"},"breadcrumb":{"@id":URL+"#breadcrumb"}},
        {"@type":"TechArticle","@id":URL+"#article","headline":TITLE.split(" | ")[0],"description":DESCRIPTION,"url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},"dateModified":"2026-10-14","author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"about":{"@type":"Thing","name":"Gemini Embedding 001","sameAs":sources[0]},"citation":sources,"inLanguage":"en"},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},{"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},{"@type":"ListItem","position":3,"name":"Gemini Embedding 001","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_pairs]}
    ]
    schema=json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False)
    page,count=re.subn(r'<script type="application/ld\+json">.*?</script>',lambda m:'<script type="application/ld+json">'+schema+'</script>',page,count=1,flags=re.S)
    if count!=1:
        raise ValueError("Missing Gemini Embedding JSON-LD")
    return page
