#!/usr/bin/env python3
"""Offline assertions for the registered SXF two-arm API research procedure."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / "guides/why-does-chatgpt-make-things-up/research/model-eval/questions.json"
SCRIPT = ROOT / "scripts/run_hallucination_model_eval.py"
README = Q.parent / "README.md"
PAGE = ROOT / "guides/why-does-chatgpt-make-things-up/index.html"

def main():
    rows = json.loads(Q.read_text(encoding="utf-8"))
    cases = rows["cases"]
    assert rows["status"] == "PREREGISTERED_NOT_RUN"
    assert len(cases) == 12 and len({x["id"] for x in cases}) == 12
    assert rows["arms"] == ["no_web", "with_web"]
    assert all(x["primary_url"].startswith("https://") for x in cases)
    assert all(x["question"] and x["expected"] and x["reviewer_note"] for x in cases)
    script = SCRIPT.read_text(encoding="utf-8")
    ast.parse(script)
    for required in ('"store": False', '"tool_choice"] = "required"', 'OPENAI_API_KEY',
                     'web_search_call', 'response_file', 'not_reviewed',
                     'captured_pending_human_review', 'failed_or_partial_no_valid_conclusions',
                     'preregistered_questions_sha256', 'if dry_run:',
                     '--acknowledge-api-costs'):
        assert required in script, required
    assert "NOT RUN" in README.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    assert "prospective" in page.lower() and "no model responses" in page.lower()
    assert "model-eval/questions.json" in page
    assert "model-eval/README.md" in page
    print("PASS: 12 fixed questions, two-arm model controls, raw capture, human-review gate and honest article labeling")

if __name__ == "__main__":
    main()
