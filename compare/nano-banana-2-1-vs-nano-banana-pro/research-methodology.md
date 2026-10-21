# SXF / AI — Nano Banana 2.1 vs Nano Banana Pro research and price lab

Reviewed: 2026-10-22. All publisher specifications checked against primary-source Google documentation.
SXF did NOT execute paid image inference, produce images from either model or independently measure quality and latency.

## Executed original cost sensitivity simulation
`python sxf-image-cost-lab.py` uses Python 3 standard library Decimal precision.
The lab evaluates 24 cases = 2 pricing tiers (Standard, Batch) x 3 image resolutions (1K,2K,4K) x 4 assumed 2.1 acceptance probabilities (40%,60%,80%,95%). In the illustrative counterfactual, Pro acceptance probability is arbitrarily fixed at 95%. **No acceptance rate is vendor-measured.**

Verified output-only pricing snapshot (Google Gemini API pricing, Oct 22 2026):
Standard: 2.1 [$0.0336,$0.0504,$0.113], Pro [$0.134,$0.134,$0.24] per 1K,2K,4K image.
Batch: 2.1 [$0.0168,$0.0252,$0.0567], Pro [$0.067,$0.067,$0.12].
Source: https://ai.google.dev/gemini-api/docs/pricing

At 2K Standard, if Pro reaches *an assumed* 95% usable output rate and all else is equal, 2.1 needs >35.73% acceptance to have a lower output-only cost per usable image: 0.95 × 0.0504 / 0.134. This threshold is arithmetic only; it says nothing about either model's actual success rates.

The calculator intentionally exposes user-editable acceptance assumptions and an optional identical per-call allowance for extra input/thinking charges; this is not a total-cost quote. Production costs may also include prompts, images, thinking, retries, search grounding, storage, review and service-tier pricing.

## Vendor evidence vs independent evidence
Google DeepMind's Nano Banana 2.1 model card contains 2.1 vs Pro comparisons using its own evaluation pipeline, including overall preference (1050 ±14 vs Pro 935 ±8), infographic design (1048 ±17 vs Pro 912 ±12), and character consistency. **These are Google-reported evaluations; SXF did not reproduce them.** Their scales and methodology may not transfer to a user's specific visual workload.

## Protocol for a genuine live study
1. Version the prompt corpus, source image rights, languages, resolutions, aspect ratios and benchmark acceptance rubric before running any API calls.
2. Call model `gemini-nano-banana-2.1` and `gemini-3-pro-image` with compatible settings. Record exact response image count and prompt/input details.
3. Blind-grade prompt adherence, brand fidelity, text legibility, layout, character/object consistency, edits, failures and required post-processing.
4. Track latency p50/p95, wall time, failures, retries, real invoice tokens, grounding charges and input images.
5. Evaluate privacy, SynthID, copyright/consent and enterprise data controls; do not publish images without rights.
6. Report sample sizes and uncertainty, never promote Google internal benchmarks as third-party SXF findings.

## Official references
https://ai.google.dev/gemini-api/docs/pricing
https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1
https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image
https://ai.google.dev/gemini-api/docs/image-generation
https://deepmind.google/models/model-cards/nano-banana-2-1/
