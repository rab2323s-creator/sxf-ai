#!/usr/bin/env python3
"""Regression tests for the model identity registry."""

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_model_identity.py"
spec = importlib.util.spec_from_file_location("validate_model_identity", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

registry = json.loads((ROOT / "data/model-identity/registry.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
entries = module.validate_registry(registry, catalog)

assert len(entries) == len(catalog["models"]) == 28
assert set(entries) == {m["model_id"] for m in catalog["models"]}
assert all(entry["provider_native_ids"] for entry in entries.values())
assert all(entry["identity_sources"] for entry in entries.values())

resolved = module.resolve_identity(registry, "OpenAI", "gpt-5.6", "GPT-5.6 Sol")
assert resolved["status"] == "alias" and resolved["matched_model_id"] == "gpt-5.6-sol"
resolved = module.resolve_identity(registry, "Mistral AI", None, "Codestral")
assert resolved["status"] == "possible_duplicate" and resolved["possible_duplicates"] == ["codestral-2508"]
resolved = module.resolve_identity(registry, "Example Provider", "example-native-id", "Example Model")
assert resolved["status"] == "new"

bad = copy.deepcopy(registry)
bad["models"][1]["aliases"].append(bad["models"][0]["provider_native_ids"][0])
try:
    module.validate_registry(bad, catalog)
except module.IdentityError:
    pass
else:
    raise AssertionError("Provider-scoped alias/native-ID collision must fail")

bad = copy.deepcopy(registry)
a, b = bad["models"][0], bad["models"][1]
a["successor"] = b["canonical_model_id"]
b["predecessor"] = a["canonical_model_id"]
b["successor"] = a["canonical_model_id"]
a["predecessor"] = b["canonical_model_id"]
try:
    module.validate_registry(bad, catalog)
except module.IdentityError:
    pass
else:
    raise AssertionError("Identity relationship cycles must fail")

print(f"Identity registry regression tests OK: {len(entries)} models")
