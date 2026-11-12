#!/usr/bin/env python3
"""SXF deterministic memory-capacity screening. NOT a real-hardware benchmark.
Decimal GB. Weight estimate: params_in_billions * nominal_bits / 8 * 1.10.
Context/runtime reserve is illustrative and not a measured model KV cache.
"""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SYSTEMS=[{"slug":"spark","name":"NVIDIA DGX Spark (128GB)","memory":128,"share":80,"bw":273,"notes":"GB10/CUDA; 128 GB model, not the 64 GB variant","source":"https://www.nvidia.com/en-us/products/workstations/dgx-spark/"},{"slug":"max","name":"Mac Studio M5 Max (128GB upgrade)","memory":128,"share":75,"bw":614,"notes":"40-core GPU option; 128GB is not the $2,499 base configuration","source":"https://support.apple.com/en-euro/128107"},{"slug":"ultra","name":"Mac Studio M5 Ultra (256GB upgrade)","memory":256,"share":80,"bw":1200,"notes":"96 GB is the base; 256 GB is a higher-cost option","source":"https://support.apple.com/en-euro/128107"},{"slug":"ryzen","name":"Ryzen AI Max+ 395 PC (128GB)","memory":128,"share":70,"bw":256,"notes":"AMD x86/ROCm support depends on OS and model/runtime build","source":"https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html"}]
MODELS=[{"slug":"qwen9","name":"Qwen3.5 9B dense","params":9,"active":9},{"slug":"qwen27","name":"Qwen3.5 27B dense","params":27,"active":27},{"slug":"qwen35","name":"Qwen3.5 35B-A3B MoE","params":35,"active":3},{"slug":"qwen122","name":"Qwen3.5 122B-A10B MoE","params":122,"active":10},{"slug":"qwen235","name":"Qwen3 235B-A22B MoE","params":235,"active":22}]
QUANTS=[("Q4",4.5),("Q8",8.5),("FP16",16)]
def rows():
    for system in SYSTEMS:
        for model in MODELS:
            for label,bits in QUANTS:
                weights=model["params"]*bits/8*1.10
                need=weights+12
                pool=system["memory"]*system["share"]/100
                margin=pool-need
                status="over indicative budget" if margin<0 else ("borderline" if margin<pool*.10 else "fits indicative budget")
                yield [system["name"],system["memory"],system["share"]/100,model["name"],model["params"],model["active"],label,bits,1.1,12,
                       f"{weights:.1f}",f"{need:.1f}",f"{pool:.1f}",f"{margin:.1f}",status]
HEAD="system,unified_memory_gb,illustrative_allocatable_fraction,model,total_params_billions,active_params_billions,format,illustrative_bits_per_parameter,weight_overhead_factor,reserved_runtime_and_context_gb,estimated_weights_with_overhead_gb,estimated_total_gb,illustrative_pool_gb,margin_gb,capacity_screen_only".split(",")
if __name__=="__main__":
    import io
    buf=io.StringIO(newline="")
    writer=csv.writer(buf,lineterminator="\n",quoting=csv.QUOTE_ALL)
    writer.writerow(HEAD);writer.writerows(rows())
    expected=list(csv.reader(io.StringIO(buf.getvalue())))
    actual=list(csv.reader((ROOT/"sxf-workstation-memory-screen.csv").open(newline="")))
    if len(actual)!=len(expected):
        raise SystemExit(f"ERROR: scenario row count mismatch {len(actual)} != {len(expected)}")
    for i,(got,want) in enumerate(zip(actual,expected)):
        if len(got)!=len(want):
            raise SystemExit(f"ERROR: wrong column count on row {i}")
        for j,(a,b) in enumerate(zip(got,want)):
            if a==b:continue
            try:
                if abs(float(a)-float(b))<=0.101:continue
            except (TypeError,ValueError):pass
            raise SystemExit(f"ERROR: scenario {i}, column {j}: {a!r} != {b!r}")
    print("PASS: verified 60 SXF capacity scenarios to displayed 0.1GB precision; NOT physical benchmarks.")
