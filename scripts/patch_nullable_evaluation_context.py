#!/usr/bin/env python3
"""Make the generated evaluation explorer tolerant of unpublished context windows.

The legacy monolithic page renderer formats a nullable context_window as an
integer. This compatibility shim is applied to the local build checkout before
running update_news.py. It is strict/idempotent and never changes catalog data.
TODO: fold this fix directly into update_news.py once it is split into modules.
"""
from pathlib import Path

path = Path(__file__).resolve().parent / "update_news.py"
source = path.read_text(encoding="utf-8")
before = '{int(model["context_window"]):,}'
after = '{"Not published" if model["context_window"] is None else format(int(model["context_window"]), ",")}'
if source.count(after) == 1:
    print("PASS: nullable context window fix already present")
elif source.count(before) == 1:
    path.write_text(source.replace(before, after, 1), encoding="utf-8")
    print("PASS: generated explorer now handles unpublished context windows")
else:
    raise SystemExit("FAIL: renderer context-window expression changed; review required")
