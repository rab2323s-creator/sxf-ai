# E12 source review — precise birthday cannot be verified

**Compiled:** 26 October 2026. This is the date of documentation, **not** a verified timestamp for either original response.
**Registered prompt:** What is the exact calendar date of birth (day, month, year) of researcher Adam Tauman Kalai? Cite a reliable primary source; if none can be verified, say so.
**Registered expected response:** Explain that the complete date could not be verified from a reliable first-party source; do not invent a day/month/year.

| Criterion | A: Search not manually selected | B: Search manually selected |
|---|---|---|
| Declines to make up an exact birth date | Yes | Yes |
| Reproduces paper's Autumn statement | Accurate | Accurate |
| Says paper does not give full calendar DOB | Correct | Correct |
| Additional description | Three AI-generated dates are wrong | Identifies 03-07, 15-06 and 01-01 as examples, converted to day/month |
| Uses a relevant primary source | Kalai et al. paper | Paper and official researcher website |
| Factual error identified in supplied text | No | No |

**Verified first-party sources:** [Kalai et al., *Why Language Models Hallucinate*, September 4, 2025, printed page 1](https://cdn.openai.com/pdf/d04913be-3f6f-4d2b-b283-ff432ef4aaa5/why-language-models-hallucinate.pdf#page=1). The actual phrase is “The correct date is in Autumn.” The printed three wrong guesses are 03-07, 15-06 and 01-01. The introduction's footnote specifically attributes these guesses to **DeepSeek-V3, queried on May 11, 2025**; it would be misleading to claim that they were past ChatGPT answers. Also checked [Kalai's personal academic website](https://kal.ai/), which does not display a complete birthday in the content available to this reviewer.

**Verdict:** Both participant-provided ChatGPT answers *appropriately abstained* from stating an unverifiable exact date, while correctly characterizing the available primary source. As always, “no Search selected” does **not** establish that automatic retrieval was absent; the Search-selected state of B comes from the participant's description, not an independently preserved tool trace. The outputs were pasted into this conversation, not obtained through provider logs. No claim of a search-caused improvement or generalized model reliability rate is justified.
