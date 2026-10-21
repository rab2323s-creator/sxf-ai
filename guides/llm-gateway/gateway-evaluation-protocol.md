# SXF AI LLM Gateway Evidence and Benchmark Protocol

The original HTTP experiment: 80 task IDs, three policies, a real local HTTPServer, synthetically injected 429 and 500 responses, and five incorrect 200-response schemas. Primary mock: 50 immediate successes, 10 recoverable 429 cases, 10 persistent 500, and 10 persistent 429. Backup mock: 15 valid and five invalid schemas in the 20 fallback cases. All provider responses were created by our test service, with no LLM calls.

The local lab uses HTTP requests to localhost, but does not measure network performance, model quality, streaming, external security, real provider quotas, region constraints, production concurrency, TLS, Retry-After waiting or jitter. The retry count is intentionally bounded at one. Modeled charge per attempted primary call is 0.002 USD and per backup call is 0.003 USD; these are teaching assumptions, not actual provider prices.

Run: python sxf_gateway_http_lab.py. Expected valid completions: baseline 50/80, retry 60/80, fallback 75/80, with 5 incorrect schemas rejected.

For a fair vendor evaluation, pin the same requests, model versions, response schema and tool contracts. Test provider and gateway nested retries, non-idempotent calls, partial streams, TLS and credentials, circuit breaker recovery, model substitution quality, RPM/TPM, token budgets, cached-input usage, customer isolation, redacted logging, and end-to-end accepted outcomes. Report p95 latency, failure counts, exact configuration, cost and vendor version. Never interpret this local lab as a benchmark of LiteLLM, Portkey, Cloudflare or Kong.
