#!/usr/bin/env python3
"""SXF offline word/character error-rate scorer for transcription experiments.

Run:
  python sxf-stt-score.py sxf-stt-example.jsonl
  python sxf-stt-score.py private-results.jsonl --by-language

Expected JSONL fields: id, language, condition, reference, hypothesis.
No network/API calls. The bundled example is synthetic, not Voxtral output.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Simple reproducible Unicode-aware normalization, not universal WER."""
    text = unicodedata.normalize("NFKC", text).casefold()
    # Keep Unicode letters and numbers; replace punctuation with spaces.
    text = "".join(ch if unicodedata.category(ch)[0] in {"L", "N"} else " " for ch in text)
    return " ".join(text.split())


def edits(reference: list[str], hypothesis: list[str]) -> int:
    """Levenshtein distance using O(min(n, m)) memory."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for i, a in enumerate(reference, 1):
        current = [i]
        for j, b in enumerate(hypothesis, 1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (a != b),
            ))
        previous = current
    return previous[-1]


def score(reference: str, hypothesis: str) -> dict:
    ref = normalize(reference)
    hyp = normalize(hypothesis)
    ref_words, hyp_words = ref.split(), hyp.split()
    ref_chars, hyp_chars = list(ref.replace(" ", "")), list(hyp.replace(" ", ""))
    return {
        "word_edits": edits(ref_words, hyp_words),
        "reference_words": len(ref_words),
        "character_edits": edits(ref_chars, hyp_chars),
        "reference_characters": len(ref_chars),
    }


def percentage(errors: int, reference_count: int):
    return None if reference_count == 0 else 100.0 * errors / reference_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute reproducible WER/CER on user-supplied transcripts")
    parser.add_argument("jsonl", type=Path, help="JSON Lines containing reference and hypothesis text")
    parser.add_argument("--by-language", action="store_true", help="Also aggregate by dataset language")
    args = parser.parse_args()
    groups: dict[str, dict[str, int]] = {}
    totals = {"word_edits": 0, "reference_words": 0, "character_edits": 0, "reference_characters": 0}
    count = 0

    with args.jsonl.open(encoding="utf-8") as input_file:
        for lineno, line in enumerate(input_file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row.get("reference"), str) or not isinstance(row.get("hypothesis"), str):
                raise ValueError(f"line {lineno}: reference and hypothesis must be strings")
            result = score(row["reference"], row["hypothesis"])
            lang = str(row.get("language", "unspecified"))
            for key, value in result.items():
                totals[key] += value
            group = groups.setdefault(lang, {k: 0 for k in totals})
            for key, value in result.items():
                group[key] += value
            count += 1
    if not count:
        parser.error("JSONL must contain at least one transcript pair")

    def format_result(result):
        return {
            "wer_percent": percentage(result["word_edits"], result["reference_words"]),
            "cer_percent": percentage(result["character_edits"], result["reference_characters"]),
            **result,
        }

    summary = {"dataset": str(args.jsonl), "clips": count, "total": format_result(totals)}
    if args.by_language:
        summary["by_language"] = {lang: format_result(values) for lang, values in sorted(groups.items())}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
