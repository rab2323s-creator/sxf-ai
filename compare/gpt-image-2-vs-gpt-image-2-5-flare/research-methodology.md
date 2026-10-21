# SXF / AI – GPT Image 2 vs GPT Image 2.5 Flare: research and audit protocol

Reviewed: 2026-10-22. Source-specific rates from official OpenAI pricing and image generation documentation.
Run `python sxf-image-token-cost-lab.py`. Python 3 standard library, no API key or network.

## Executed original economic analysis
The lab creates 48 intentionally synthetic comparison rows: 2 models × 2 billing tiers (Standard, Batch) × 3 assumed output image token volumes (1,000 / 4,000 / 8,000) × 4 independently assumed accepted-image rates (40/60/80/95%). Input assumptions are 200 text input tokens and 1,000 image input tokens per job. All rates are published per-1M-token coefficients.
At 4,000 output image tokens in Standard mode under equal hypothetical token usage, GPT Image 2 costs $0.0645 and Flare $0.129; these are not provider per-image quotes because model token consumption and quality semantics vary.
With GPT Image 2 accepted at an ASSUMED 40%, Flare would need >80% accepted assets to be cheaper per accepted output under those restrictive equal-token conditions. This demonstrates a calculation method, NOT actual measured acceptance, model quality or speed. The script exports all 48 scenarios to CSV.

## Current model pricing – USD per 1M tokens
Standard GPT Image 2: text input 2.50; image input 4.00; image output 15.00.
Standard GPT Image 2.5 Flare: text input 5.00; image input 8.00; image output 30.00.
Batch GPT Image 2: 1.25 / 2 / 7.50.
Batch GPT Image 2.5 Flare: 2.50 / 4 / 15.
Input caching only applies to the Responses API image generation tool, not direct Images API calls. The live pricing and docs should be confirmed on purchase date. The older GPT Image 2 calculator does NOT predict 2.5 token usage.

## Benchmark missing on purpose
No images from GPT Image 2 or Flare were generated for this article; there are no paid model requests, observed success rates, p95 measurements or independently scored image outputs. OpenAI's 50% lower latency and quality-improvement statements are OpenAI-reported claims, not an SXF performance benchmark.

## Independent live benchmark protocol
1. Secure permissions for references and model data. Freeze a corpus (product photos, text-rich posters, multilingual graphics, multi-turn edits, transparent product cutouts).
2. Pin actual model IDs/snapshots, explicit supported output size, quality, background and file format. GPT Image 2.5 quality levels include xhigh/max, unlike GPT Image 2. Avoid declaring identical 'high' settings equivalent across generations.
3. Run multiple prompt variants on both services under specified plan/tier; record exact image usage, input prompt tokens, image input tokens, retries, policy rejections and output dimensions.
4. Blind-grade reference retention, legible and correct text, geometry, compositional requirements, unwanted changes across edits, and asset rights. Avoid turning subjectively scored work into false hard-accuracy numbers.
5. Report p50/p95 latency, actual invoice reconciliation, $ per accepted asset, human correction minutes and artifact hashes.
6. Publish dates, corpus size, confidence intervals, conditions and failure examples.

## Official sources
- https://developers.openai.com/api/docs/models/gpt-image-2
- https://developers.openai.com/api/docs/models/gpt-image-2.5-flare
- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/api/docs/guides/image-prompting
- https://openai.com/index/introducing-chatgpt-images-2-5/
