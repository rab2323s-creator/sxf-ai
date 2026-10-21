"""SXF / AI — Runway Gen-4.5 versus Kling 3.0 video economics lab.
Reproducible 48-scenario DECIMAL sensitivity analysis, no external API calls.
Source: Runway Dev official credits, $0.01 each, verified October 22, 2026.
6 published model/mode rates × 2 shared durations × 4 HYPOTHETICAL
Kling acceptance assumptions; Gen-4.5 acceptance arbitrarily set to 80%.
The scenarios are not quality, speed, acceptance or vendor benchmarks.
Run: python sxf-video-economics-lab.py
"""
from decimal import Decimal, getcontext
import json
getcontext().prec=18

USD_PER_CREDIT=Decimal("0.01")
RATES={
    "gen4.5": Decimal("12"),
    "kling3.0_standard_silent": Decimal("9"),
    "kling3.0_standard_audio": Decimal("13"),
    "kling3.0_pro_silent": Decimal("12"),
    "kling3.0_pro_audio": Decimal("17"),
    "kling3.0_4k": Decimal("43"),
}
SHARED_DURATIONS=(5,10)
KLING_ASSUMED_ACCEPTANCE=tuple(map(Decimal,("0.40","0.60","0.80","0.95")))
GEN_ASSUMED_ACCEPTANCE=Decimal("0.80")

def accepted_output_cost(model,seconds,acceptance):
    if not (Decimal("0")<acceptance<=Decimal("1")):
        raise ValueError("hypothetical acceptance must be greater than zero and at most one")
    return USD_PER_CREDIT*RATES[model]*Decimal(seconds)/acceptance

def main():
    cases=[]
    for model in RATES:
        for seconds in SHARED_DURATIONS:
            for kling_assumption in KLING_ASSUMED_ACCEPTANCE:
                # Gen-4.5 row uses 80% baseline in every case to keep one comparison policy.
                assumed = GEN_ASSUMED_ACCEPTANCE if model=="gen4.5" else kling_assumption
                cases.append({
                    "model":model,"seconds":seconds,
                    "hypothetical_acceptance":str(assumed),
                    "usd_per_generated_clip":str(USD_PER_CREDIT*RATES[model]*seconds),
                    "usd_per_accepted_clip":str(round(accepted_output_cost(model,seconds,assumed),6)),
                    "note":"output-only arithmetic; no measured success, audio quality or model inference"
                })
    assert len(cases)==48
    assert accepted_output_cost("gen4.5",10,GEN_ASSUMED_ACCEPTANCE)==Decimal("1.5")
    assert accepted_output_cost("kling3.0_standard_silent",10,Decimal("0.6"))==Decimal("1.5")
    threshold=GEN_ASSUMED_ACCEPTANCE*RATES["kling3.0_standard_silent"]/RATES["gen4.5"]
    assert threshold==Decimal("0.6")
    assert USD_PER_CREDIT*RATES["kling3.0_pro_audio"]*10==Decimal("1.70")
    print(json.dumps({
        "kind":"Executed arithmetic scenario study, NOT model benchmark",
        "cases":len(cases),
        "shared_duration_seconds":list(SHARED_DURATIONS),
        "gen4_5_assumed_acceptance":str(GEN_ASSUMED_ACCEPTANCE),
        "kling_standard_silent_break_even_acceptance":str(threshold),
        "results":cases
    },indent=2))
if __name__=="__main__":
    main()
