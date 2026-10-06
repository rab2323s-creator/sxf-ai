#!/usr/bin/env python3
"""CI scale guards for SXF model catalog growth."""

from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAX_INDEX_BYTES_PER_MODEL = 1100
MAX_INDEX_BYTES_AT_500 = 550_000
TARGET_STRESS_MODELS = 500


class ScaleGuardError(ValueError):
    pass


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compact_bytes(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def load_index_builder():
    path = ROOT / "scripts" / "build_model_index.py"
    spec = importlib.util.spec_from_file_location("build_model_index", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_catalog(catalog: dict, count: int) -> dict:
    source = catalog["models"]
    if not source:
        raise ScaleGuardError("Catalog must contain at least one model for stress generation")
    cloned = deepcopy(catalog)
    cloned["models"] = []
    for index in range(count):
        model = deepcopy(source[index % len(source)])
        model["model_id"] = f"scale-test-{index:04d}"
        model["model"] = f"Scale Test Model {index:04d}"
        model["sxf_url"] = f"/models/scale-test-{index:04d}/"
        cloned["models"].append(model)
    return cloned


def validate_scale() -> dict:
    catalog = load_json(ROOT / "data" / "model-pricing.json")
    index = load_json(ROOT / "data" / "model-index.json")
    registry = load_json(ROOT / "data" / "model-identity" / "registry.json")
    reverification = load_json(ROOT / "data" / "model-reverification.json")

    catalog_ids = [model["model_id"] for model in catalog["models"]]
    index_ids = [model["model_id"] for model in index["models"]]
    registry_ids = [model["canonical_model_id"] for model in registry["models"]]
    freshness_ids = [item["model_id"] for item in reverification["items"]]

    if catalog_ids != index_ids:
        raise ScaleGuardError("Index order/coverage drift from canonical catalog")
    if set(catalog_ids) != set(registry_ids):
        raise ScaleGuardError("Identity registry coverage drift from canonical catalog")
    if set(catalog_ids) != set(freshness_ids):
        raise ScaleGuardError("Reverification queue coverage drift from canonical catalog")

    index_size = compact_bytes(index)
    per_model = index_size / max(1, len(index_ids))
    if per_model > MAX_INDEX_BYTES_PER_MODEL:
        raise ScaleGuardError(
            f"Lightweight index budget exceeded: {per_model:.1f} bytes/model > {MAX_INDEX_BYTES_PER_MODEL}"
        )

    builder = load_index_builder()
    stress_catalog = synthetic_catalog(catalog, TARGET_STRESS_MODELS)
    stress_index = builder.build_index(stress_catalog)
    stress_size = compact_bytes(stress_index)
    if stress_index["model_count"] != TARGET_STRESS_MODELS:
        raise ScaleGuardError("500-model stress index lost records")
    if len({m["model_id"] for m in stress_index["models"]}) != TARGET_STRESS_MODELS:
        raise ScaleGuardError("500-model stress index produced duplicate IDs")
    if stress_size > MAX_INDEX_BYTES_AT_500:
        raise ScaleGuardError(
            f"500-model index payload exceeds budget: {stress_size} > {MAX_INDEX_BYTES_AT_500}"
        )

    return {
        "catalog_models": len(catalog_ids),
        "index_bytes": index_size,
        "index_bytes_per_model": round(per_model, 1),
        "stress_models": TARGET_STRESS_MODELS,
        "stress_index_bytes": stress_size,
    }


def main() -> int:
    try:
        metrics = validate_scale()
        print("SXF scale guards OK")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        return 0
    except (ScaleGuardError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"scale guard error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
