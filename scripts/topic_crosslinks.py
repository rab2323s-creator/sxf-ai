"""Curated context links from published Guide and Research pages to topic hubs."""
from __future__ import annotations
from html import escape
from pathlib import Path

TOPIC_NAMES = {"ai-agents":"AI Agents","coding-ai":"Coding AI","ai-security":"AI Security","ai-safety":"AI Safety"}
CONTEXT_ROUTES = {
    "guides/ai-agent-evaluation-checklist/index.html": (
        "Move from the evaluation checklist to the wider agent ecosystem and its security controls.",
        ("ai-agents", "ai-security")),
    "guides/ai-agent-frameworks-comparison/index.html": (
        "Explore AI agent systems beyond individual frameworks.", ("ai-agents",)),
    "guides/ai-agent-use-cases/index.html": (
        "Continue from use cases to the wider AI agent landscape.", ("ai-agents",)),
    "guides/model-context-protocol-mcp/index.html": (
        "Connect MCP architecture with agent workflows and security controls.",
        ("ai-agents", "ai-security")),
    "research/ai-agent-reliability/index.html": (
        "Explore agent systems alongside safety and evaluation research.",
        ("ai-agents", "ai-safety")),
    "research/ai-agent-memory/index.html": (
        "Explore AI agents beyond memory, including deployment security.",
        ("ai-agents", "ai-security")),
    "research/ai-coding-agent-architecture/index.html": (
        "Follow coding AI systems and the wider agent landscape.",
        ("coding-ai", "ai-agents")),
}
MARKER = 'data-topic-context="v1"'
SCRIPT = '<script src="/assets/topic-navigation.js" defer></script>'

def context_markup(description: str, slugs: tuple[str, ...]) -> str:
    links = "".join(
        f'<a href="/topics/{escape(slug, quote=True)}/"><span>{escape(TOPIC_NAMES[slug])} topic hub</span><span aria-hidden="true">↗</span></a>'
        for slug in slugs)
    return (
        f'<nav class="topic-context-block shell" aria-label="Explore related AI topics" {MARKER}>'
        '<span class="topic-context-label">EXPLORE THE WIDER SUBJECT</span>'
        '<h2 class="topic-context-heading">Continue by topic</h2>'
        f'<p class="topic-context-explain">{escape(description)}</p>'
        f'<div class="topic-context-links">{links}</div></nav>')

def enrich_topic_context(html: str, description: str, slugs: tuple[str, ...]) -> str:
    if MARKER not in html:
        if "</main>" not in html:
            raise ValueError("Missing closing main for Topics context")
        html = html.replace("</main>", context_markup(description, slugs) + "</main>", 1)
    if SCRIPT not in html:
        if "</body>" not in html:
            raise ValueError("Missing closing body for Topics events")
        html = html.replace("</body>", SCRIPT + "</body>", 1)
    return html

def apply_topic_crosslinks(root: Path) -> None:
    for route, (description, slugs) in CONTEXT_ROUTES.items():
        path = root / route
        if not path.is_file():
            raise FileNotFoundError(f"Topic context target is missing: {route}")
        before = path.read_text(encoding="utf-8")
        after = enrich_topic_context(before, description, slugs)
        if after != before:
            path.write_text(after, encoding="utf-8")
