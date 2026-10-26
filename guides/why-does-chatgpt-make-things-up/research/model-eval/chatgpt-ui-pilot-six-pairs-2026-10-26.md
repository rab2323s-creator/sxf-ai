# SXF ChatGPT UI pilot: six paired prompts (provisional field notes)

**Compiled:** 26 October 2026 · **Status:** Six ChatGPT UI answer pairs shared in conversation and checked against first-party sources; NOT the 12-pair API experiment; NOT an estimate of ChatGPT's overall hallucination rate.

## Provenance and setup

A site collaborator pasted **12 ChatGPT response texts for the first six** (E01–E06) of the [previously registered 12-question set](questions.json), two answers per question. The collaborator reported use of the ChatGPT **High** thinking setting. For each pair the first response was taken in a conversation where Search was *not manually selected* (A); the second was submitted as a **Search-enabled** reply (B). The interface's exact underlying model identifier, conversation links, exact response timestamps, request payloads, raw provider JSON and independently verifiable tool traces were not supplied. These are **user-pasted answer texts**: the original records were not fetched directly by SXF's systems.

**CRITICAL:** A response containing a favicon preview or external link is not proof that Search did or did not execute. The A responses contain web-style source cards, so automatic retrieval is plausible. The treatment variable documented here is *manual selection of the Search button*, **not guaranteed absence versus presence of web access**. Nothing below justifies a causal claim about tool effects.

The protocol was initially intended for 12 matched prompts, but collection stopped after the first six at the request of the participant. The sample is **purposive**, predominantly easy first-party documentation lookups, not randomly sampled questions.

## Case-by-case source review

| ID | Prompt target | Arm A: Search not manually selected | Arm B: Search selected | Independent official source |
|---|---|---|---|---|
| E01 | Whether OpenAI acknowledges fabricated studies/citations | Core claim supported | Core claim supported | [OpenAI Help Center](https://help.openai.com/en/articles/8313428) |
| E02 | Whether confidence guarantees correctness | Correct core answer; **quotation issue**: two source statements were blended into a single quotation, not an exact extract | Correct core answer and two traceable short quotations | [OpenAI Help Center](https://help.openai.com/en/articles/8313428) |
| E03 | NIST's label for confident false outputs | Correct: **confabulation**. Source preview also showed third-party nicfab.eu | Correct: **confabulation**. Source preview also showed GitHub | [NIST AI 600-1, §2.2, printed p.6 / PDF p.10](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf#page=10) |
| E04 | Whether all hallucinations are deliberate lies | Correct: NIST's description of false output is not proof of intent | Correct, matching the intended distinction | [NIST AI 600-1, §2.2](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf#page=10) |
| E05 | Whether accuracy-only grading can encourage guessing | Correct description and grounded quotation | Correct description and grounded quotation | [OpenAI, *Why language models hallucinate*, Sep 5 2025](https://openai.com/index/why-language-models-hallucinate/) |
| E06 | First close Pluto flyby and date | Correct **New Horizons / July 14, 2015**, but **incorrect supplemental distance details**, below | Correct main answer and correct distance above surface | [NASA mission](https://science.nasa.gov/mission/new-horizons/); [NASA distance clarification](https://www.nasa.gov/news-release/nasa-announces-updated-television-coverage-media-activities-for-pluto-flyby/) |

## One demonstrable factual mistake — E06, A

The pasted A response first correctly said New Horizons reached about **12,500 km (7,800 miles) above Pluto's surface**. But it then described as a more precise clarification:

> For precision, the closest approach was approximately 12,500 km from Pluto's center, or 7,800 km above its surface.

This second sentence is **wrong and internally inconsistent**. NASA states that the spacecraft passed about **12,500 km / 7,800 miles above the surface**, *not from the center*; it also substitutes kilometers for miles in the “7,800” figure. The B response instead gave the correct above-surface distance (~7,750 miles / ~12,500 km). The original requested question concerned the spacecraft and date, both answered correctly; the mistake appears in an **unnecessary volunteered elaboration**.

This is the defensible editorial lesson from these observations: **a correct headline answer can conceal an inaccurate detail in the supporting explanation**.

## One source-fidelity issue — E02, A

The A response presented a quotation about incorrect outputs and sounding confident as if it were a single verbatim OpenAI sentence. OpenAI actually separates these ideas into distinct sentences; the wording in A smooths over the break. The **substance** was right, but the quotation was **not literally reproduced**. The B response supplied two shorter snippets that appear in the official Help Center document. Treat source support and verbatim quote fidelity as **distinct review questions**.

## What these six cases can and cannot establish

- **Observed:** All 12 user-pasted answers gave a supportable response to their question's *central fact or distinction*. This does NOT mean all 12 answers were flawless.
- **Observed:** One A answer (E06) contained a clear additional factual/unit error; one A answer (E02) contained a quotation-fidelity issue.
- **Not established:** A ChatGPT hallucination *rate*; reproducible model performance; statistically meaningful improvement caused by Search; confirmed no-search baselines; rates for the six untested preregistered cases.
- **Not claimed:** Independently preserved original ChatGPT transcripts, automated provider logs, blinded multi-reviewer scoring, or evidence that the model’s internal version remained fixed.

**How to replicate:** Open [the frozen questions](questions.json), use the [manual capture protocol](chatgpt-plus-manual-protocol.md), save real conversation links/screenshots plus complete answers, explicitly inspect search activity, then independently review exact claims against linked primary sources. The original 12-pair API preregistration and its `PREREGISTERED_NOT_RUN` state remain unchanged; its runner has not been executed.

Editorial observations can be used in the article with these caveats. They must **not** be promoted as a controlled experiment or marketed as a broad reliability statistic.

## Text archive and collection metadata

The **12 separately archived text records** are in [ui-pilot-2026-10-26/responses/](ui-pilot-2026-10-26/responses/); their machine-readable provenance is in [metadata.json](ui-pilot-2026-10-26/metadata.json). All records were reconstructed from the exact text the participant pasted into the SXF research discussion. E01–E03 retain pasted favicon-link markup; E04–E06 omit decorative favicon/image preview lines and explicitly mark omissions, while preserving the substantive answer content. **These are not primary ChatGPT export files or independently verified share links**. UTC times of each original answer were not provided and are recorded as `null`. The compilation date is not to be mistaken for a response timestamp. The participant reported High thinking effort. The A arm is *Search not selected by the participant*, not verified search absence. The B arm is *Search selected*, without independent execution logs.

The article now includes a side-by-side Pluto distance comparison with the official NASA unit/reference-point correction. The original registered 12-pair API study was still never run.
