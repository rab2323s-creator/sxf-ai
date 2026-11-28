"""Recompute SXF derived statistics from published aggregate facts; Python 3, offline."""
from pathlib import Path
import csv
import math
ROOT = Path(__file__).resolve().parent
with (ROOT / "latency-summary.csv").open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert sum(int(r["usable_turns"]) for r in rows) == 2078
assert sum(int(r["observed_turns"]) for r in rows) == 2158
p50_min = min(int(r["p50_ms"]) for r in rows)
p95_min = min(int(r["p95_ms"]) for r in rows)
for r in rows:
    p50, p95 = int(r["p50_ms"]), int(r["p95_ms"])
    coverage = 100 * int(r["usable_turns"]) / int(r["observed_turns"])
    score = 50 * (p50_min / p50 + p95_min / p95)
    assert math.isclose(coverage, float(r["coverage_pct"]), abs_tol=0.000051)
    assert p95-p50 == int(r["tail_gap_ms"])
    assert math.isclose(p95/p50, float(r["tail_ratio"]), abs_tol=0.000051)
    assert math.isclose(score, float(r["sxf_index_50_50"]), abs_tol=0.000051)
    print(r["platform"], round(score, 2), round(coverage, 2))
with (ROOT / "task-summary.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        clean, realistic = int(r["clean_pass_at_1_pct"]), int(r["realistic_pass_at_1_pct"])
        assert clean-realistic == int(r["sxf_drop_pp"])
        assert math.isclose(100*realistic/clean, float(r["sxf_retention_pct"]), abs_tol=0.000051)
        print(r["model"], clean-realistic, round(100*realistic/clean, 2))
print("PASS: SXF arithmetic, no provider calls")
