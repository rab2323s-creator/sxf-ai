#!/usr/bin/env python3
"""SXF benchmark-interpretation lab: auditable synthetic examples; no live rankings."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parent
with (ROOT/"sxf-leaderboard-claim-audit.csv").open(encoding="utf-8",newline="") as f:
    claims=list(csv.DictReader(f))
assert len(claims)==12
assert len({c["id"] for c in claims})==12
allowed={"different-unit","different-task","version-break","uncertainty","variant-mismatch","scope-overreach","interpretation","missing-constraint","none"}
assert all(c["failure_class"] in allowed for c in claims)
assert all(c["status"] in {"REJECT","CONDITIONALLY VALID"} for c in claims)
assert all((c["failure_class"]=="none")== (c["status"]=="CONDITIONALLY VALID") for c in claims)
assert all(c["sxf_reason"] and c["safer_reading"] for c in claims)
reject=sum(c["status"]=="REJECT" for c in claims)
assert reject==9
audit=json.loads((ROOT/"aa-index-transition.json").read_text(encoding="utf-8"))
versions=audit["versions"]
assert len(versions)==2
assert [v["evaluations"] for v in versions]==[10,9]
assert [v["private_evaluation_weight_pct"] for v in versions]==[45,60]
assert all(sum(v["category_weights_pct"].values())==100 for v in versions)
assert len(audit["v5_changes"]["new"])==2
assert len(audit["v5_changes"]["retired_from_index"])==3
print(f"PASS: {len(claims)} authored examples, {reject} unsafe examples and {len(claims)-reject} conditional cases; AA methodology audit validated. No physical or vendor models evaluated.")
