#!/usr/bin/env python3
"""SXF offline classification/authorization scorer (synthetic starter only).

JSONL must include id, group, expected, predicted. Generate real model predictions
before attributing scores to Command A+ or any alternative model.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

def score(path: Path) -> dict:
    buckets=defaultdict(lambda: {"total":0,"matched":0})
    for i,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        row=json.loads(line)
        for k in ("id","group","expected","predicted"):
            if not isinstance(row.get(k),str):
                raise ValueError(f"line {i}: {k} must be a string")
        group=row["group"]
        matched=(row["expected"].strip().casefold()==row["predicted"].strip().casefold())
        buckets[group]["total"]+=1
        buckets[group]["matched"]+=int(matched)
    if not buckets: raise ValueError("Empty dataset")
    total=sum(x["total"] for x in buckets.values())
    matched=sum(x["matched"] for x in buckets.values())
    return {
        "dataset":str(path),"cases":total,"matched":matched,
        "exact_match_fraction":matched/total,
        "by_group":{
            key:{"cases":x["total"],"matched":x["matched"],
                 "exact_match_fraction":x["matched"]/x["total"]}
            for key,x in sorted(buckets.items())
        },
        "disclosure":"Synthetic fixtures do not represent tested Cohere model outputs."
    }

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python sxf-command-a-plus-eval.py path/to/labeled_predictions.jsonl")
    print(json.dumps(score(Path(sys.argv[1])),indent=2,ensure_ascii=False))
