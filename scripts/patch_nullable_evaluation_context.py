#!/usr/bin/env python3
"""Safely format unpublished model context limits in legacy generated pages.

The generator currently repeats model["context_window"] in multiple templates.
Replace formatting expressions with an explicit "Not published" fallback and
numeric data attributes with "unknown". Never invent a numeric value.
"""
from pathlib import Path
import re

path = Path(__file__).resolve().parent / "update_news.py"
source = path.read_text(encoding="utf-8")
formatted = re.compile(r"""\{\s*int\(model\[["']context_window["']\]\):,\}""")
plain = re.compile(r"""\{\s*int\(model\[["']context_window["']\]\)\}""")
safe_formatted = """{"Not published" if model.get("context_window") is None else format(int(model["context_window"]), ",")}"""
safe_plain = """{"unknown" if model.get("context_window") is None else int(model["context_window"])}"""
n_formatted = len(formatted.findall(source))
n_plain = len(plain.findall(source))
if n_formatted == n_plain == 0 and safe_formatted in source and safe_plain in source:
    print("PASS: context limit fallback already installed")
elif n_formatted >= 1 and n_plain >= 1:
    updated = formatted.sub(lambda _: safe_formatted, source)
    updated = plain.sub(lambda _: safe_plain, updated)
    path.write_text(updated, encoding="utf-8")
    print(f"PASS: safely patched {n_formatted} formatted and {n_plain} raw context fields")
else:
    raise SystemExit(f"FAIL: generator template contract changed: {n_formatted} formatted, {n_plain} raw occurrences")
