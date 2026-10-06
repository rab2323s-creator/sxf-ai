#!/usr/bin/env python3
"""Regression test for SXF catalog scale guards."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_catalog_scale.py"
spec = importlib.util.spec_from_file_location("validate_catalog_scale", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

metrics = module.validate_scale()
assert metrics["catalog_models"] >= 28
assert metrics["stress_models"] == 500
assert metrics["index_bytes_per_model"] <= module.MAX_INDEX_BYTES_PER_MODEL
assert metrics["stress_index_bytes"] <= module.MAX_INDEX_BYTES_AT_500

print(
    f"Scale guard regression OK: {metrics['catalog_models']} live models; "
    f"500-model stress index={metrics['stress_index_bytes']} bytes"
)
