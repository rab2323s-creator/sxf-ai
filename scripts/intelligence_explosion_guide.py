"""Regenerate the evergreen guide from canonical body content and checked-in page shell."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "guides/intelligence-explosion/index.html"
BODY = ROOT / "data/guide-content/intelligence-explosion.html"
START = "<!-- intelligence-explosion:body-start -->"
END = "<!-- intelligence-explosion:body-end -->"


def render_intelligence_explosion_guide():
    shell = PAGE.read_text(encoding="utf-8")
    content = BODY.read_text(encoding="utf-8")
    if shell.count(START) != 1 or shell.count(END) != 1:
        raise RuntimeError("Guide shell content markers are missing or duplicated")
    before, remainder = shell.split(START, 1)
    _previous_content, after = remainder.split(END, 1)
    rendered = before + START + content + END + after
    for required in ("https://sxf.si/guides/intelligence-explosion/",
                     "recursive-improvement-feedback-loop.svg",
                     "hard-vs-soft-ai-takeoff.svg", "FAQPage", "\"@type\":\"Article\""):
        if required not in rendered:
            raise RuntimeError("Intelligence-explosion guide missing: " + required)
    if content.count("<details>") != 10:
        raise RuntimeError("Guide must contain exactly ten visible FAQ entries")
    return rendered
