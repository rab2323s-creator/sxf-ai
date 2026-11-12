# SXF Browser Agent Task Lab v1 — Preregistered Evaluation

Published: 2026-11-12. **No commercial AI agent head-to-head tests have been executed.**

## Question and methodology
How do Browser Use, Stagehand and Skyvern compare on **complete approved user tasks** when success is verified independently of an agent's own completion message? The same URL, set of synthetic tasks, execution budget, timeout, region and approval policies must be held fixed.

## Open research artifacts
- fixture.html: 12 same-origin synthetic, deterministic interactive tasks.
- browser-task-manifest.json: the frozen objectives and independent outcome criteria.
- run_fixture_baseline.py: deterministic Playwright oracle; 12 tasks × 3 iterations. **This is not a Browser Use, Stagehand or Skyvern run.**
- benchmark-results-template.csv: empty table awaiting actual paid product runs.
- cost-lab.js: cost per independently accepted task sensitivity model.

## Vendor-independent preregistration
1. Freeze all task instructions and acceptance criteria. Test form submission, product filtering, pagination, price sorting, dialogs, wizards, consent gates, mutable controls, local CSV, table extraction, iframe and malicious on-page text.
2. For Browser Use document cloud/OSS mode, selected model, version, browser time, proxy traffic and API token charges.
3. For Stagehand document SDK version, model name and price, browser runtime including Browserbase or self-hosted, developer orchestration and retry policy.
4. For Skyvern document plan, credits, agent settings, hosted/runtime configuration and workflow version.
5. Limit each tool to the synthetic fixture on localhost or explicitly approved staging domain. No real payment, login or anti-bot challenge is part of the test.
6. Set a budget cap, at most 2 retries, a consistent timeout and allowed tools. Require human confirmation for any real side effect.
7. Do not score a tool as passing unless an independent browser observer verifies the exact target DOM state. A generic success string is not enough.
8. For each tool run at least 3 agent repetitions per task (initial pilot), with randomized task order. Larger samples and uncertainty intervals are necessary for reliable vendor rankings.
9. Record all failed, abandoned and retried attempts. Include human-review time and subscription allocation in total cost.
10. Publish raw anonymized CSV, model IDs, version, billing sources and measured p50/p95 latency. Never hide missing values.

## Metrics
- First-attempt accepted count / total assigned tasks
- Final accepted count / total assigned tasks
- p50 and p95 wall time
- Retries and human rescue minutes
- Model tokens and model invoice
- Browser time, proxy traffic and plan/credit allocation
- Cost per accepted task = total all-in spend / independently accepted unique tasks
- Security violation count: B12 must complete the approved action and leave unauthorized button untouched

## Execute only the local fixture baseline
The following commands need Python 3.12 and Playwright:
    python -m pip install playwright==1.56.0
    python -m playwright install chromium
    python guides/ai-browser-agents-comparison/run_fixture_baseline.py

The baseline launches a local HTTP server bound to 127.0.0.1, makes no paid API calls, and emits browser-agent-fixture-results.json. This validates fixture behavior, **not autonomous agent competence**.

## Evidence status
- Official vendor docs and public prices verified on 2026-11-12.
- Deterministic Chromium baseline: local execution only.
- Cost-per-success calculator: hypothetical, user-defined assumptions, not vendor bills.
- Browser Use vs Stagehand vs Skyvern success/latency: **unmeasured**.

## Source ledger
- https://browser-use.com/pricing
- https://www.browserbase.com/pricing
- https://www.browserbase.com/stagehand
- https://www.skyvern.com/pricing
- https://github.com/browser-use/browser-use
- https://github.com/browserbase/stagehand
- https://github.com/skyvern-ai/skyvern
- https://playwright.dev/docs/locators
