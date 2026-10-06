#!/usr/bin/env python3
"""Regression tests for generalized pricing meters."""

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_model_catalog.py"

spec = importlib.util.spec_from_file_location("build_model_catalog", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

page_model = {
    "pricing_status": "official-paid",
    "calculator_eligible": False,
    "pricing_basis": {
        "meter": "pages",
        "quantity": 1,
        "dimensions": ["page"],
        "display_unit": "per page",
    },
    "pricing": {
        "standard": [
            {
                "start": "2026-01-01",
                "end": None,
                "rates": {"page": 0.002},
            }
        ]
    },
}

module.validate_pricing(page_model, "Test/PageModel")

bad_page_model = {
    **page_model,
    "pricing": {
        "standard": [
            {
                "start": "2026-01-01",
                "end": None,
                "input": 1.0,
                "output": 2.0,
            }
        ]
    },
}

try:
    module.validate_pricing(bad_page_model, "Test/BadPageModel")
except module.CatalogError:
    pass
else:
    raise AssertionError("Non-token pricing must reject token input/output fields")

token_model = {
    "pricing_status": "official-paid",
    "calculator_eligible": True,
    "pricing_basis": {
        "meter": "tokens",
        "quantity": 1_000_000,
        "dimensions": ["input", "cached_input", "output"],
        "display_unit": "per 1 million tokens",
    },
    "pricing": {
        "standard": [
            {
                "start": "2026-01-01",
                "end": None,
                "input": 0.3,
                "output": 2.5,
            }
        ]
    },
}

module.validate_pricing(token_model, "Test/TokenModel")


embedding_model = {
    "pricing_status": "official-paid",
    "calculator_eligible": False,
    "pricing_basis": {
        "meter": "tokens",
        "quantity": 1_000_000,
        "dimensions": ["input", "cached_input"],
        "display_unit": "per 1 million tokens",
    },
    "pricing": {
        "standard": [
            {
                "start": "2026-01-01",
                "end": None,
                "input": 0.15,
                "cached_input": 0.015,
            }
        ]
    },
}

module.validate_pricing(embedding_model, "Test/EmbeddingModel")

bad_embedding_calculator = {
    **embedding_model,
    "calculator_eligible": True,
}

try:
    module.validate_pricing(bad_embedding_calculator, "Test/BadEmbeddingCalculator")
except module.CatalogError:
    pass
else:
    raise AssertionError("Input-only token pricing must not become calculator eligible")

print("Generalized pricing meter tests passed")
