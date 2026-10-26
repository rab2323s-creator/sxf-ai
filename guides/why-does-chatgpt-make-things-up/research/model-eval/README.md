# SXF paired ChatGPT hallucination study — registered, NOT RUN

**Status on 26 October 2026:** the exact 12 questions and source checklist are frozen in `questions.json`, but no model API calls have been run as part of this study. The separate eight-case editorial audit on the article is **not** model output and remains correctly labelled.

## Question and comparison

Can live web search change the **observable factual reliability** of one model on twelve hand-picked real-world questions? Compare **the same requested API model** for each prompt:

- **No web:** Responses API request with no tools.
- **With web:** same system prompt and question, web-search tool enabled and required. The response must contain a `web_search_call`; otherwise that pair is invalid.

The order is balanced by question number (even questions web-first, odd baseline-first). Both arms have an identical prompt telling the model it may say it cannot verify. The raw API responses, exact request arguments, UTC timestamp, response model ID, latency and web-search traces are stored on disk. **No synthetic example counts as a model answer**.

## Why these questions?

SXF checked first-party OpenAI, NIST, NASA, United Nations and Nobel Prize materials in advance and registered twelve answer keys. This **is not a random sample**: it probes fabricated references, confidence, misread entities, known historical facts, future events and cases where abstention is appropriate. The key is not included in the model prompt.

## Run (requires explicit API access)

The experiment needs an OpenAI API key in your own environment (`OPENAI_API_KEY`) with available usage quota. A ChatGPT Plus subscription **does not** provide an API key. The OpenAI Responses API may incur model and web-search usage charges.

```bash
python scripts/run_hallucination_model_eval.py --dry-run
export OPENAI_API_KEY="..."     # Do not check keys into Git
python scripts/run_hallucination_model_eval.py --acknowledge-api-costs
```

The default model is `gpt-4.1-mini` if available to the API account. The runner uses `store=false`, a 130-second timeout, and writes under `guides/why-does-chatgpt-make-things-up/research/model-eval/runs/<UTC timestamp>/`. You can override `--model` to a supported *same model for both arms*; both resolved model IDs are recorded. If a call fails, keep the partial directory but do not report the study complete.

For a no-secret local integrity check, run:
```bash
python tests/test_hallucination_model_eval.py
```

## Human scoring — mandatory before publishing findings

Each full `responses/*.json` is a **raw API response** and the associated `requests/*.json` contains the actual prompt and options (but not credentials). A reviewer should make one record per question per arm, including:

- `correct`: all checkable claims supported and no invented details.
- `incorrect`: a central checkable claim is false or fabricated.
- `abstained`: the system declined to supply an unsupported answer; see whether the task was truly unanswerable.
- `mixed_or_unclear`: partial correctness or unresolvable claim requiring separate notes.
- `not_reviewed`: default; **never included in a reported count**.

Check cited URLs actually exist and that the stated proposition is supported by the passage, not merely by the title. Note fresh-data availability and any caveats. For E11 and E12, an unsupported concrete answer is a hallucination risk; a careful admission of uncertainty is preferable. The `with_web` arm must show tool use and source support; a URL by itself is not proof.

The script generates `reviews.csv` with empty human labels. No results dashboard or success percentages are generated until all labels are reviewed and the raw paired run passes structural checks. A single reviewer is a limitation; a second blinded reviewer is preferable.

## Bias and scope limitations

- Only **12 purposively selected English questions**, mostly factual, are sampled.
- Single completions per condition; the experiment **cannot establish general accuracy**, superiority, statistical significance or real-world hallucination rates.
- Search results are volatile; record execution time and exact model ID. Web access may change source rankings.
- There is no independent control over OpenAI model internals, hidden reasoning or training cutoff.
- Search can help with grounding but cannot guarantee a true answer.
- This protocol is not a claim of actual results, even if it is linked from SXF's guide.

Primary sources and reviewer targets are part of `questions.json`. The files and prompts are permissively inspectable; after actual authenticated runs, share a checked artifact and human review before adding findings to the article.
