#!/usr/bin/env python3
"""SXF manual SKILL.md evaluator. No external packages, models, or network."""
import csv
import sys

def flag(value):
    v = (value or "").strip().lower()
    if v in ("true", "yes", "1"): return True
    if v in ("false", "no", "0"): return False
    if not v: return None
    raise ValueError("Use true, false or blank for observed_trigger")

def main(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("CSV must have unique, non-empty case IDs")
    tp=tn=fp=fn=missing=0
    for row in rows:
        expected=flag(row["expected_trigger"])
        observed=flag(row["observed_trigger"])
        if expected is None: raise ValueError("Missing expected label: "+row["id"])
        if observed is None: missing+=1; continue
        if expected and observed: tp+=1
        elif not expected and not observed: tn+=1
        elif not expected and observed: fp+=1
        else: fn+=1
    pct=lambda n,d: f"{100*n/d:.1f}%" if d else "N/A"
    print(f"Measured {len(rows)-missing}/{len(rows)} cases (not a vendor benchmark)")
    print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
    print("Precision="+pct(tp,tp+fp)+" Recall="+pct(tp,tp+fn)+" Accuracy="+pct(tp+tn,tp+fp+tn+fn))
    if missing: print("INCOMPLETE: run your actual agent and record observations.")
    print("Labels are manual observations, not instrumented by this script.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "eval-cases.csv"))
