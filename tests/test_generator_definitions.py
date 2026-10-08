#!/usr/bin/env python3
"""Guard the generated site source against accidental duplicate function definitions."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "update_news.py"

def main():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE))
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    duplicates = sorted(k for k, count in Counter(names).items() if count > 1)
    assert not duplicates, f"Duplicate top-level functions: {duplicates}"
    required = {
        "gemini_37_flash_reference_html",
        "gpt_61_sol_reference_html",
        "grok_46_reference_html",
        "grok_47_reference_html",
        "render_catalog_model_page",
        "provider_page_html",
        "benchmark_page_html",
        "update_sitemap",
        "main",
    }
    assert required.issubset(names), f"Missing specialist renderer(s): {sorted(required - set(names))}"
    print(f"PASS: {len(names)} unique top-level functions, required renderers retained")

if __name__ == "__main__":
    main()
