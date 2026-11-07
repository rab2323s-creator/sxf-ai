#!/usr/bin/env python3
"""SXF offline ranked retrieval evaluator for embedding experiments.

Expected JSONL: id, group, relevant_ids (list), ranked_ids (list).
The bundled fixtures are synthetic; predictions are NOT Mistral outputs.
Scoring reports Recall@1, Recall@5 and reciprocal rank of first relevant hit.
Multiple relevant documents are supported. No network/API calls.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

def evaluate(path: Path) -> dict:
    buckets=defaultdict(lambda:{"queries":0,"recall1_sum":0.0,"recall5_sum":0.0,
                                "rr_sum":0.0})
    for number,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        case=json.loads(line)
        if not isinstance(case.get("id"),str) or not isinstance(case.get("group"),str):
            raise ValueError(f"line {number}: id/group must be strings")
        ranked=case.get("ranked_ids")
        relevant=case.get("relevant_ids")
        if (not isinstance(ranked,list) or not isinstance(relevant,list)
                or not all(isinstance(s,str) for s in ranked+relevant)
                or not relevant or len(set(relevant))!=len(relevant)
                or len(set(ranked))!=len(ranked)):
            raise ValueError(f"line {number}: unique ranked_ids and nonempty relevant_ids required")
        gold=set(relevant)
        found=[i+1 for i,doc in enumerate(ranked) if doc in gold]
        b=buckets[case["group"]]
        b["queries"]+=1
        b["recall1_sum"]+=len(gold.intersection(ranked[:1]))/len(gold)
        b["recall5_sum"]+=len(gold.intersection(ranked[:5]))/len(gold)
        b["rr_sum"]+=(1/found[0] if found else 0.0)
    if not buckets:
        raise ValueError("Empty fixture")
    def summary(stats: dict) -> dict:
        n=stats["queries"]
        return {
            "queries":n,
            "recall_at_1":stats["recall1_sum"]/n,
            "recall_at_5":stats["recall5_sum"]/n,
            "mrr":stats["rr_sum"]/n,
        }
    totals={k:sum(b[k] for b in buckets.values()) for k in (
        "queries","recall1_sum","recall5_sum","rr_sum")}
    return {
        "dataset":str(path),
        "total":summary(totals),
        "by_group":{name:summary(stats) for name,stats in sorted(buckets.items())},
        "disclosure":"Synthetic example rankings only; not measured Mistral Embed retrieval performance.",
    }

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python sxf-mistral-embed-retrieval.py labeled_rankings.jsonl")
    print(json.dumps(evaluate(Path(sys.argv[1])),ensure_ascii=False,indent=2))
