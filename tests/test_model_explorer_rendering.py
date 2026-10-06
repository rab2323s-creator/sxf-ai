#!/usr/bin/env python3
"""Regression coverage for model Explorer HTML rendering."""

from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("update_news", SCRIPTS / "update_news.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = (SCRIPTS / "update_news.py").read_text(encoding="utf-8")
start = source.rfind("def model_explorer_html():")
end = source.find("\ndef ", start + 1)
renderer_source = source[start:] if end == -1 else source[start:end]
assert 'price["cached_input"]' not in renderer_source, "Explorer rendering must not require cached_input"
html = module.model_explorer_html()
assert 'data-model-id="amazon.nova-2-lite-v1:0"' in html, "Explorer rows must expose canonical model IDs"

assert "Amazon Nova 2 Lite" in html, "Explorer must render Nova 2 Lite"
assert 'amazon.nova-2-lite-v1:0' in html, "Explorer must retain the provider-native Nova model ID"

nova_start = html.index("Amazon Nova 2 Lite")
nova_fragment = html[nova_start:nova_start + 1800]
assert '<td class="model-price">—</td>' in nova_fragment, (
    "Models without cached-input pricing must render an em dash instead of raising"
)

pricing_html = module.model_pricing_page_html()
assert "Amazon Nova 2 Lite" in pricing_html, "Pricing page must render Nova 2 Lite"
nova_pricing_start = pricing_html.index("Amazon Nova 2 Lite")
nova_pricing_fragment = pricing_html[nova_pricing_start:nova_pricing_start + 2200]
assert "—" in nova_pricing_fragment, (
    "Pricing page must tolerate models without cached-input pricing"
)

explorer_js = (ROOT / "models" / "explorer.js").read_text(encoding="utf-8")
assert 'fetch("/data/model-index.json"' in explorer_js, "Explorer must load the lightweight model index"
assert 'fetch("/data/model-pricing.json"' not in explorer_js, "Explorer must not load the full pricing catalog"

print("Model Explorer and pricing rendering regression tests passed")
