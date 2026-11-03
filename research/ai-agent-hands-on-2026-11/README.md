# SXF AI Agent Lab — Study notes and limitations (November 3, 2026)

This original exploratory comparison covers **ChatGPT Work, Claude Cowork, and Manus Lite**. Each was given the same synthetic task instructions, once per scenario, making nine runs in total. The operator confirmed all nine runs completed without follow-up instructions. This is a small field test, **not** a production-grade reliability benchmark.

## Reference outcomes

| Scenario | ChatGPT Work | Claude Cowork | Manus Lite |
| --- | --- | --- | --- |
| CSV task triage | Core answer key matched | Core answer key matched | Core answer key matched |
| Excel update reconciliation | Core answer key matched | Core answer key matched | Core answer key matched |
| Official-documentation research | Report produced | Report produced | Report produced |

**CSV test:** overdue tasks T102 and T104; blocked T104; due today T106.

**Excel test (November 3, 2026 at 12:00 UTC):** overdue T201, T205 and T209; blocked T204 and T205; unfinished due today T206 and T210; total remaining work 41 hours against 34 hours capacity, a seven-hour shortage.

**Web-research test:** the agents were asked for a comparison report plus evidence CSV. Deliverable creation is observable; it does not establish exhaustive correctness of the cited claims.

## Limitations

- **Single run per scenario and product:** no repeated-run consistency, statistical reliability or robust rankings.
- Reports were not exhaustively fact-checked. Citation volume is not a quality score.
- Wall-clock duration, credits, monetary cost, fault tolerance, high-risk operations and permission safety were not benchmarked.
- The Manus run used **Lite**. Zapier Agents and Devin were not included.
- The fixtures are synthetic, not actual organizational task data.
- The operator confirmed completion without further prompts; this does not establish unattended production operation.
- Original outputs contain agent-generated claims and recommendations; archival publication is not independent endorsement.

## Evidence archive and provenance

The [SXF study page](https://sxf.si/research/ai-agent-hands-on-2026-11/) links files that are actually present in the public GitHub repository. The local original evidence package includes more files than were initially published to GitHub; that distinction is acknowledged rather than supplying broken download links. Raw binary outputs, when made available separately, should be treated as archival material rather than verified factual references.

## Further SXF research

- [25-test AI Agent Evaluation Checklist](https://sxf.si/guides/ai-agent-evaluation-checklist/)
- [AI Agent Reliability — 12 Metrics](https://sxf.si/research/ai-agent-reliability/)
- [Separate original research-agent trace (October 18, 2026)](https://github.com/rab2323s-creator/sxf-ai/blob/main/guides/what-is-agentic-ai/research-agent-trace-2026-10-18.json)
