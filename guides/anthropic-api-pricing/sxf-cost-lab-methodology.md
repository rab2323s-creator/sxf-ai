# SXF Claude API Cost Lab v1.0 — Reproducible Method
Date: 2026-11-08. Public article: https://sxf.si/guides/anthropic-api-pricing/

## Evidence statement
This dataset is an original deterministic **cost simulation**, not a live Anthropic API experiment. All scenario token volumes and acceptance percentages are hypothetical unless explicitly specified otherwise. No real-world accuracy, latency, win rate, cache hit rate or invoice measurement is implied.

## Primary rate sources
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/build-with-claude/batch-processing
Rates were checked on November 8, 2026; USD per million billable tokens.

## Model
For each request use mutually exclusive categories U (normal input), O (output), W5 (5-minute write), W1 (1-hour write), R (cache read) and model-specific unit rates (pu,po,pw5,pw1,pr):
cost = (U*pu + O*po + W5*pw5 + W1*pw1 + R*pr)/1000000.
Multiply by eligible modifiers: Batch 0.5; Opus 5.5 Fast 2.0 (not with Batch); US-only inference 1.1. Add separately billed tools and operating costs outside token charges.
Haiku 5.5 threshold: prompt_length = U + W5 + W1 + R, and prompt_length > 100000 switches all categories for the request to higher rate (not marginal tiering).

## Fixtures and computed results
Scenario 01: 100000 requests with U=2500,O=300: Haiku 5.5 $40.00; Sonnet 5.5 $800.00; Opus 5.5 $1600.00. No caching, Batch or tools.
Scenario 02: 10000 requests with U=20000,O=6000: Haiku $50.00; Sonnet $1000.00; Opus $2000.00. No retries or tool charges.
Scenario 03: 1000 Sonnet 5.5 requests with 40000-token cacheable prefix, U=2000, O=1000 every request, first W5=40000 and later R=40000 for 999 requests, with perfect hits without expiry. Cost = $0.10 write + $3.996 cache reads + $4 fresh input + $10 output = $18.096. No-cache baseline = $94.00. This is an optimistic mathematical example, NOT a production cache prediction.

## Prompt cache break-even
Without cache for identical reusable prefix P across N requests: N*P*base_input_price.
With cache: P*(write_multiplier+(N-1)*cache_read_multiplier)*base_input_price.
On Sonnet/Opus 5.5: 5-minute write=1.25 and read=.05 gives break-even savings starting at N=2; 1-hour write=2.0 and read=.05 gives savings from N=3; requires cacheability and timely hits.

## Limitations
Source prices are Anthropic first-party lists; partner cloud routing and enterprise discount terms differ.
The tokenizer may differ by model version, and price does not demonstrate efficacy.
Excluded: taxes, network, search/tools, retries, human review, storage, incidents, negotiated discounts, payment conditions and actual acceptance-rate measurements.
Revalidate all model prices and API behavior before refreshing article or deploying financial plans.
