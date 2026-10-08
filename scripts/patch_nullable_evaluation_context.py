#!/usr/bin/env python3
"""Handle absent context limits in the legacy generated evaluation explorer.

The source template lives in an oversized generator module. Match the exact
Python formatting expression with or without string-literal escaped quotes.
Only replace that one expression, fail closed on source drift, and never invent
missing numeric context-window data.
"""
from pathlib import Path
import re

path = Path(__file__).resolve().parent / "update_news.py"
source = path.read_text(encoding="utf-8")
replacement = """{'Not published' if model.get('context_window') is None else format(int(model['context_window']), ',')}"""
pattern = re.compile(r"""\{\s*int\(\s*model\[\s*\\?['"]context_window\\?['"]\s*\]\s*\)\s*:\s*,\s*\}""")

if source.count(replacement) == 1:
    print("PASS: evaluation explorer handles unpublished context window (already patched)")
else:
    updated, count = pattern.subn(lambda match: replacement, source)
    if count != 1:
        candidates = [(number, line.strip()[:220]) for number, line in enumerate(source.splitlines(), 1)
                      if "context_window" in line and "int(" in line]
        raise SystemExit("FAIL: expected one context-window format expression; "
                         f"found {count}. Candidate source lines: {candidates[:10]}")
    path.write_text(updated, encoding="utf-8")
    print("PASS: evaluation explorer handles unpublished context window")
