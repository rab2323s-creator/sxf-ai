#!/usr/bin/env python3
"""Offline SXF Haiku evaluation starter: classification agreement with ground truth.

Input JSONL: id, group, expected, predicted. Example is deliberately synthetic,
NOT a record of API calls or measured model performance.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

def evaluate(path: Path) -> dict:
    groups=defaultdict(lambda:{"correct":0,"total":0})
    for lineno,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        row=json.loads(line)
        if not all(isinstance(row.get(key),str) for key in ("id","group","expected","predicted")):
            raise ValueError(f"Line {lineno}: missing string id/group/expected/predicted")
        groups[row["group"]]["total"]+=1
        groups[row["group"]]["correct"]+=int(row["expected"].strip().casefold()==row["predicted"].strip().casefold())
    total=sum(v["total"] for v in groups.values())
    correct=sum(v["correct"] for v in groups.values())
    if not total:
        raise ValueError("No labeled rows found")
    return {"dataset":str(path),"examples":total,"matched":correct,
            "exact_match_fraction":correct/total,
            "by_group":{g:{"examples":v["total"],"correct":v["correct"],
                           "exact_match_fraction":v["correct"]/v["total"]}
                        for g,v in sorted(groups.items())}}

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python sxf-haiku45-eval.py PATH_TO_JSONL")
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2,ensure_ascii=False))
