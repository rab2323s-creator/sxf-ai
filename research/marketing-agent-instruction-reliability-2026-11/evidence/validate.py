#!/usr/bin/env python3
"""SXF Lab #2: audit CSV exports using Python's standard library."""
import csv
from pathlib import Path
COLS="source_id,company,region,sector,observed_signal,reason_for_fit,source_evidence,draft_subject,draft_body,review_status".split(",")
def check(filename):
    with open(filename,encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f))
    if not rows: return {"file":filename,"error":"empty"}
    header_ok=rows[0]==COLS
    data=rows[1:]
    valid=sum(len(r)==10 for r in data) if header_ok else 0
    drafts=[r[-2] for r in data if len(r)>=10 and r[-1]=="DRAFT_NEEDS_HUMAN_APPROVAL"]
    return {"file":filename,"rows":len(data),"header_ok":header_ok,"valid_csv_rows":valid,"drafts_50_80_words":sum(50<=len(x.split())<=80 for x in drafts)}
if __name__=="__main__":
    import sys
    for file in sys.argv[1:]: print(check(file))
# Source text exports are intentionally preserved unaltered. To reproduce
# SXF scorecard, isolate each labeled CSV block first, then run this validator.
