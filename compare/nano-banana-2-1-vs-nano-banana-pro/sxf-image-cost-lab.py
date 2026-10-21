"""SXF Nano Banana 2.1 vs Pro: audited published-price sensitivity lab.
Executes 24 deterministic hypothetical economics scenarios: two billing modes,
three output resolutions, four assumed usable-output acceptance rates.
These are arithmetic simulations using Google published prices (Oct 22, 2026).
No Gemini model calls, generated images, latency or quality benchmark.
Run: python sxf-image-cost-lab.py
"""
from decimal import Decimal, getcontext
import json
getcontext().prec=16
PRICES={
 "standard":{"1K":("0.0336","0.134"),"2K":("0.0504","0.134"),"4K":("0.113","0.240")},
 "batch":{"1K":("0.0168","0.067"),"2K":("0.0252","0.067"),"4K":("0.0567","0.120")}
}
ACCEPT=("0.40","0.60","0.80","0.95") # Explicit assumptions, NOT observed accuracy
def calc():
    out=[]
    for mode, resolutions in PRICES.items():
        for size, (a,b) in resolutions.items():
            nano=Decimal(a);pro=Decimal(b)
            for assumed in ACCEPT:
                rate=Decimal(assumed)
                out.append({
                    "mode":mode,"resolution":size,"nano21_output_only_usd":a,
                    "pro_output_only_usd":b,
                    "assumed_nano21_acceptance":assumed,
                    "assumed_pro_acceptance":"0.95",
                    "nano21_usd_per_accepted":str(round(nano/rate,6)),
                    "pro_usd_per_accepted":str(round(pro/Decimal(".95"),6)),
                    "nano21_less_cost_per_accepted":nano/rate<pro/Decimal(".95")
                })
    assert len(out)==24
    # Price comparisons are source-backed arithmetic, not quality measurements.
    assert Decimal(PRICES["standard"]["2K"][0])==Decimal(".0504")
    assert Decimal(PRICES["standard"]["2K"][1])==Decimal(".134")
    threshold=Decimal(".95")*Decimal(".0504")/Decimal(".134")
    assert round(threshold,4)==Decimal(".3573")
    return out,threshold
if __name__=="__main__":
    rows,threshold=calc()
    print(json.dumps({"kind":"illustrative scenario analysis, not model benchmark",
      "sample_count":len(rows),"nano21_acceptance_break_even_if_pro_is_95pct_at_2K_standard":
       str(round(threshold,4)),"results":rows},indent=2))
