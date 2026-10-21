"""SXF / AI Grok 4.3 original reproducible long-context billing experiment.

A REAL executable decimal arithmetic test of published xAI rates, using
48 SYNTHETIC usage scenarios: 4 prompt lengths x 2 output lengths x
3 assumed cache-hit rates x 2 service tiers.

No xAI API calls, hallucination tests, benchmark scores, invoices,
measured caching behavior or actual model latency. Run:
    python sxf-grok43-context-cost-lab.py
The script writes a CSV of all 48 scenarios alongside itself.
Source: https://docs.x.ai/developers/pricing (checked 2026-10-22).
"""
from decimal import Decimal, getcontext
from pathlib import Path
import csv

getcontext().prec=24
D=Decimal
PRICE={
    "short":{"input":D("1.25"),"cached":D("0.20"),"output":D("2.50")},
    "long":{"input":D("2.50"),"cached":D("0.40"),"output":D("5.00")},
}
TOKENS=(199000,201000,400000,900000)
OUTPUTS=(2000,8000)
CACHE=(D("0"),D("0.5"),D("0.8"))
BATCH=(False,True)
CONTEXT_LIMIT=1000000
def estimate(prompt, output, cached_share, batch):
    if prompt + output > CONTEXT_LIMIT:
        raise ValueError("prompt + output exceeds reference context")
    if not D(0)<=cached_share<=D(1):
        raise ValueError("Invalid assumed cache share")
    tier="long" if prompt>=200000 else "short"
    rates=PRICE[tier]
    factor=D("0.8") if batch else D("1")
    cached=D(prompt)*cached_share
    uncached=D(prompt)-cached
    cost=(uncached*rates["input"]+cached*rates["cached"]+
          D(output)*rates["output"])/D(1000000)*factor
    return tier,cost
def main():
    rows=[]
    for prompt in TOKENS:
        for output in OUTPUTS:
            for cache in CACHE:
                for batch in BATCH:
                    tier,cost=estimate(prompt,output,cache,batch)
                    rows.append({
                        "fictional_prompt_tokens":prompt,
                        "fictional_output_tokens":output,
                        "assumed_cache_fraction":str(cache),
                        "service":"batch" if batch else "standard",
                        "billing_tier":tier,
                        "estimated_token_cost_usd":str(cost.quantize(D(".000001"))),
                        "disclosure":"Synthetic usage, pricing-only. Not actual model data."
                    })
    assert len(rows)==48
    assert estimate(199000,2000,D("0"),False)[1]==D(".25375")
    assert estimate(201000,2000,D("0"),False)[1]==D(".5125")
    assert estimate(201000,2000,D(".5"),False)[1]==D(".30145")
    assert estimate(201000,2000,D(".5"),True)[1]==D(".24116")
    assert estimate(900000,8000,D(".8"),True)[1]==D(".5968")
    assert all(r["estimated_token_cost_usd"] for r in rows)
    target=Path(__file__).with_name("sxf-grok43-context-cost-scenarios.csv")
    with target.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    print("SXF original arithmetic lab: 48 fictional use cases; 0 provider calls")
    print("199k prompt+2k output, uncached standard: $0.253750")
    print("201k prompt+2k output, uncached standard: $0.512500")
    print("201k prompt+2k output, 50% cached batch: $0.241160")
    print("Created",target.name)

if __name__=="__main__":
    main()
