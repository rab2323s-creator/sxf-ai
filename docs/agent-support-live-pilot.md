# SXF support-agent live evaluation pilot (v1)

**Status:** Protocol and runnable harness only. **No model results have been collected or published.**
This pilot addresses the evidence gap in the [AI agent cost article](/guides/ai-agent-cost/). Do not change the article to claim tested agent accuracy unless a live run is completed, validated and disclosed.

## What is tested

- 24 original **synthetic** customer-support cases, grouped into six categories: returns, damaged arrivals, delivery status, cancellation, account privacy, warranty.
- Every case includes a publicly inspectable policy, order facts, and a **pre-registered expected decision**.
- One model call per case; no external tools, no real customer data or live write operations. The model gives *proposed decisions*, not executed actions.
- Measured: exact-match decision accuracy, response failure rate, completion latency, API usage tokens and estimated inference cost. Explanations are not independently fact-graded.
- Three deliberate boundary/adversarial wording cases test policy adherence within the small fixture set.
- This is **not an autonomous tool-using agent benchmark** and is **not statistically representative of production traffic**.

## Reproduce offline, without API access

```sh
python tests/test_agent_support_pilot.py
python scripts/agent_support_pilot.py --mode dry-run
```

The dry run validates the dataset's deterministic policy rules and report generation. Its 100% rule-check agreement **is not agent accuracy**. No inference occurs.

## Run the actual model, only when you approve API charges

Supply your own API key via an environment variable; **never commit the key or generated individual API logs**:

```sh
export OPENAI_API_KEY="YOUR_KEY"
python scripts/agent_support_pilot.py \
  --mode live \
  --model YOUR_SUPPORTED_CHAT_COMPLETIONS_MODEL \
  --input-usd-per-million PRICE_INPUT \
  --output-usd-per-million PRICE_OUTPUT \
  --max-cost-usd 2 \
  --output /tmp/sxf-agent-support-live-results.json
```

The token prices must be entered from the provider's official currently applicable rates. The cap is a **soft estimated budget** checked between requests; the final request can exceed it. Configure your provider account's actual billing limits independently. An API error counts as an incorrect case. No retries are issued. A nonzero process exit means the full 24-case dataset was not attempted.

## Research integrity before publication

1. Archive the exact dataset, rubric, runner SHA, provider/model version, run date, price-source URL and unmodified results JSON.
2. Have a human independently audit borderline decisions and whether the strict policy labels are appropriate. Document disagreements.
3. Repeat on separate dates (at least 3 complete runs) and report each run, not just the best. Report token pricing **as of the run date** and whether the actual invoice differs from the estimated API cost.
4. Add measured baseline human time and review/override time before claiming *enterprise ROI*; this pilot alone measures model decision accuracy, latency and estimated API spend only.
5. Publish results with explicit **synthetic dataset** and **small-sample** qualifiers, failures and disclosure of model/provider relationships.
6. Review for prompt injection and privacy risks before adapting to real customer data. Never execute account actions automatically from this harness.

Dataset: `data/agent-support-pilot-cases.json` • Runner: `scripts/agent_support_pilot.py` • Offline QA: `tests/test_agent_support_pilot.py`.
