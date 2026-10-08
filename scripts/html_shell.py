"""Reusable pure HTML builders for SXF navigation, footer and SEO head.

These functions intentionally preserve the existing output contract byte for byte.
Filesystem normalization and site orchestration remain in update_news.py.
"""
from __future__ import annotations

import json
from html import escape


def page_header(active=""):
    links = [
        ("/models/", "Models", "models"),
        ("/compare/", "Compare", "compare"),
        ("/tools/", "Tools", "tools"),
        ("/research/", "Research", "research"),
        ("/open-source/", "Open Source", "open-source"),
        ("/guides/", "Guides", "guides"),
        ("/superintelligence/", "Superintelligence", "superintelligence"),
        ("/brief/", "Brief", "brief"),
        ("/about/", "About", "about"),
    ]
    nav_parts = []
    for href, label, key in links:
        current = ' aria-current="page"' if key == active else ""
        nav_parts.append(f'<a href="{href}"{current}>{label}</a>')
    nav = "".join(nav_parts)
    return f'''<header class="site-header"><div class="header-inner">
      <a class="brand" href="/" aria-label="SXF AI home"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
      <nav class="top-nav" aria-label="Primary navigation">{nav}</nav>
      <div class="header-status"><span class="pulse-dot"></span>LIVE</div>
    </div></header>'''


def page_footer():
    return '''<footer class="footer shell">
      <div class="footer-main">
        <div class="footer-identity">
          <a class="brand footer-brand" href="/" aria-label="SXF AI home"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
          <p class="footer-statement">AI intelligence,<br><span>mapped in motion.</span></p>
          <p class="footer-description">Primary-source signals, model intelligence, expert guides and research context — organized for fast understanding.</p>
          <a class="footer-contact" href="mailto:info@sxf.si" aria-label="Email SXF at info@sxf.si"><span class="footer-contact-dot" aria-hidden="true"></span><span class="footer-contact-label">CONTACT</span><strong>info@sxf.si</strong><b aria-hidden="true">↗</b></a>
        </div>
        <nav class="footer-nav" aria-label="Footer navigation">
          <div class="footer-nav-group"><p>INTELLIGENCE</p><a href="/models/">Models <span>↗</span></a><a href="/models/pricing/">Model Pricing <span>↗</span></a><a href="/signals/">Signals <span>↗</span></a><a href="/topics/">Topics <span>↗</span></a><a href="/research/">Research <span>↗</span></a></div>
          <div class="footer-nav-group"><p>EXPLORE</p><a href="/compare/">Compare Models <span>↗</span></a><a href="/guides/">Guides <span>↗</span></a><a href="/superintelligence/">Superintelligence <span>↗</span></a><a href="/open-source/">Open Source <span>↗</span></a><a href="/brief/">SXF Brief <span>↗</span></a></div>
          <div class="footer-nav-group"><p>SXF</p><a href="/about/">About & Method <span>↗</span></a><a href="mailto:info@sxf.si">Contact <span>↗</span></a><a href="https://vivamediacreative.com/labs/">VMC Labs <span>↗</span></a><a href="https://vivamediacreative.com/">Viva Media Creative <span>↗</span></a></div>
        </nav>
      </div>
      <div class="footer-bottom"><span>© <span id="year"></span> SXF / AI</span><span>Curated AI intelligence · Built for signal.</span><span>Developed within <a href="https://vivamediacreative.com/labs/">VMC Labs</a></span></div>
    </footer><script>document.getElementById("year").textContent=new Date().getFullYear();</script>'''


def page_head(title, description, canonical, schema, page_type="website", robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"):
    safe_description = escape(description[:180], quote=True)
    if page_type == "article":
        social_image_meta = '<meta name="twitter:card" content="summary" />'
    else:
        social_image_meta = '''<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:alt" content="SXF / AI — The AI Signals Hub" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />
      <meta name="twitter:image:alt" content="SXF / AI — The AI Signals Hub" />'''
    return f'''<head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="dark" />
      <title>{escape(title)}</title>
      <meta name="description" content="{safe_description}" />
      <meta name="robots" content="{escape(robots, quote=True)}" />
      <meta name="googlebot" content="{escape(robots, quote=True)}" />
      <meta name="theme-color" content="#07090d" />
      <link rel="canonical" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="en" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="x-default" href="{escape(canonical, quote=True)}" />
      <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      <meta property="og:type" content="{escape(page_type, quote=True)}" />
      <meta property="og:site_name" content="SXF / AI" />
      <meta property="og:title" content="{escape(title, quote=True)}" />
      <meta property="og:description" content="{safe_description}" />
      <meta property="og:url" content="{escape(canonical, quote=True)}" />
      {social_image_meta}
      <meta name="twitter:title" content="{escape(title, quote=True)}" />
      <meta name="twitter:description" content="{safe_description}" />
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")}</script>
      <link rel="stylesheet" href="/styles.css" />
      <link rel="stylesheet" href="/intelligence.css" />
    </head>'''
