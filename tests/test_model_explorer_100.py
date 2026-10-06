#!/usr/bin/env python3
"""Stress the server-rendered Model Explorer contract with 100 synthetic models."""

from copy import deepcopy
from pathlib import Path
import importlib.util
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("update_news", SCRIPTS / "update_news.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

original = module.MODEL_PRICING_CATALOG
synthetic = deepcopy(original)
source_models = original["models"]
models = []
for index in range(100):
    model = deepcopy(source_models[index % len(source_models)])
    model["model_id"] = f"explorer-stress-{index:03d}"
    model["model"] = f"Explorer Stress {index:03d}"
    model["sxf_url"] = f"/models/explorer-stress-{index:03d}/"
    models.append(model)
synthetic["models"] = models

try:
    module.MODEL_PRICING_CATALOG = synthetic
    html = module.model_explorer_html()
finally:
    module.MODEL_PRICING_CATALOG = original

rows = re.findall(r'<tr data-model-row\s+data-model-id="([^"]+)"', html)
assert len(rows) == 100, f"Expected 100 Explorer rows, got {len(rows)}"
assert len(set(rows)) == 100, "Explorer stress rendering produced duplicate model IDs"
assert "100 models ·" in html, "Explorer verification badge must scale model count"
assert 'data-order="99"' in html, "Explorer must preserve deterministic catalog order through 100 rows"
assert 'id="modelExplorerCount">100 models shown' in html, "Server-rendered fallback must expose the full result count"

print("Model Explorer 100-model server rendering stress test passed")
