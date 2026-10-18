"""Render an evidence-backed reference guide to AI model benchmark methodology."""
import json
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"data/guide-content/ai-model-benchmarks-explained.html"
URL="https://sxf.si/guides/ai-model-benchmarks-explained/"
TITLE="AA Benchmarks Explained: AA-Briefcase, AA-LCR & AI Index | SXF"
HEADLINE="Artificial Analysis (AA) Benchmarks: AA-Briefcase, AA-LCR & AI Index"
DESCRIPTION="What are Artificial Analysis (AA) benchmarks? Compare AA-Briefcase v1.1, AA-LCR v1.1 and the Intelligence Index, including scoring methods and limitations."
IMAGES=[
URL+"images/intelligence-index-weights.svg",
URL+"images/benchmark-scoring-metrics.svg"
]
FAQ=[
("What is an AA benchmark?","In this context, AA stands for Artificial Analysis. An AA benchmark measures a specific AI model capability using a defined task set, evaluation setup and scoring method. AA-Briefcase assesses agentic knowledge work, AA-LCR tests long-context reasoning, and the Artificial Analysis Intelligence Index combines results from multiple evaluations. Their raw scores are not interchangeable."),
("What is the Artificial Analysis Intelligence Index?","It is a normalized weighted composite of ten evaluations covering agents, coding, general capability and scientific reasoning in version 4.3.2. It is not a direct Elo rating or percentage correct."),
("What does AA-Briefcase v1.1 measure?","AA-Briefcase v1.1 evaluates AI agent performance on professional knowledge-work deliverables using a combined evaluation framework and Elo-style relative comparisons."),
("What is the AA-LCR v1.1 benchmark?","AA-LCR v1.1 measures long-context reasoning over documents using Pass@1 accuracy on controlled questions with repeated measurements. It does not measure total usable context capacity alone."),
("What does GDPval-AA v2.1 measure?","GDPval-AA v2.1 assesses agentic occupational deliverables across 220 tasks using anchored Elo judgments. Its ratings are not equivalent to worker productivity percentages."),
("Can I compare Elo and accuracy percentages?","No. Elo is a relative comparison-based rating; accuracy is a fraction of correctly completed items. Their numbers cannot be compared or combined without a documented normalization framework."),
("Which AI benchmark should I trust?","Trust a benchmark only within the capability and conditions it actually tests. Review task design, model configuration, evaluator, reproducibility, uncertainty and relevance to your intended workload."),
("Does a top leaderboard position prove a model is best for business?","No. Business performance also depends on task fit, deployment security, reliability, latency, cost, review requirements and the quality of final outcomes on representative work."),
("How often should benchmark results be refreshed?","Recheck after model, tool, evaluation or scoring-method changes. Preserve the benchmark and model version alongside every historical score rather than overwriting unrelated snapshots.")
]
SOURCES=["https://artificialanalysis.ai/methodology/intelligence-benchmarking","https://artificialanalysis.ai/evaluations/aa-briefcase","https://artificialanalysis.ai/evaluations/aa-lcr","https://artificialanalysis.ai/methodology/gdpval-aa"]

def guide_html(shell):
    page_head=shell["page_head"]
    page_header=shell["page_header"]
    page_footer=shell["page_footer"]
    graph=[
        {"@type":"WebPage","@id":URL+"#webpage","url":URL,"name":TITLE,"description":DESCRIPTION,"inLanguage":"en","isPartOf":{"@id":"https://sxf.si/#website"},"mainEntity":{"@id":URL+"#article"},"breadcrumb":{"@id":URL+"#breadcrumb"}},
        {"@type":"TechArticle","@id":URL+"#article","url":URL,"mainEntityOfPage":{"@id":URL+"#webpage"},"headline":HEADLINE,"description":DESCRIPTION,"datePublished":"2026-10-15","dateModified":"2026-10-18","author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},"image":IMAGES,"articleSection":"AI Model Benchmark Research","citation":SOURCES,"inLanguage":"en","keywords":["aa benchmark","aa benchmarks","aa ai benchmark","Artificial Analysis benchmarks","aa-briefcase v1.1","aa-lcr v1.1","lcr benchmark","gdpval-aa v2.1","artificial analysis intelligence index"]},
        {"@type":"BreadcrumbList","@id":URL+"#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},{"@type":"ListItem","position":2,"name":"Guides","item":"https://sxf.si/guides/"},{"@type":"ListItem","position":3,"name":"AA Benchmarks Explained","item":URL}]},
        {"@type":"FAQPage","@id":URL+"#faq","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in FAQ]},
    ]
    schema={"@context":"https://schema.org","@graph":graph}
    head=page_head(TITLE,DESCRIPTION,URL,schema)
    head=head.replace("</head>",'<link rel="stylesheet" href="/guides/ai-model-benchmarks-explained/reference.css" />\n</head>')
    head=head.replace('<meta property="og:type" content="website"','<meta property="og:type" content="article"')
    # Use the single social image/card provided by page_head; do not append conflicting duplicates.
    content=CONTENT.read_text(encoding="utf-8")
    return f'''<!doctype html><html lang="en">{head}
<body class="intel-page guide-article-page">{page_header("guides")}<main><article>
<header class="guide-article-hero shell">
<nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>AI Model Benchmarks Explained</span></nav>
<p class="eyebrow">SXF GUIDES / BENCHMARK RESEARCH</p>
<h1>Artificial Analysis (AA) Benchmarks:<br><span>AA-Briefcase, AA-LCR &amp; AI Index</span></h1>
<p class="guide-deck">Artificial Analysis (AA) benchmarks measure different AI capabilities—not one universal score. Explore how AA-Briefcase v1.1, AA-LCR v1.1, GDPval-AA v2.1 and the Intelligence Index evaluate models, how their scoring methods differ, and what the results can actually tell you.</p>
<div class="guide-byline"><div><span>Reading time</span><strong>15 min</strong></div><div><span>Research standard</span><strong>Official source verification</strong></div></div>
</header>{content}</article></main>{page_footer()}</body></html>'''
