"""Keep the evergreen intelligence-explosion guide present during scheduled site updates."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "guides/intelligence-explosion/index.html"
def render_intelligence_explosion_guide():
    html = PAGE.read_text(encoding="utf-8")
    for required in ("https://sxf.si/guides/intelligence-explosion/", "recursive-improvement-feedback-loop.svg", "FAQPage", "TechArticle"):
        if required not in html:
            raise RuntimeError("Intelligence-explosion guide missing: " + required)
    return html
