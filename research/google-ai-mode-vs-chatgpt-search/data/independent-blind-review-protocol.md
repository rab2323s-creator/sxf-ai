# SXF / AI: Independent blind review protocol (v0.1)
**Status 2026-11-05: INDEPENDENT REVIEW PENDING — NOT COMPLETED**

## Existing pilot
- 14 identical English prompts sent manually to Google AI Mode and ChatGPT Search; 28 first-run user-pasted answers.
- Original first-pass scores: 92.57/100 Google and 100/100 ChatGPT, *graded by ChatGPT*. These are self-conflicted, unblinded editorial observations, not independently validated results.
- The public spreadsheet excerpts are partially abridged or normalized; **not verified verbatim**. Precise original query times and original share links were not recorded.

## Source-chain gate
1. Obtain the source conversation via the account holder's **official data export**. Do not make this export public; it can contain unrelated private chats.
2. Preserve the complete UTF-8 answer text from the export and its original message boundary. Two products were sometimes pasted into one user message. Keep the original message, identify the two answer segments manually and verify boundaries.
3. Record source-message ID, content length and SHA-256 for every accepted verbatim answer. If raw content is not verifiable, mark the case **ineligible** for final scoring.
4. Maintain a private key from randomized answer ID A/B to the source product. **Never share it with reviewers before submission.**

## Independent assessment
- Two reviewers with no affiliation to either product, evaluating without original model names or earlier grades.
- Four dimensions, each rated 0 to 5, fractional ratings allowed:
  - Factual accuracy (40 points): key facts, computations, measured claims and lack of material overstatement.
  - Evidence and citation support (30): actual original sources corroborate exact claims.
  - Currency and context (20): effective dates, price tiers, legal scope, uncertainty.
  - Useful communication (10): addresses the original question directly and clearly.
- Total score: 8 × accuracy + 6 × sources + 4 × currency + 2 × usefulness.
- Reviewers keep claim-level source URLs and concise explanations of contested ratings. They may abstain when provenance or evidence is missing.
- Freeze both independent review sheets before unblinding. Document disagreements, resolve with a third reviewer if material, and publish the previous and updated scores separately.

## Limits that should remain attached to every result
This is a purposefully selected 14-query, one-run-per-product *exploratory pilot*. It cannot measure general accuracy or error frequency. Multiple runs with recorded product settings and source timestamps constitute a separate follow-up experiment.

## Public pages and data
- [Main article](https://sxf.si/research/google-ai-mode-vs-chatgpt-search/)
- [Research appendix](https://sxf.si/research/google-ai-mode-vs-chatgpt-search/full-study/)
- [Exact prompt CSV](https://sxf.si/research/google-ai-mode-vs-chatgpt-search/data/prompts.csv)
- [First-pass score CSV](https://sxf.si/research/google-ai-mode-vs-chatgpt-search/data/initial-editorial-scores.csv)

**This page describes a protocol, not a completed independent review.**
