#!/usr/bin/env python3
"""Restore the Compare V2 enhancement layer after generated HTML refreshes.

scripts/update_news.py owns the generated comparison catalog and SEO markup.
This script owns only the Compare V2 progressive enhancement slots. Run it
immediately after each update_news.py call and before validation/deployment.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "compare" / "index.html"
CONTROL = '''
        <div class="compare-builder-presets" aria-label="Illustrative workload presets">
          <span>Example workloads</span>
          <button type="button" data-compare-preset="chat" aria-pressed="false">Customer support</button>
          <button type="button" data-compare-preset="coding" aria-pressed="false">Coding agent</button>
          <button type="button" data-compare-preset="research" aria-pressed="false">Long-form research</button>
          <small>Illustrative assumptions, not measured benchmarks.</small>
        </div>
'''
VOLUME = '''
        <div class="compare-builder-volume">
          <label for="compareMonthlyRequests">Monthly requests</label>
          <input id="compareMonthlyRequests" type="number" min="1" max="100000000" step="100" value="1000">
          <small>Estimates exclude taxes, tool calls and platform fees.</small>
        </div>
'''
COCKPIT = '''
        <section class="compare-decision-shell" aria-label="Decision assistant">
          <div class="compare-decision-toolbar">
            <label for="compareDecisionGoal">Your priority <select id="compareDecisionGoal"><option value="budget">Lowest direct cost</option><option value="coding">Coding &amp; agents</option><option value="research">Research &amp; science</option><option value="business">Business &amp; knowledge</option></select></label>
            <label class="compare-decision-check"><input type="checkbox" id="compareDecisionEvidenceOnly"> Only same-configuration evaluations</label>
            <button type="button" id="compareDecisionShare">Copy scenario link ↗</button>
            <span id="compareDecisionShareStatus" role="status"></span>
          </div>
          <div id="compareDecisionCockpit" class="compare-decision-cockpit" aria-live="polite"><p>Loading verified decision data…</p></div>
        </section>
'''
ERROR = '        <div id="compareBuilderError" class="compare-builder-error" role="alert" hidden></div>\n'
EVIDENCE = '        <section id="compareEvidence" class="compare-evidence" aria-live="polite"></section>\n'
REQUIRED = (
    'data-compare-builder',
    'id="compareModelA"',
    'id="compareModelB"',
    'id="compareBuilderResults"',
    'id="compareCuratedLink"',
    'id="compareBuilderError"',
    'id="compareEvidence"',
    'id="compareDecisionCockpit"',
    'id="compareDecisionGoal"',
    'id="compareDecisionEvidenceOnly"',
    'id="compareDecisionShare"',
    'id="compareMonthlyRequests"',
    'data-compare-preset="coding"',
    '/compare/compare-enhancements.css',
    '/compare/decision-engine.js',
    '/compare/decision-cockpit.js',
    '/compare/compare.js',
)

def before(html: str, identifier: str, anchor: str, insert: str) -> str:
    if identifier in html:
        return html
    if html.count(anchor) != 1:
        raise ValueError(f"Compare generator contract changed; missing/duplicated anchor: {anchor[:100]}")
    return html.replace(anchor, insert + anchor, 1)

def restore(html: str) -> str:
    if 'data-compare-builder' not in html:
        raise ValueError("Generated page lost the Compare builder entirely.")
    html = before(html, 'data-compare-preset="coding"',
                  '<div class="compare-builder-workload">', CONTROL,
                  )
    html = before(html, 'id="compareMonthlyRequests"',
                  '<div id="compareBuilderResults"', VOLUME)
    html = before(html, 'id="compareDecisionCockpit"',
                  '<div id="compareBuilderResults"', COCKPIT)
    html = before(html, 'id="compareBuilderError"',
                  '<div id="compareBuilderResults"', ERROR)
    html = before(html, 'id="compareEvidence"',
                  '<div id="compareCuratedLink"', EVIDENCE)
    script = '<script src="/compare/compare.js" defer></script>'
    html = before(html, '/compare/compare-enhancements.css',
                  script, '<link rel="stylesheet" href="/compare/compare-enhancements.css">')
    html = before(html, '/compare/decision-engine.js', script,
                  '<script src="/compare/decision-engine.js" defer></script>')
    html = before(html, '/compare/decision-cockpit.js', script,
                  '<script src="/compare/decision-cockpit.js" defer></script>')
    validate(html)
    return html

def validate(html: str) -> None:
    for marker in REQUIRED:
        if html.count(marker) != 1:
            raise ValueError(f"Compare V2 requires exactly one {marker!r}; found {html.count(marker)}")
    if html.index('/compare/decision-engine.js') > html.index('/compare/compare.js'):
        raise ValueError("Decision engine must load before compare.js.")
    for name in ("compare.js", "decision-engine.js", "decision-cockpit.js", "compare-enhancements.css"):
        if not (ROOT / "compare" / name).is_file():
            raise ValueError(f"Missing Compare V2 asset: {name}")

def main() -> None:
    source = PAGE.read_text(encoding="utf-8")
    if "--check" in sys.argv:
        validate(source)
        print("PASS: generated Compare V2 is complete")
        return
    output = restore(source)
    if output != source:
        PAGE.write_text(output, encoding="utf-8")
        print("Restored Compare V2 after page regeneration")
    else:
        print("Compare V2 already present; no changes")

if __name__ == "__main__":
    main()
