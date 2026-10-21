"""SXF / AI: GPT-Image-2 vs GPT-Image-2.5 Flare cost sensitivity experiment.

Python 3 standard library only. Run: python sxf-image-token-cost-lab.py
48 synthetic scenarios = 2 models × 2 processing tiers × 3 output-token
scenarios × 4 ASSUMED acceptance rates. No OpenAI image calls,
generated images, real quality measurements, or independent latency data.

Input token counts are held equal only to explain pricing mathematics.
In real requests the models may use DIFFERENT token quantities for the
same image size/quality. Check official API usage and invoices.
Published USD per million token rates verified 2026-10-22.
"""
from decimal import Decimal, getcontext
import csv
from pathlib import Path

getcontext().prec=20
D=Decimal
RATES={
 "standard":{
  "gpt-image-2":{"text_in":"2.50","image_in":"4","image_out":"15"},
  "gpt-image-2.5-flare":{"text_in":"5","image_in":"8","image_out":"30"}},
 "batch":{
  "gpt-image-2":{"text_in":"1.25","image_in":"2","image_out":"7.50"},
  "gpt-image-2.5-flare":{"text_in":"2.50","image_in":"4","image_out":"15"}}
}
OUTPUT_TOKENS=(1000,4000,8000) # fictional usage examples, NOT model predictions
ACCEPT_RATES=(D(".40"),D(".60"),D(".80"),D(".95")) # fictional acceptance
TEXT_INPUT=200
IMAGE_INPUT=1000
def cost(mode,model,output_tokens,text_tokens=TEXT_INPUT,image_tokens=IMAGE_INPUT):
    r=RATES[mode][model]
    return (D(r["text_in"])*text_tokens+D(r["image_in"])*image_tokens
            +D(r["image_out"])*output_tokens)/D(1000000)
def run():
    out=[]
    for mode in RATES:
        for model in RATES[mode]:
            for n in OUTPUT_TOKENS:
                for accept in ACCEPT_RATES:
                    c=cost(mode,model,n)
                    out.append({"mode":mode,"model":model,"hypothetical_output_tokens":n,
                        "hypothetical_text_input_tokens":TEXT_INPUT,
                        "hypothetical_image_input_tokens":IMAGE_INPUT,
                        "assumed_acceptance":str(accept),
                        "usd_per_generated_image":str(c),
                        "usd_per_accepted_image":str((c/accept).quantize(D(".000001")))})
    assert len(out)==48
    assert cost("standard","gpt-image-2",4000)==D(".0645")
    assert cost("standard","gpt-image-2.5-flare",4000)==D(".129")
    assert cost("batch","gpt-image-2",4000)==D(".03225")
    assert cost("batch","gpt-image-2.5-flare",4000)==D(".0645")
    # With identical token usage, Flare's rate is 2x GPT-Image-2;
    # to be cheaper per *accepted* image, its acceptance must be >2x.
    baseline=D(".40")
    break_even=baseline*(cost("standard","gpt-image-2.5-flare",4000) /
                         cost("standard","gpt-image-2",4000))
    assert break_even==D(".80")
    return out,break_even

if __name__=="__main__":
    rows,threshold=run()
    print(f"SXF local synthetic pricing sensitivity: {len(rows)} scenarios")
    print("Pricing date: 2026-10-22. No API calls / quality tests.")
    print(f"At 40% hypothetical GPT-Image-2 acceptance and identical input/output tokens,")
    print(f"Flare must exceed {threshold*100}% accepted images to reduce cost per accepted asset.")
    print("Standard costs at 200 text + 1000 image input + 4000 image output tokens:")
    print("GPT-Image-2: $0.0645; Flare: $0.129. These token volumes are illustrative.")
    out=Path(__file__).with_name("sxf-image-token-scenarios.csv")
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out.name}")
