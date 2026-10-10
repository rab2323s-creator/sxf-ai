# Zero-API-fee local model evaluation (recommended first)

**Free path:** GitHub Actions → **Free local Qwen support pilot (no paid API)** → **Run workflow** → 3 repetitions. This uses an openly licensed Qwen3 4B model (GGUF Q4_K_M) on the GitHub-hosted CPU runner. **No OpenAI API key, payment API, or cloud-model account is used.** The action is manual only and does not execute on every push. Free GitHub Actions eligibility and quotas depend on repository/account settings.

- Model: `unsloth/Qwen3-4B-Instruct-2507-GGUF` at pinned revision `b48eaa0431fbfc07e852bc574f440def545d5ccb`; exact model file SHA256 `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597`, Apache-2.0.
- Actual inference: `scripts/agent_support_local_pilot.py` contacts **only localhost** llama.cpp server. It saves answers, errors, total input/output tokens, elapsed time, exact-match accuracy and model checksum.
- One free run: 24 synthetic tasks × 3 repetitions = 72 measured recommendations.
- The downloadable artifact `sxf-free-local-pilot-results` is the raw evidence; manually review bad cases and publish **both** correct and incorrect results.
- **Not a true autonomous agent**, as there are no tool calls or write actions. Do not call it a real-world enterprise study. Vendor inference API fee is $0; machine/energy/maintenance are not valued.
- No public article claims are added automatically. Review the measured result first, then publish an accurately labelled small synthetic benchmark.
- Github workflow timeouts and remote model download can fail; such failures must not be presented as model accuracy.

---

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
