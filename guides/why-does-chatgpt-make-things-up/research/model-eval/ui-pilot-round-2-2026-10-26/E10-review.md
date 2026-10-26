# E10 source review — search does not eliminate hallucinations

**Compiled:** 2026-10-26
**Status:** provisional two-answer source review, second UI pilot in progress.
**Registered prompt:** Does OpenAI's research on hallucinations say that adding search eliminates all hallucinations?
**Registered expected response:** No.

| Check | A: Search not manually selected | B: Search manually selected |
|---|---|---|
| Rejects search-as-cure-all | Correct | Correct |
| Search can reduce hallucinations | Supported | Supported |
| Errors may remain despite retrieval | Supported | Supported |
| Primary-source quote fidelity | No direct quotation claimed | Exact: “Search (and reasoning) are not panaceas.” |
| Factual error found | None identified | None identified |

**Primary source verified:** [OpenAI, *Why Language Models Hallucinate*, PDF, section 5, printed page 15 (PDF page 15)](https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf#page=15). The source says that multiple studies find search-augmented models may reduce hallucinations, while binary grading still rewards guessing when search fails to deliver a confident answer; search may not help intrinsic errors such as miscalculations. [OpenAI's September 5, 2025 research summary](https://openai.com/index/why-language-models-hallucinate/) likewise says accuracy cannot reach 100% for every real-world question regardless of search and reasoning capabilities.

The B answer's **page 15 citation is correct by printed-page number**; the PDF uses the same printed page at the page viewer's page 15 (zero-index 14). Research paper cover is dated September 4, 2025 whereas the OpenAI public summary is dated September 5, 2025; participant responses referred to the **September 5 public research release**, which is valid.

**Verdict:** Both participant-pasted answers are substantively correct, with a traceable literal quotation in B. As with E07–E09, no underlying model build ID, original timestamps or tool-call logs were supplied. Not manually selecting Search in A is **not proof of no automated browsing**; B was Search-selected by user report, not independently verified. These two answers do not prove a causal benefit from Search and must not be used as a population hallucination-rate estimate.
