#!/usr/bin/env python3
"""Report catalog coverage from the canonical SXF model sources.

This is intentionally descriptive rather than opinionated: it derives only
capabilities that are explicitly represented in the catalog. Editorial
recommendations belong in the expansion plan, not in generated metrics.
"""

from collections import defaultdict
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_model_catalog.py"

spec = importlib.util.spec_from_file_location("build_model_catalog", BUILDER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def has_av(model):
    inputs = {str(x).lower() for x in model.get("modalities", {}).get("input", [])}
    return bool(inputs & {"audio", "video"})


def is_open_weight(model):
    return "open-weight" in model.get("positioning", "").lower()


def main():
    catalog = module.build_catalog()
    providers = defaultdict(list)
    for model in catalog["models"]:
        providers[model["provider"]].append(model)

    headers = [
        "Provider", "Models", "Reasoning", "Image", "A/V",
        ">=1M ctx", "Official paid", "Open-weight"
    ]
    print(" | ".join(headers))
    print(" | ".join(["---"] * len(headers)))

    for provider in sorted(providers):
        models = providers[provider]
        values = [
            provider,
            str(len(models)),
            str(sum(bool(m.get("reasoning")) for m in models)),
            str(sum("image" in {str(x).lower() for x in m.get("modalities", {}).get("input", [])} for m in models)),
            str(sum(has_av(m) for m in models)),
            str(sum(int(m.get("context_window") or 0) >= 1_000_000 for m in models)),
            str(sum(m.get("pricing_status") == "official-paid" for m in models)),
            str(sum(is_open_weight(m) for m in models)),
        ]
        print(" | ".join(values))

    models = catalog["models"]
    print()
    print(f"Total models: {len(models)}")
    print(f"Providers: {len(providers)}")
    print(f"Reasoning: {sum(bool(m.get('reasoning')) for m in models)}")
    print(f"Audio/video input: {sum(has_av(m) for m in models)}")
    print(f">=1M context: {sum(int(m.get('context_window') or 0) >= 1_000_000 for m in models)}")
    print(f"Official paid API: {sum(m.get('pricing_status') == 'official-paid' for m in models)}")
    print(f"Open-weight: {sum(is_open_weight(m) for m in models)}")


if __name__ == "__main__":
    main()
