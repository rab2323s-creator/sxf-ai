# SXF / AI — Hallucination verification demonstration (26 October 2026)

**Research artifact linked from the public guide:** https://sxf.si/guides/why-does-chatgpt-make-things-up/

## The actual procedure
1. SXF assembled eight practical questions drawn from everyday AI use: confidence, citations, search, freshness, quotations, ambiguity, intention, and evaluation incentives.
2. For each question the editorial exercise first *intentionally constructed* a plausible but unsafe unchecked draft to illustrate a recognizable mistake.
3. The editorial audit then read a linked first-party document (OpenAI Help, NIST AI 600-1, or OpenAI's research summary) and wrote a restrained corrected answer.
4. A reproducible test checks that eight distinct records have a source, a fault label, both answer states, and an explicit verification instruction. The test is a structural check only; the researcher's judgment about whether text is supported by its source remains human-reviewed.
5. The guide displays the comparison and a reader-facing verification workflow.

## Why call it a demonstration rather than an AI benchmark?
These are **synthetic editorial answer examples**, not output transcripts captured from a ChatGPT or Gemini API. We did not run an LLM without search and then again with search. Consequently this artifact **must not** be used to infer hallucination rates, reduction in error rates after retrieval, relative model performance, or statistically significant effectiveness. Nothing was concealed; the unchecked texts were chosen to illustrate failure modes. The real observation is that the preselected misleading claims can be checked against primary-source statements and rewritten more narrowly.

## How to reproduce
Read `guides/why-does-chatgpt-make-things-up/research/verification-cases.json` and the three linked primary sources. For each `H01`–`H08`, open its `source`, perform the `check` instruction, and compare the `unchecked` and `verified` language. To verify the source-data structure locally, run:
```
python tests/test_hallucination_guide.py
```
The local test cannot independently attest to website contents or actual AI model behavior.

## Source scope and limitations
- OpenAI Help Center: actual risk examples and user precautions; may be revised by the provider.
- NIST AI 600-1: characterization of confabulation, impact and anthropomorphism risk.
- OpenAI, *Why language models hallucinate* (5 Sep 2025): analysis of guessing and uncertainty under common evaluation conditions.
- The demonstration is English-language, limited to eight handpicked cases and three documents; not a random sample.
- No claims about real-time model accuracy, efficacy of web retrieval, browser behavior, production incident rates or a benchmark denominator.
- The UI marks examples as editorial constructions. This audit establishes a transparent *method of checking claims*, not that an AI model was tested.
