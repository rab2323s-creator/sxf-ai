# SXF local AI workstations — methodology and integrity

**Published:** 2026-11-13. **Editorial evidence status:** original deterministic calculation, not an independently run physical hardware benchmark.

## Evidence hierarchy

1. Manufacturer specifications and prices: NVIDIA, Apple, AMD, Framework and Beelink sources linked in the guide (sources checked November 13, 2026). DGX Spark list pricing varies materially over time, and not all prices refer to equal configurations.
2. Independent measured inference data: attributed to BAEM1N's `llm-bench` project, Track B llama.cpp Q4_K_M cross-platform results. Apple device is the source's **M5 Max 128GB test rig**, *not claimed to be a Mac Studio M5 Ultra*. AMD source rig has **96GB**, not our illustrative 128GB system preset. Independent measurements and the SXF modelling dataset are kept separate.
3. SXF first-party analysis: `sxf-capacity-screen.py` implements a controlled, auditable mathematical screening model. No claims of an SXF physical workstation measurement or a GPU speed prediction.

## Calculation

For every hardware-system S, model M and format Q:

```
estimated weight GB = total_parameters_billions × nominal_bits_per_parameter / 8 × 1.10
indicative working set GB = estimated weight GB + 12 GB illustrative reserve
illustrative allocatable pool GB = installed unified memory GB × assumed allocatable share
margin GB = pool − working set
fit status = over budget if margin < 0; borderline if margin < 10% of pool; else fits indicative budget
```

The 1.10 multiplier, 12GB baseline reserve, and allocation shares (80%, 75%, 80%, 70%) are **scenario assumptions**, not manufacturer's guaranteed capacity or measurements. Decimal GB is used. Real GGUF Q4_K_M block sizes, quantization metadata, KV-cache size, tensor placement, model architecture and context concurrency vary. Active MoE parameters are shown for understanding compute, **never subtracted from resident weight storage**. A positive margin is a *screening result only*, not confirmation that the model will run or meet latency requirements.

Four system configurations × five example models × three nominal precisions = **60 scenarios**.

## Reproduction

```bash
python guides/local-ai-workstations/sxf-capacity-screen.py
python tests/test_local_ai_workstations.py
```

The Python script verifies byte-for-byte reproduction of `sxf-workstation-memory-screen.csv`, with no external packages. The interactive JavaScript calculator uses the same parameters and formula while allowing the user to change assumed memory share and context reserve. It does not upload data or require API keys.

## Attribution and cautions

BAEM1N source: https://github.com/BAEM1N/llm-bench/
NVIDIA: https://www.nvidia.com/en-us/products/workstations/dgx-spark/
Apple: https://support.apple.com/en-euro/128107
AMD: https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html

Neither this dataset nor the interactive tool is an official NVIDIA, Apple, AMD, Framework or benchmark-provider endorsement. No commercial placement or affiliate links have been added.
