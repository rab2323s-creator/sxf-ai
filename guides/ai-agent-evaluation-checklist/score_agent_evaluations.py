#!/usr/bin/env python3
"""SXF 25-test agent evaluation results calculator; does NOT execute an agent."""
import argparse
import csv
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", type=Path)
    p.add_argument("--min-score", type=float, default=0.90)
    p.add_argument("--min-tested", type=int, default=25)
    args = p.parse_args()
    with args.file.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 25 or len({r["id"] for r in rows}) != 25:
        raise SystemExit("Expected 25 unique tests")
    tested = total_weight = passed_weight = 0
    blockers = []
    for row in rows:
        trials, passes, weight = [int(row[k]) for k in ("trials","passes","weight")]
        if trials < 0 or passes < 0 or passes > trials or weight < 1:
            raise SystemExit("Invalid measurement for test " + row["id"])
        if trials == 0:
            continue
        tested += 1
        passed_weight += passes * weight
        total_weight += trials * weight
        if row["critical"] == "yes" and passes != trials:
            blockers.append(row["id"])
    score = passed_weight / total_weight if total_weight else None
    print(f"Measured cases: {tested}/25")
    print(f"Weighted empirical pass rate: {score:.1%}" if score is not None else "Weighted empirical pass rate: NOT MEASURED")
    print("Critical failing cases: " + (", ".join(blockers) if blockers else "none observed"))
    ready = tested >= args.min_tested and score is not None and score >= args.min_score and not blockers
    print("Illustrative release policy: " + ("PASS" if ready else "NOT READY"))
    if not ready:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
