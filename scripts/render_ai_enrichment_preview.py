#!/usr/bin/env python3
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from ai_publish_quality import build_schema_plan, validate_publish_draft
from update_news import (
    BASE_URL,
    category_path,
    display_date,
    extract_models,
    item_topics,
    page_footer,
    page_head,
    page_header,
    related_items,
    signal_row,
    slugify,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "data" / "ai-enrichment-review.json"
CONFIG_PATH = ROOT / "data" / "ai-enrichment-config.json"
CANDIDATES_PATH = ROOT / "data" / "ai-enrichment-candidates.json"
ARCHIVE_PATH = ROOT / "data" / "archive.json"
PREVIEW_ROOT = ROOT / "preview" / "signals"

REVIEW_VERSION = "sxf-ai-enrichment-review-v1"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def citation_links(urls):
    return "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">Source {index} ↗</a>'
        for index, url in enumerate(urls, start=1)
    )


def review_schema(item, draft, schema_plan):
    canonical = item["signal_url"]
    faq = draft.get("faq") or []
    comparisons = draft.get("comparison_points") or []
    graph = [
        {
            "@type": "TechArticle",
            "@id": canonical + "#article",
            "headline": draft["h1"],
            "description": draft["meta_description"],
            "datePublished": item["published"],
            "mainEntityOfPage": canonical,
            "url": canonical,
            "articleSection": item["category"],
            "isPartOf": {"@id": "https://sxf.si/#website"},
            "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
            "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
            "citation": draft["sources"],
            "inLanguage": "en",
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Signals", "item": BASE_URL + "/signals/"},
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": item["category"],
                    "item": BASE_URL + category_path(item["category"]),
                },
                {
                    "@type": "ListItem",
                    "position": 4,
                    "name": draft["h1"],
                    "item": canonical,
                },
            ],
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": row["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": row["answer"]},
                }
                for row in faq
            ],
        },
    ]
    if "ItemList" in schema_plan["types"]:
        graph.append(
            {
                "@type": "ItemList",
                "name": f'{draft["h1"]} comparison',
                "numberOfItems": len(comparisons),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index,
                        "item": {
                            "@type": "Thing",
                            "name": row["dimension"],
                            "description": row["analysis"],
                        },
                    }
                    for index, row in enumerate(comparisons, start=1)
                ],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def list_cards(rows, text_key):
    return "".join(
        f'''<article class="research-card">
          <p>{escape(row[text_key])}</p>
          <div class="research-citations">{citation_links(row.get("source_urls") or [])}</div>
        </article>'''
        for row in rows
    )


def research_signal_preview_html(item, all_items, review, evidence):
    draft = review["draft"]
    quality_gate = load_json(CONFIG_PATH)["publish_quality_gate"]
    deterministic_errors = validate_publish_draft(draft, evidence, quality_gate)
    if deterministic_errors:
        raise RuntimeError(
            f'{review["signal_slug"]}: reviewed draft no longer passes publish quality gate: '
            + " | ".join(deterministic_errors)
        )

    schema_plan = build_schema_plan(draft, evidence)
    expected_types = review.get("schema_types") or []
    if schema_plan["types"] != expected_types:
        raise RuntimeError(
            f'{review["signal_slug"]}: schema plan drift: {schema_plan["types"]} != {expected_types}'
        )

    canonical = item["signal_url"]
    schema = review_schema(item, draft, schema_plan)
    related = "".join(signal_row(x) for x in related_items(item, all_items))
    topics = item_topics(item)
    models = extract_models(item["title"])
    topic_links = "".join(
        f'<a href="/topics/{escape(topic["slug"], quote=True)}/">{escape(topic["name"])}</a>'
        for topic in topics[:4]
    )
    model_links = "".join(
        f'<a href="/models/{escape(slugify(name), quote=True)}/">{escape(name)}</a>'
        for name in models[:4]
    )

    comparison_rows = "".join(
        f'''<tr>
          <th scope="row">{escape(row["dimension"])}</th>
          <td>{escape(row["analysis"])}</td>
          <td><div class="research-citations">{citation_links(row.get("source_urls") or [])}</div></td>
        </tr>'''
        for row in draft["comparison_points"]
    )

    faq_html = "".join(
        f'''<details>
          <summary>{escape(row["question"])}</summary>
          <p>{escape(row["answer"])}</p>
          <div class="research-citations">{citation_links(row.get("source_urls") or [])}</div>
        </details>'''
        for row in draft["faq"]
    )

    verify_html = "".join(f"<li>{escape(value)}</li>" for value in draft["what_to_verify"])
    source_html = "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(url)} <span>↗</span></a>'
        for url in draft["sources"]
    )

    return f'''<!doctype html><html lang="en">
    {page_head(
        draft["seo_title"] + " | SXF / AI",
        draft["meta_description"],
        canonical,
        schema,
        "article",
        "noindex,follow,noarchive",
    )}
    <body class="intel-page signal-page research-signal-page">
      <a class="skip-link" href="#signal-main">Skip to signal</a>
      <div class="ambient ambient-one" aria-hidden="true"></div><div class="ambient ambient-two" aria-hidden="true"></div>
      {page_header()}
      <div class="review-banner"><div class="shell"><strong>MANUAL REVIEW PREVIEW</strong><span>NOINDEX · NOT PUBLISHED · QUALITY {review["validator_quality_score"]}/100</span></div></div>
      <main id="signal-main">
        <section class="intel-hero shell research-hero">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/signals/">Signals</a><span>/</span><a href="{escape(category_path(item["category"]), quote=True)}">{escape(item["category"])}</a></nav>
          <div class="intel-kicker"><span class="pulse-dot"></span> RESEARCH SIGNAL / {escape(item["category"].upper())}</div>
          <h1>{escape(draft["h1"])}</h1>
          <p class="research-deck">{escape(draft["intro"])}</p>
          <div class="signal-meta-strip">
            <div><span>SOURCE</span><strong>{escape(item["source"])}</strong></div>
            <div><span>PUBLISHED</span><strong>{escape(display_date(item["published"]))}</strong></div>
            <div><span>QUALITY</span><strong>{review["validator_quality_score"]}/100</strong></div>
            <div><span>REVIEW</span><strong>Preview</strong></div>
          </div>
        </section>

        <section class="signal-layout shell">
          <article class="signal-brief">
            <p class="eyebrow">WHAT CHANGED</p>
            <p class="signal-summary">{escape(draft["what_changed"])}</p>
            <div class="signal-context"><span>WHY IT MATTERS</span><p>{escape(draft["why_it_matters"])}</p></div>
            <div class="signal-context"><span>PRICING / CAPABILITY IMPACT</span><p>{escape(draft["pricing_or_capability_impact"])}</p></div>
            <div class="signal-context"><span>WHO SHOULD CARE</span><p>{escape(draft["who_should_care"])}</p></div>
          </article>
          <aside class="source-card">
            <span class="source-card-label">SOURCE OF RECORD</span><strong>{escape(item["source"])}</strong>
            <p>This preview is grounded only in the approved evidence set and is not yet published as the canonical signal content.</p>
            <a href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">Open original source <b>↗</b></a>
          </aside>
        </section>

        <section class="research-section shell">
          <div class="intel-section-head"><div><p class="eyebrow">KEY FACTS</p><h2>The release, reduced to verified facts.</h2></div><span>{len(draft["key_facts"])} cited facts</span></div>
          <div class="research-grid">{list_cards(draft["key_facts"], "claim")}</div>
        </section>

        <section class="research-section shell">
          <div class="intel-section-head"><div><p class="eyebrow">COMPARISON</p><h2>Where Sol and Luna actually differ.</h2></div><span>{len(draft["comparison_points"])} comparison dimensions</span></div>
          <div class="model-comparison research-comparison"><div class="model-table-wrap"><table>
            <thead><tr><th>Dimension</th><th>Analysis</th><th>Evidence</th></tr></thead>
            <tbody>{comparison_rows}</tbody>
          </table></div></div>
        </section>

        <section class="research-section shell">
          <div class="research-two-up">
            <div>
              <div class="intel-section-head"><div><p class="eyebrow">TECHNICAL DETAILS</p><h2>Specs that change implementation.</h2></div></div>
              <div class="research-stack">{list_cards(draft["technical_details"], "detail")}</div>
            </div>
            <div>
              <div class="intel-section-head"><div><p class="eyebrow">PRACTICAL TAKEAWAYS</p><h2>What to do with the information.</h2></div></div>
              <div class="research-stack">{list_cards(draft["practical_takeaways"], "takeaway")}</div>
            </div>
          </div>
        </section>

        <section class="research-section shell research-verify">
          <div><p class="eyebrow">WHAT TO VERIFY</p><h2>Before production use.</h2></div>
          <ol>{verify_html}</ol>
        </section>

        <section class="research-section shell">
          <div class="research-two-up research-lower">
            <div class="model-faq">
              <div class="intel-section-head"><div><p class="eyebrow">FAQ</p><h2>Search questions, answered directly.</h2></div><span>{len(draft["faq"])} questions</span></div>
              {faq_html}
            </div>
            <div class="model-sources">
              <div class="intel-section-head"><div><p class="eyebrow">OFFICIAL SOURCES</p><h2>Evidence used on this page.</h2></div></div>
              {source_html}
            </div>
          </div>
        </section>

        <section class="signal-taxonomy shell">
          <div><span>TOPICS</span>{topic_links or '<small>No topic tag yet</small>'}</div>
          <div><span>MODELS</span>{model_links or '<small>No named model detected</small>'}</div>
        </section>

        <section class="related-signals shell">
          <div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Keep the context connected.</h2></div><a href="/signals/">All signals ↗</a></div>
          <div class="signal-list">{related}</div>
        </section>
      </main>
      {page_footer()}
    </body></html>'''


def main():
    review_payload = load_json(REVIEW_PATH)
    if review_payload.get("version") != REVIEW_VERSION:
        raise RuntimeError("AI enrichment review version drift")
    if review_payload.get("mode") != "manual-review":
        raise RuntimeError("AI enrichment review must remain manual-review")

    config = load_json(CONFIG_PATH)
    gate = config["publish_quality_gate"]
    candidates = load_json(CANDIDATES_PATH).get("candidates") or []
    archive = load_json(ARCHIVE_PATH)
    items = archive.get("items") or []

    candidate_by_slug = {row["signal_slug"]: row for row in candidates}
    item_by_slug = {row["signal_slug"]: row for row in items}

    rendered = 0
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)

    for review in review_payload.get("items") or []:
        slug = review.get("signal_slug")
        if review.get("review_status") != "preview":
            raise RuntimeError(f"{slug}: only preview review_status is allowed in v1")
        if review.get("approved_for_publish") is not False:
            raise RuntimeError(f"{slug}: approved_for_publish must remain false in preview v1")
        if review.get("index_decision") != "noindex":
            raise RuntimeError(f"{slug}: preview index_decision must be noindex")
        if int(review.get("validator_quality_score", 0)) < int(gate["minimum_ai_quality_score"]):
            raise RuntimeError(f"{slug}: validator quality score below publish gate")

        candidate = candidate_by_slug.get(slug)
        item = item_by_slug.get(slug)
        if candidate is None or item is None:
            raise RuntimeError(f"{slug}: review target missing from current candidate/archive data")
        if review.get("signal_url") != item.get("signal_url"):
            raise RuntimeError(f"{slug}: signal URL drift")
        if review.get("evidence_hash") != candidate.get("evidence_hash"):
            raise RuntimeError(f"{slug}: evidence hash changed; regenerate and review before rendering")

        deterministic_errors = validate_publish_draft(review["draft"], candidate["evidence"], gate)
        if deterministic_errors:
            raise RuntimeError(f"{slug}: reviewed draft failed deterministic gate: {' | '.join(deterministic_errors)}")

        preview_slug = review["draft"]["seo_slug_recommendation"]
        out_dir = PREVIEW_ROOT / preview_slug
        out_dir.mkdir(parents=True, exist_ok=True)
        html = research_signal_preview_html(item, items, review, candidate["evidence"])
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        rendered += 1

    print(f"AI enrichment review previews rendered: {rendered}")


if __name__ == "__main__":
    main()
