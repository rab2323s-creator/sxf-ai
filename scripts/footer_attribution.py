"""Normalize project-attribution links inside already-rendered SXF footers.

Runs after the publishing generator. Leaves article body, metadata, structured
data, the homepage's external credit and About's project attribution untouched.
"""
from __future__ import annotations

import re
from pathlib import Path

FOOTER = re.compile(r'(<footer class="footer shell">)(.*?)(</footer>)', re.S)
VMC_URL = 'https://vivamediacreative.com/labs/'
VIVA_URL = 'https://vivamediacreative.com/'
NAV_VMC = f'<a href="{VMC_URL}">VMC Labs <span>↗</span></a>'
NAV_VIVA = f'<a href="{VIVA_URL}">Viva Media Creative <span>↗</span></a>'
EXTERNAL_CREDIT = f'Developed within <a href="{VMC_URL}">VMC Labs</a>'
INTERNAL_CREDIT = 'Developed within <a href="/about/#origin-title">VMC Labs</a>'


def normalize_footer_attribution(root: Path) -> int:
    modified = 0
    for path in root.rglob('*.html'):
        if '.git' in path.parts or path.parts[-2:] == ('tests', 'index.html'):
            continue
        original = path.read_text(encoding='utf-8')
        if '<footer class="footer shell">' not in original:
            continue
        is_home = path == root / 'index.html'

        def rewrite(match: re.Match[str]) -> str:
            footer = match.group(2)
            # Existing variants may have shorter footers; preserve them.
            if 'class="footer-nav"' not in footer:
                return match.group(0)
            footer = footer.replace(NAV_VMC, '').replace(NAV_VIVA, '')
            if is_home:
                footer = footer.replace(INTERNAL_CREDIT, EXTERNAL_CREDIT)
            else:
                footer = footer.replace(EXTERNAL_CREDIT, INTERNAL_CREDIT)
            if 'href="' + VMC_URL not in footer and is_home:
                raise ValueError('Homepage must retain its VMC Labs credit')
            if not is_home and ('href="' + VMC_URL in footer or 'href="' + VIVA_URL in footer):
                raise ValueError(f'Unexpected external attribution in footer: {path}')
            return match.group(1) + footer + match.group(3)

        updated, count = FOOTER.subn(rewrite, original)
        if count != 1:
            raise ValueError(f'Expected one footer in {path}, found {count}')
        if updated != original:
            path.write_text(updated, encoding='utf-8')
            modified += 1
    return modified


if __name__ == '__main__':
    print(f'Normalized footers: {normalize_footer_attribution(Path(__file__).resolve().parents[1])}')
