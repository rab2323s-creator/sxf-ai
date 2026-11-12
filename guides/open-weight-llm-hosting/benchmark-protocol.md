# SXF Hosting Protocol v1 — preregistered measurement design

Published 2026-11-12. Status: **protocol only; no four-provider benchmark executed**.

## Objective
Estimate total cost per accepted inference response, latency under load, reliability and workload feasibility when hosting the *same* open-weight model via managed token APIs or custom GPU workers.

## Evidence boundaries
- Documented: public price ledgers and supported product capabilities, dated.
- Modeled: workload estimates, equations and sensitivity scenarios; not observed results.
- Unmeasured: latency, TTFT, tokens/sec, GPU uptime, invoices, cold-start and real quality.

## Preregistration
1. Pin identical model weights, revision, tokenizer and template. A shared branded model ID does not guarantee identical binary deployment.
2. Use original non-sensitive synthetic tasks in three groups: short-chat (100-1,000 input tokens), retrieval-heavy (4,000-16,000 input), and output-heavy (>512 output).
3. Match temperature, reasoning effort, max output budget and timeout; flag unsupported settings.
4. Distinguish product paths: Together/Fireworks token API, Runpod Serverless worker, Modal custom GPU app. Do not mix with other product tiers.
5. Prepare five warm-ups; then at least 30 valid trials per stratum at concurrency 1, 4 and 16. Run cold starts after a verified full shutdown. Randomize provider order.
6. Measure p50/p95 end-to-end and TTFT with streaming; tokens/sec needs reliable completion counts and generation duration. Record 429/5xx, timeouts, invalid output, accepted-answer rubric and retries.
7. Use dated invoices, billable replicas, CPU/RAM, storage, network, reservations, operations and retries. Do not substitute GPU-only published rates for actual invoices.
8. Publish raw redacted CSV, billing ledger, script revision, region, GPU SKU, model ID, uncertainty, confidence intervals and limitations. No winner without real runs.

## Optional non-streaming probe
The repository includes hosting_probe.py, an optional opt-in standard-library Python probe for OpenAI-compatible chat endpoints. It records HTTP status, wall time and API-reported token counts. It does not measure TTFT, quality or GPU uptime and does not retain prompts/keys.

Supply a trusted HTTPS endpoint and an API key through a local environment variable. No requests are sent merely by importing or downloading the tool. Set a real account-side spend limit. Use only synthetic/non-sensitive prompts. It is not a validated benchmark until results are independently checked.

## Price-source ledger
- Together gpt-oss-120b: https://www.together.ai/models/gpt-oss-120b — $0.15/$0.60 input/output per million on 2026-11-12.
- Fireworks gpt-oss-120b: https://fireworks.ai/models/fireworks/gpt-oss-120b — $0.15/$0.60 input/output per million on 2026-11-12.
- Runpod H100 PRO Serverless: https://www.runpod.io/pricing — $5.39 worker GPU-hour; source page last updated Nov 9, 2026.
- Modal H100 SXM5: https://modal.com/pricing — $0.001097 per GPU-second; CPU/memory may be additional, verified 2026-11-12.
- Model provenance: https://help.openai.com/en/articles/11870455-openai-open-weight-models-gpt-oss.

## Equation audit
For N monthly requests and I input/O output tokens each:
- Token API = N * (I * input_rate + O * output_rate) / 1,000,000.
- GPU model = billable_hours * hourly_GPU_rate * (1 + hypothetical_overhead_fraction).
- Break-even GPU hours = token_API_cost / (hourly_GPU_rate * (1+overhead_fraction)).
- Average completion tokens/sec required at break-even = N * O / (break_even_hours * 3,600). This ignores input prefill, queues and actual runtime capability.
- Cost per 1,000 accepted requests = total_cost * 1,000 / (N * accepted_fraction).

Limitations: not a full total-cost-of-ownership estimate; staff, security, bandwidth, SLA, taxes and other costs vary. The 15% overhead default is a modeling assumption, not a published provider fee.
