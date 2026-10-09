#!/usr/bin/env python3
"""Verify intentional contextual links to the enterprise economics study."""
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
TARGET = "/guides/ai-agent-cost/"
ARTICLES = {
    "guides/what-is-agentic-ai/index.html": "use-cases",
    "guides/best-ai-agents/index.html": "pricing",
    "guides/how-to-build-ai-super-agent/index.html": "cost",
    "guides/ai-agent-security/index.html": "human-approval",
    "guides/ai-negotiation-agents/index.html": "measurement",
}

class LinkAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.section_stack = []
        self.matches = []
        self.heading_link_count = 0
        self.paragraph_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section":
            self.section_stack.append(a.get("id"))
        if tag == "p":
            self.paragraph_depth += 1
        if tag == "a" and a.get("href") == TARGET:
            self.matches.append({
                "section": self.section_stack[-1] if self.section_stack else None,
                "in_paragraph": self.paragraph_depth > 0,
            })

    def handle_endtag(self, tag):
        if tag == "section" and self.section_stack:
            self.section_stack.pop()
        if tag == "p" and self.paragraph_depth:
            self.paragraph_depth -= 1

def main():
    assert (ROOT / TARGET.strip("/") / "index.html").is_file(), "Study destination missing"
    for article, section in ARTICLES.items():
        page = (ROOT / article).read_text(encoding="utf-8")
        audit = LinkAudit()
        audit.feed(page)
        assert audit.matches == [{"section": section, "in_paragraph": True}], (
            f"{article}: expected one in-context paragraph link inside #{section}, got {audit.matches}"
        )
        print("PASS contextual link:", article, "section:", section)
    gen = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert gen.count('href="/guides/ai-agent-cost/"') == 1, "Unexpected generated guide reference count"
    assert "A plan price alone cannot show whether deployment pays off." in gen
    assert (ROOT / "guides/best-ai-agents/index.html").read_text().count(TARGET) == 1
    print("PASS generator parity: best AI agents link is permanent")

if __name__ == "__main__":
    main()
