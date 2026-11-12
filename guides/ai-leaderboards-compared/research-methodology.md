# SXF / AI — AI leaderboards compared (2026): editorial and replication method

**Published:** 2026-11-13. **Verified primary sources:** Artificial Analysis v5.0.1 official methodology, Artificial Analysis v4.3 and v5 launch notes, Arena ranking/uncertainty/Bradley–Terry documentation, Arena factuality/Agent Mode information, LiveBench 2.0 public leaderboard, original LiveBench codebase.

## Original research components

1. **Artificial Analysis methodological transition audit** (`aa-index-transition.json`). It documents the provider's v4.3 and v5 index release sources and known comparison-breaking changes. Count of evaluations, category weights, private/held-out weight and named additions/removals are copied from primary methodological records. These counts are *not* model performance measurements. Notes: v4.3 vs v5.0.1 comparison uses the September 7 and October 27 dated launch documents, plus the current as-reviewed v5.0.1 method.
2. **Twelve authored claim fixtures** (`sxf-leaderboard-claim-audit.csv`). An explicitly constructed educational negative/positive control set covering metric-unit mismatch, task mismatch, methodology break, model variant mismatch, confidence interval uncertainty, scope overreach and operational costs. Nine were deliberately written to be unsafe and three were deliberately constructed to be conditionally comparable. **9/12 is not a measured prevalence of benchmark misuse in the industry.**
3. **Offline interactive case inspector** (`leaderboards.js`). The UI mirrors twelve fixture claims. It performs no network requests, analytics, LLM inference or hidden grading.
4. **Reproducible Python check** (`audit_claims.py`). Uses the standard library to validate fixture keys, classification consistency, dates/weights and version counts; no third-party dependencies.

Run `python guides/ai-leaderboards-compared/audit_claims.py` to validate the files and `python tests/test_ai_leaderboards_compared.py` for the source-to-page contract.

## Key editorial claims

- Artificial Analysis v5.0.1: nine evaluations, four categories weighted 25% each, indexed normalization. The company said 60% held-out/private evaluation weight at v5 launch. Citation: https://artificialanalysis.ai/methodology/intelligence-benchmarking and https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5/.
- v4.3 had ten evaluations, 30% agents, 20% coding, 30% general, 20% scientific and 45% private/held-out. Citation: https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3.
- Arena standard Text comparison: anonymous pairwise preferences with Bradley–Terry, confidence intervals and rank spread. Arena Agent mode and factuality are distinct methods, not interchangeable. Citations: https://arena.ai/faq/ and https://arena.ai/blog/ranking-method and the linked support docs.
- LiveBench 2.0 public site: long-horizon deliverable suites, version shown as November 6, 2026, published success economics; distinguish it from earlier LiveBench research. Citation: https://livebench.ai/.

## Scope and limits

This report **does not** create a single model ranking from unrelated scales, calculate model improvements from version jumps, collect real Arena voting data, download hidden evaluation sets or measure AI model quality. Read provider original scoreboards for the latest per-model positions. The 12-case fixture is an independent interpretive teaching and quality-assurance device, not a physical experiment or a measured vendor benchmark.

Commercial transparency: no vendor paid SXF for a listing; no monetized links or invented AggregateRating/Review data. A high rank on Google is not guaranteed.
