# SXF / AI — Marketing Agent Lab evidence archive

**Study date:** November 4, 2026. **Fixture:** fictional, six marketing channels, baseline and current 7-day windows. **Platforms actually run:** Zapier Agents and Make AI Agent. No live ad account, CRM, publishing tool, or Search Console property was connected for the campaign benchmark.

## Files
- `campaign-fixture.csv`: the 12 input rows; no real business performance information.
- `test03-prompt.txt`: the campaign anomaly prompt. The same logical task and thresholds were used on both platforms.
- `test03-gold.json`: answer key computed from the source values without rounding intermediate metrics.
- `run-results.json`: operator-transcribed JSON outputs from six Test 03 and two Test 04 runs. The full ancillary reasoning text is **not** retained as a byte-for-byte log. Do not call these provider-exported logs.
- `test03-scorecard.csv`: confusion-matrix components for the six individual runs.
- `test04-prompt.txt`: the marketing diagnostic recommendations task.
- `seo-audit-notes.md`: qualitative note about separate Zapier SEO tests; **not** counted in the campaign benchmark.

## Calculations
CTR = clicks / impressions; CPC = spend / clicks; CVR = conversions / clicks; ROAS = revenue / spend. Compare (current / baseline - 1) * 100 on raw, unrounded values. For Organic Search (zero spend), exclude CPC and ROAS. Thresholds: relative CTR drop >=10%, CPC rise >=30%, CVR drop >=25%, ROAS drop >=40%. Six true flags across three channels per test run.

Test 03 aggregate (three repeated identical-input runs each): Make TP=17, FP=0, FN=1, precision=17/17=100%, recall=17/18=94.44%; Zapier TP=17, FP=2, FN=1, precision=17/19=89.47%, recall=17/18=94.44%. Exact set match = 2/3 each. This is descriptive arithmetic on 3 non-independent repeats, **not** an uncertainty-calibrated estimate of platform reliability.

Test 04 is ONE run per platform, qualitatively reviewed on: 3 relevant channels, 6 triggered metrics, correct priorities (HIGH for ROAS drop >=40%, else MEDIUM), exactly two diagnostic checks per flagged channel, explicit unverified hypotheses, format compliance and numerical accuracy. It is NOT a causal or intervention study.

### Important limits
- No live workflows or tool-executing autonomous campaign actions were evaluated.
- No repetitions with different datasets or independent reviewers; the source fixture was reused. Model sampling/configuration may differ by platform.
- Latency values are visible *reasoning seconds* for Make, not measured end-to-end latencies, and Zapier latency was not captured. Make credits reflect only the runs where the operator supplied a number.
- The user-supplied transcripts are the evidence basis; full original logs/screenshots are not archived here. Do not imply third-party verification.
- This is not a benchmark of underlying foundation models, market share, safety, total cost of ownership, or commercial performance.
- Findings are dated; product names, prices and beta terms may change.

### Fixed numeric reference
Nonbrand Search: CTR 4.00% -> 3.6585366% (relative -8.5366%, *no* CTR alert); CPC $1.20 -> $1.90 (+58.3333%); CVR 3.00% -> 2.00% (-33.3333%); ROAS 2.50 -> 1.0526316 (-57.8947%). Meta Prospecting: CVR 3.00% -> 1.3333% (-55.5556%); ROAS 2.40 -> 1.00 (-58.3333%). Organic Search CTR 8.00% -> 7.00% (-12.5%); CVR 4.00% -> 3.60% (-10%, *no* CVR alert).

**Linked article:** https://sxf.si/guides/best-ai-agents-for-marketing/  
**Research page:** https://sxf.si/research/ai-marketing-agent-lab-2026-11/  
**Editorial policy:** https://sxf.si/about/#method
