#!/usr/bin/env python3
"""Guard against automated feed rebuilds silently removing original SXF Agent Lab evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
guide = (ROOT / "guides/best-ai-agents/index.html").read_text(encoding="utf-8")
lab = (ROOT / "research/ai-agent-hands-on-2026-11/index.html").read_text(encoding="utf-8")
source = (ROOT / "data/guide-content/ai-agent-lab-section.html").read_text(encoding="utf-8")
generator = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")

assert 'id="sxf-hands-on-tests"' in source
assert 'lab_section_html' in generator
assert guide.count('id="sxf-hands-on-tests"') == 1, "Missing or duplicate study section"
assert guide.count('href="#sxf-hands-on-tests"') == 1, "Study missing from navigation"
assert '/research/ai-agent-hands-on-2026-11/' in guide
assert 'November 3, 2026' in guide
assert 'Claude Cowork' in source and 'Manus Lite' in source
assert 'research/ai-agent-hands-on-2026-11/' in lab
assert 'no overall winner' in source.lower()
print("PASS: SXF Agent Lab section persists in generated guide")
