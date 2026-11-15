"""Reviewed, source-backed Signal briefs with deterministic rendering."""
from __future__ import annotations
import json
from html import escape
from pathlib import Path
from urllib.parse import urlparse

DATA = json.loads((Path(__file__).resolve().parents[1] / "data" / "signal-editorial-reviews.json").read_text(encoding="utf-8"))
REVIEWS = DATA["items"]


def get_review(item):
    return REVIEWS.get(item.get("signal_slug", ""))


def render_review_evidence(review):
    if not review:
        return ""
    cards = []
    for entry in review["evidence"]:
        url = entry["source"]
        assert urlparse(url).scheme == "https"
        cards.append('<div><strong>' + escape(entry["label"]) + '</strong><p>'
                     + escape(entry["fact"]) + ' <a href="' + escape(url, quote=True)
                     + '" target="_blank" rel="noopener noreferrer">Primary evidence ↗</a></p></div>')
    return ('<section class="signal-deep-dive shell signal-evidence" aria-labelledby="signal-evidence-title">'
            '<div class="intel-section-head"><div><p class="eyebrow">PRIMARY-SOURCE FACTS</p>'
            '<h2 id="signal-evidence-title">What the evidence establishes.</h2></div>'
            '<span>Reviewed ' + escape(review["reviewed_at"]) + '</span></div>'
            '<div class="deep-dive-facts">' + "".join(cards) + '</div>'
            '<div class="deep-dive-section" style="margin-top:24px"><p class="eyebrow">LIMITATIONS</p>'
            '<p>' + escape(review["limitations"]) + '</p></div></section>')


def render_review_analysis(review):
    """Render source-grounded editorial analysis only for reviews with an analysis section."""
    if not review or not review.get("analysis"):
        return ""
    sections = []
    for i, section in enumerate(review["analysis"], 1):
        heading = escape(section["heading"])
        def link_paragraph(paragraph):
            rendered = escape(paragraph)
            for link in section.get("inline_links", []):
                label = escape(link["text"])
                href = link["url"]
                if not href.startswith("/") or href.startswith("//") or '"' in href:
                    raise ValueError("Invalid SXF inline link")
                if label in rendered:
                    rendered = rendered.replace(label, '<a href="' + escape(href, quote=True) + '">' + label + '</a>', 1)
            return "<p>" + rendered + "</p>"
        paragraphs = "".join(link_paragraph(paragraph) for paragraph in section["paragraphs"])
        source = escape(section["source"], quote=True)
        sections.append(
            '<article class="deep-dive-section">'
            + '<p class="eyebrow">TECHNICAL ANALYSIS / ' + str(i).zfill(2) + '</p>'
            + '<h2>' + heading + '</h2>' + paragraphs
            + '<p><a href="' + source
            + '" target="_blank" rel="noopener noreferrer">Check primary-source evidence ↗</a></p>'
            + '</article>'
        )
    return (
        '<section class="signal-deep-dive shell signal-editorial-analysis" aria-labelledby="signal-technical-analysis-title">'
        '<div class="intel-section-head"><div><p class="eyebrow">SXF RESEARCH EXPLAINER</p>'
        '<h2 id="signal-technical-analysis-title">What the technical evidence means.</h2></div>'
        '<span>Source-grounded analysis</span></div>'
        + "".join(sections)
        + '</section>'
    )

def render_review_reader_tools(review):
    """Render reviewed, reader-facing action checks and verified internal routes."""
    if not review:
        return ""
    checklist = review.get("reader_checklist", [])
    links = review.get("internal_links", [])
    if not checklist and not links:
        return ""
    from urllib.parse import urlparse
    checks_html = "".join(
        '<li>' + escape(value) + '</li>'
        for value in checklist if isinstance(value, str) and value.strip()
    )
    links_html = ""
    for link in links:
        path = link.get("url", "")
        parsed = urlparse(path)
        # Site-relative, same-origin links only; prevent unsafe protocols.
        if not path.startswith("/") or path.startswith("//") or parsed.scheme or parsed.netloc:
            raise ValueError("Reviewed internal link must stay on the SXF domain")
        links_html += ('<li><a href="' + escape(path, quote=True) + '">'
                       + escape(link["title"]) + '</a><p>'
                       + escape(link.get("description", "")) + '</p></li>')
    return (
        '<section class="signal-deep-dive shell signal-reader-tools" '
        'aria-labelledby="signal-reader-tools-title">'
        '<div class="intel-section-head"><div><p class="eyebrow">PRACTICAL TAKEAWAYS</p>'
        '<h2 id="signal-reader-tools-title">What readers can check next.</h2>'
        '</div></div>'
        + ('<div class="deep-dive-section"><h3>Verification checklist</h3><ol>'
           + checks_html + '</ol></div>' if checks_html else '')
        + ('<div class="deep-dive-section"><h3>Read the related SXF guides</h3><ul>'
           + links_html + '</ul></div>' if links_html else '')
        + '</section>'
    )

def render_review_special(review):
    """Article-specific reported facts, methodology tables and human-readable FAQ.

    Optional fields are authored in the editorial data. No FAQ structured-data
    markup is emitted because snippets are not promised by Google.
    """
    if not review:
        return ""
    feature = review.get("sxf_feature")
    parts = []
    if feature:
        source = feature["source"]
        if not (source.startswith("https://") and source in review["sources"]):
            raise ValueError("Feature must cite a listed primary source")
        if feature["type"] == "matrix":
            headings = "".join("<th scope='col'>" + escape(cell) + "</th>" for cell in feature["columns"])
            rows = "".join("<tr>" + "".join(("<th scope='row'>" if i == 0 else "<td>") +
                escape(str(cell)) + ("</th>" if i == 0 else "</td>") for i, cell in enumerate(row))
                + "</tr>" for row in feature["rows"])
            display = '<div class="deep-dive-table-wrap" tabindex="0" role="region" aria-label="' + escape(feature["heading"], quote=True) + '"><table class="deep-dive-table"><thead><tr>' + headings + '</tr></thead><tbody>' + rows + '</tbody></table></div>'
        elif feature["type"] == "steps":
            display = '<ol class="deep-dive-checklist">' + "".join("<li><strong>" +
                escape(row["label"]) + "</strong> " + escape(row["detail"]) + "</li>"
                for row in feature["steps"]) + "</ol>"
        elif feature["type"] == "cards":
            display = '<div class="deep-dive-facts">' + "".join("<div><strong>" +
                escape(row["label"]) + "</strong><p>" + escape(row["detail"]) +
                "</p></div>" for row in feature["cards"]) + "</div>"
        else:
            raise ValueError("Unknown review feature type")
        parts.append('<section class="signal-deep-dive shell signal-research-feature" aria-label="Independent article context"><div class="deep-dive-section"><p class="eyebrow">' +
                     escape(feature["eyebrow"]) + '</p><h2>' + escape(feature["heading"]) +
                     '</h2><p>' + escape(feature["intro"]) + '</p>' + display + '<p>' +
                     escape(feature["note"]) + ' <a href="' + escape(source, quote=True) +
                     '" target="_blank" rel="noopener noreferrer">Check the original evidence ↗</a></p></div></section>')
    if review.get("faq"):
        faq = "".join("<details><summary>" + escape(x["question"]) + "</summary><p>" +
                      escape(x["answer"]) + "</p></details>" for x in review["faq"])
        parts.append('<section class="signal-deep-dive shell signal-reader-faq"><div class="deep-dive-section deep-dive-faq"><p class="eyebrow">READER QUESTIONS</p><h2>' +
                     escape(review["faq_heading"]) + '</h2>' + faq + '</div></section>')
    return "".join(parts)
