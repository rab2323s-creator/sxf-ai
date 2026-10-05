#!/usr/bin/env python3
"""Print objective SXF catalog coverage quality metrics."""

from collections import Counter
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_model_catalog.py"

spec = importlib.util.spec_from_file_location("build_model_catalog", BUILDER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inputs(model):
    return {str(x).lower() for x in model.get("modalities", {}).get("input", [])}


def inferred_open_weight(model):
    haystack = " ".join([
        str(model.get("positioning", "")),
        *[str(x) for x in model.get("notes", [])],
    ]).lower()
    return "open-weight" in haystack or "open weights" in haystack or model.get("provider") == "Meta"


def main():
    catalog = module.build_catalog()
    models = catalog["models"]
    providers = Counter(m["provider"] for m in models)

    metrics = {
        "models": len(models),
        "providers": len(providers),
        "reasoning": sum(bool(m.get("reasoning")) for m in models),
        "image": sum("image" in inputs(m) for m in models),
        "video": sum("video" in inputs(m) for m in models),
        "audio": sum("audio" in inputs(m) for m in models),
        "context_1m_plus": sum(int(m.get("context_window") or 0) >= 1_000_000 for m in models),
        "official_paid": sum(m.get("pricing_status") == "official-paid" for m in models),
        "calculator_eligible": sum(m.get("calculator_eligible") is True for m in models),
        "open_weight_inferred": sum(inferred_open_weight(m) for m in models),
    }

    print("SXF catalog coverage quality")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print("\nProvider distribution:")
    for provider, count in providers.most_common():
        print(f"{provider}: {count}")

    top_three = sum(count for _, count in providers.most_common(3))
    print(f"\nTop-3 provider concentration: {top_three}/{len(models)} ({top_three / len(models):.1%})")
    print("Open-weight is currently inferred from editorial data; migrate to structured access fields before further scale.")


if __name__ == "__main__":
    main()
