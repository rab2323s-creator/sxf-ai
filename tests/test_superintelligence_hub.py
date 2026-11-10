#!/usr/bin/env python3
"""Guard the generated AGI-versus-ASI comparison against automated overwrites."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "superintelligence/index.html").read_text(encoding="utf-8")
source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
css = (ROOT / "intelligence.css").read_text(encoding="utf-8")
section = html.split('<section class="si-continuum shell">', 1)[1].split('</section>', 1)[0]
assert section.index('class="si-continuum-grid"') < section.index('class="si-compare"') < section.index('class="guide-callout"')
assert section.count('<tr><th scope="row">') == 4 and section.count('<th scope="col">') == 3
assert section.count('data-label="AGI"') == 4 and section.count('data-label="ASI"') == 4
assert 'role="region" aria-label="AGI versus ASI comparison"' in section
assert source.count('<h3 id="agi-vs-asi">AGI vs ASI:') == 1
assert 'stacked cards on phones' in css and 'content:attr(data-label)' in css
print("PASS: persistent responsive AGI vs ASI comparison")
