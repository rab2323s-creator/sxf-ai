# SXF / AI Grok 4.3 — reproducible economic evaluation and source audit

Reviewed October 22, 2026. Publication focuses on API-oriented search intent for Grok 4.3, not on a claimed independent leader-board ranking.

## Original executable study
Run `python sxf-grok43-context-cost-lab.py` using only Python 3 stdlib. The test processes 48 entirely fictional usage scenarios:
- Four prompt lengths: 199k, 201k, 400k and 900k.
- Two output lengths: 2k and 8k tokens.
- Three HYPOTHETICAL cached fractions: 0%, 50%, 80%.
- Standard and Batch pricing (20% Grok 4.3 Batch discount).

The cost model follows the xAI pricing break at 200k prompt tokens. It checks the sum of input and output against a one-million-token working budget as a conservative planning control; this is not a guarantee about the provider's exact output budget or response cap. It computes raw price arithmetic and writes CSV. **No calls to xAI, images, real prompts, benchmarks or actual cache hits occurred.**

Example outputs: 199k prompt / 2k output, uncached Standard = $0.25375; 201k / 2k uncached Standard = $0.5125; 201k / 2k, HYPOTHETICALLY half cached Batch = $0.24116. Passing the 200k tier changes billing, but comparisons are illustrative. No output-quality or latency measurement exists.

## Official model evidence
- Model identity and 1M context: https://docs.x.ai/developers/models/grok-4.3
- Pricing with >=200k long tier and Batch: https://docs.x.ai/developers/pricing
- Rate limits by service tier: https://docs.x.ai/developers/rate-limits
- xAI Responses and prompt caching practices: https://docs.x.ai/developers/model-capabilities/text/best-practices
- Reasoning semantics: https://docs.x.ai/developers/model-capabilities/text/reasoning
- Structured outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- Cost ticks actual API billed usage: https://docs.x.ai/developers/cost-tracking
- Model retirement/migration: https://docs.x.ai/developers/migration/may-15-retirement
- xAI Amazon Bedrock announcement: https://x.ai/news/grok-amazon-bedrock
- AWS Grok 4.3 card: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-xai-grok-4-3.html

## Important caveats
Some provider overview prose names 'none/low/medium/high' while the model detail 'reasoning efforts' list also includes xhigh. For reliable deployment, test model/region/endpoint acceptance rather than promise xhigh on every deployment.
The xAI cost field `usage.cost_in_usd_ticks` represents actual billed cost at the relevant API endpoint; 1 USD = 10^10 ticks, as documented.
Newer Grok releases are available, including Grok 4.6 and 4.7. Model availability and price are region/time dependent. Tool calls and Priority tiers can add costs not represented by the estimator.

## Genuine live validation protocol (not completed)
1. Obtain API keys and contract authorization. Pin model/region/endpoint, service tier, reasoning level, token usage.
2. Create consented 20/100/200K+ document retrieval and function calling tasks with human-reviewed correct outputs.
3. Record all successes, refusals, schema validation, tool errors, p50/p95 latency, cached token quantities and total billed cost ticks.
4. Compare with 4.6 and 4.7 only under equivalent API settings. Document long-context billing and different context limits.
5. Publish reproducible anonymized fixtures and raw observations (not fabricated scores).
