# SXF / AI — Marketing Agent Lab evidence archive

**Study date:** November 4, 2026. **Fixture:** fictional, six marketing channels, baseline and current 7-day windows. **Platforms actually run:** Zapier Agents, Make AI Agent, n8n AI Agent (with OpenAI `gpt-4.1-mini`), and Dify Agent (configured with a model labeled `Gemini 3.5 Flash`). No live ad account, CRM, publishing tool, or Search Console property was connected for the campaign benchmark.

## Files
- `campaign-fixture.csv`: the 12 input rows; no real business performance information.
- `test03-prompt.txt`: the campaign anomaly prompt. The same exact benchmark prompt and dataset were used across the four tested environments, according to the operator-guided test record.
- `test03-gold.json`: answer key computed from the source values without rounding intermediate metrics.
- `run-results.json`: operator-transcribed JSON outputs from twelve Test 03 and four Test 04 runs. The full ancillary reasoning text is **not** retained as a byte-for-byte log. Do not call these provider-exported logs.
- `test03-scorecard.csv`: confusion-matrix components for the twelve individual runs.
- `test04-prompt.txt`: the marketing diagnostic recommendations task.
- `seo-audit-notes.md`: qualitative note about separate Zapier SEO tests; **not** counted in the campaign benchmark.

## Calculations
CTR = clicks / impressions; CPC = spend / clicks; CVR = conversions / clicks; ROAS = revenue / spend. Compare (current / baseline - 1) * 100 on raw, unrounded values. For Organic Search (zero spend), exclude CPC and ROAS. Thresholds: relative CTR drop >=10%, CPC rise >=30%, CVR drop >=25%, ROAS drop >=40%. Six true flags across three channels per test run.

Test 03 aggregate (three repeated identical-input runs each): Make TP=17, FP=0, FN=1, precision=17/17=100%, recall=17/18=94.44%, exact 2/3; Zapier TP=17, FP=2, FN=1, precision=17/19=89.47%, recall=17/18=94.44%, exact 2/3; n8n TP=18, FP=6, FN=0, precision=18/24=75%, recall=18/18=100%, exact 0/3; Dify TP=18, FP=0, FN=0, precision=18/18=100%, recall=18/18=100%, exact 3/3. Each n8n run yielded the same six valid alert codes plus two false alerts: Nonbrand CTR and Organic CVR. This is descriptive arithmetic on 3 non-independent repeats, **not** an uncertainty-calibrated estimate of platform reliability.

Test 04 is ONE run per platform, qualitatively reviewed on: 3 relevant channels, 6 triggered metrics, correct priorities (HIGH for ROAS drop >=40%, else MEDIUM), exactly two diagnostic checks per flagged channel, explicit unverified hypotheses, format compliance and numerical accuracy. n8n returned the three correct channels plus an unwarranted Meta Retargeting entry, three nonqualifying metric claims (Nonbrand CTR, Organic CVR, Meta Retargeting CVR), and HIGH instead of MEDIUM for Organic Search. n8n's checks and explicit unverified labels met those structural requirements; the unsupported numerical evidence did not. Dify returned the three qualifying channels only, six supported alert metrics with accurate rounded numerical changes, correct HIGH/HIGH/MEDIUM priorities, exactly two checks per channel and clearly marked hypotheses; its operator-pasted response was JSON-only. It is NOT a causal or intervention study.

### Important limits
- The n8n workflow was manually executed using Manual Trigger → AI Agent → OpenAI Chat Model (`gpt-4.1-mini`) in n8n Cloud. Dify used the UI Agent configuration with a model labeled `Gemini 3.5 Flash` and operator-pasted Preview chat results; the agent had no connected skills/tools/data sources documented. No tool-using autonomous actions or live campaign integrations were evaluated.
- No repetitions with different datasets or independent reviewers; the source fixture was reused. Model sampling/configuration may differ by platform. The n8n and Dify runs used user-selected named models, but other providers' versions/settings were not equivalently captured. No platform-level causal attribution or cross-provider model-equivalent comparison is justified.
- Latency values are visible *reasoning seconds* for Make, not measured end-to-end latencies, and Zapier latency was not captured. Make credits reflect only the runs where the operator supplied a number.
- The user-supplied transcripts are the evidence basis; full original logs/screenshots are not archived here. Do not imply third-party verification. The n8n Test 03 operator pasted an output table containing Markdown JSON fences; whether the fences originated from the AI response or n8n's display/copy formatting is unknown, so JSON-only compliance is not scored conclusively for these runs. The n8n Test 04 paste was plain JSON. All three Dify Test 03 pastes and its Test 04 paste were presented as standalone JSON; there are no independently exported logs, model-call parameters, or timestamps for those executions.
- Dify is an additional hands-on lab observation, outside the eight-product editorial shortlist of the companion guide; it is not a ninth product profile in that ranked-by-use-case shortlist. Numerical scoring compares responses on one fixture, not underlying automation platforms under controlled model-equivalent conditions.
- This is not a benchmark of underlying foundation models, market share, safety, total cost of ownership, or commercial performance.
- Findings are dated; product names, prices and beta terms may change.

### Fixed numeric reference
Nonbrand Search: CTR 4.00% -> 3.6585366% (relative -8.5366%, *no* CTR alert); CPC $1.20 -> $1.90 (+58.3333%); CVR 3.00% -> 2.00% (-33.3333%); ROAS 2.50 -> 1.0526316 (-57.8947%). Meta Prospecting: CVR 3.00% -> 1.3333% (-55.5556%); ROAS 2.40 -> 1.00 (-58.3333%). Organic Search CTR 8.00% -> 7.00% (-12.5%); CVR 4.00% -> 3.60% (-10%, *no* CVR alert).

**n8n Test 04 reference correction:** Meta Retargeting CVR 6.00% -> 98/1640 = 5.97561% (relative -0.4065%, not -26.63%), so no alert. Organic Search CVR 4.00% -> 3.60% is -10%, not -25%. Organic Search's only qualifying alert is CTR -12.5%; its priority is MEDIUM. The output's Nonbrand CTR -8.56% differs slightly from the unrounded -8.5366% and remains below the alert threshold. Numerical reporting may contain rounding errors independently of alert classification.

**Dify Test 04 reference confirmation:** Nonbrand CPC +58.3333%, CVR −33.3333%, ROAS −57.8947%; Meta Prospecting CVR −55.5556%, ROAS −58.3333%; Organic Search CTR −12.5%. The Dify operator-pasted response reported these six events accurately to two decimals, used priorities HIGH/HIGH/MEDIUM, and did not include an unqualified channel. Its suggested causes remain hypotheses, not established facts.

**Linked article:** https://sxf.si/guides/best-ai-agents-for-marketing/  
**Research page:** https://sxf.si/research/ai-marketing-agent-lab-2026-11/  
**Editorial policy:** https://sxf.si/about/#method
