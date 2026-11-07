#!/usr/bin/env python3
"""SXF offline long-context citation-selection accuracy scorer.

Input JSONL: id, context_band, position, expected_source, predicted_source.
User-supplied predictions must come from a real measured model run before
accuracy can be attributed to any model. Bundled examples are synthetic.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

VALID_BANDS = {"8k", "32k", "128k", "1m"}
VALID_POSITIONS = {"start", "middle", "end"}

def evaluate(path: Path) -> dict:
    groups=defaultdict(lambda:{"correct":0,"total":0})
    count=0
    matched=0
    for lineno,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        row=json.loads(line)
        for field in ("id","context_band","position","expected_source","predicted_source"):
            if not isinstance(row.get(field),str):
                raise ValueError(f"line {lineno}: missing string {field}")
        if row["context_band"] not in VALID_BANDS or row["position"] not in VALID_POSITIONS:
            raise ValueError(f"line {lineno}: invalid band or evidence position")
        ok=row["expected_source"].strip()==row["predicted_source"].strip()
        group=f'{row["context_band"]}/{row["position"]}'
        groups[group]["total"]+=1
        groups[group]["correct"]+=int(ok)
        count+=1
        matched+=int(ok)
    if not count:
        raise ValueError("No examples")
    return {
        "data":str(path),
        "examples":count,
        "exact_source_accuracy":matched/count,
        "correct":matched,
        "by_band_and_placement":{
            key:{"examples":value["total"],"correct":value["correct"],
                 "exact_source_accuracy":value["correct"]/value["total"]}
            for key,value in sorted(groups.items())
        },
        "disclaimer":"No model performance inferred from synthetic data."
    }

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python sxf-scout-eval.py path/to/real_predictions.jsonl")
    print(json.dumps(evaluate(Path(sys.argv[1])),ensure_ascii=False,indent=2))
