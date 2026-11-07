#!/usr/bin/env python3
"""SXF offline OCR quality scorer (no external API or network calls).

JSONL fields:
id, group, reference, hypothesis,
expected_fields (object), predicted_fields (object)

Normalized character error rate and exact critical-field matching are
illustrative metrics; a rigorous deployment should add table-cell structure,
confidence calibration, layout matching, language-specific normalization and
human consensus. The bundled fixtures are synthetic, NOT Mistral results.
"""
from __future__ import annotations

import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        row = [i]
        for j, y in enumerate(b, 1):
            row.append(min(row[-1] + 1, prev[j] + 1,
                           prev[j - 1] + int(x != y)))
        prev = row
    return prev[-1]


def score_rows(path: Path) -> dict:
    stats = defaultdict(lambda: {
        "documents": 0, "character_edits": 0, "reference_characters": 0,
        "field_matches": 0, "field_total": 0,
    })
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for key in ("id", "group", "reference", "hypothesis"):
            if not isinstance(row.get(key), str):
                raise ValueError(f"line {line_number}: missing string {key}")
        fields = row.get("expected_fields", {})
        guesses = row.get("predicted_fields", {})
        if not isinstance(fields, dict) or not isinstance(guesses, dict):
            raise ValueError(f"line {line_number}: expected_fields/predicted_fields must be objects")
        ref, hyp = normalize(row["reference"]), normalize(row["hypothesis"])
        bucket = stats[row["group"]]
        bucket["documents"] += 1
        bucket["character_edits"] += edit_distance(ref, hyp)
        bucket["reference_characters"] += len(ref)
        for field, value in fields.items():
            bucket["field_total"] += 1
            bucket["field_matches"] += int(guesses.get(field) == value)

    if not stats:
        raise ValueError("Empty dataset")
    groups = {}
    for group, values in sorted(stats.items()):
        groups[group] = {
            **values,
            "cer": values["character_edits"] / values["reference_characters"]
            if values["reference_characters"] else None,
            "critical_field_exact_match": values["field_matches"] / values["field_total"]
            if values["field_total"] else None,
        }
    total = {key: sum(x[key] for x in stats.values()) for key in (
        "documents", "character_edits", "reference_characters", "field_matches", "field_total"
    )}
    return {
        "dataset": str(path),
        "total": {
            **total,
            "cer": total["character_edits"] / total["reference_characters"]
            if total["reference_characters"] else None,
            "critical_field_exact_match": total["field_matches"] / total["field_total"]
            if total["field_total"] else None,
        },
        "by_group": groups,
        "disclosure": "Synthetic example strings; no Mistral OCR benchmark or API call was run.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python sxf-ocr-eval.py /path/to/your-results.jsonl")
    print(json.dumps(score_rows(Path(sys.argv[1])), ensure_ascii=False, indent=2))
