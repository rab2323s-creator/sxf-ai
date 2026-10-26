# SXF ChatGPT Plus manual two-condition capture — no API charges

**Purpose:** Evaluate observable ChatGPT answers on the **same preregistered 12 questions** in `questions.json`, with and without visible web-search use. This is the article-relevant alternative to testing a different brand.

**Status: NOT RUN.** This protocol does **not** claim that any of the 24 expected ChatGPT responses has been collected or reviewed.

## No extra API charge
Use the owner's existing ChatGPT subscription via chatgpt.com, subject to plan and Search usage limits. **Do not use OpenAI API** for this manual path. OpenAI explicitly supports manually selecting ChatGPT Search. The browser UI may also search automatically, so the supposedly no-web arm must be audited carefully. The Github connection alone cannot click ChatGPT on the owner's behalf.

## Capture procedure
1. Read `questions.json` **before** collecting data. Don't modify the registered questions based on observed results. Only paste the text from the `question` field into the new chat.
2. Select the **same visible model / effort choice** for every question and record its UI label. ChatGPT's internal model version may not be exposed; do not claim a frozen model build.
3. For each case E01–E12 open **two fresh conversations**, one per arm, to avoid one answer affecting the other. Keep the questions and any preceding setup identical; preferably **use no setup message**, and paste the question verbatim.
4. **Arm A: no_web.** Do not select Search. Append no tool-specific commands. After receiving the answer, verify whether the UI shows search activity or citations indicating use of external search. **If search happened automatically, mark this case invalid for the no-web comparison** and do not treat it as an ungrounded baseline.
5. **Arm B: with_web.** Select the ChatGPT **Search** tool explicitly from the tool menu, or use `/Search` if available, before pasting the identical question. Verify that it actually searched and inspect displayed sources. If no search happened, label it `search_not_observed`, not a successful search-grounded response.
6. Save the **complete verbatim response and clickable source URLs** for each arm separately, along with UTC timestamp, visible model choice and search-use observation. Copy plain text into a local file named `E01__no_web.txt`, `E01__with_web.txt`, and so on. Supplement with screenshots of search/source indications when helpful. Do not edit the original answer or publish private conversation data without inspection.
7. Fill `chatgpt-plus-capture-template.csv` with the 24 corresponding entries and file names. Do not fill the review outcome just because a response sounds convincing.

## Mandatory blinded-to-condition source review
Give the raw answers (ideally without condition labels) and the ground-truth primary URLs from `questions.json` to a reviewer. Independently open first-party sources and compare exact claims, citations, dates and quotations. For every answer record:
- `correct`: central factual claims verified, without invented details.
- `incorrect`: false or fabricated central claim.
- `abstained`: explicit justified uncertainty / refusal to guess.
- `mixed_or_unclear`: factual mix or unresolved ambiguity.
- `not_reviewed`: incomplete assessment.

For each claimed citation, check **both** whether the page exists and whether the cited passage supports the precise claim. Record the source passage and the reviewer’s rationale. Count only valid paired cases in a narrowly described outcome table. Do not represent small purposively chosen samples as general ChatGPT hallucination rates.

## Study-design limitations
- Consumer ChatGPT may automatically search; a "no search" instruction is not equivalent to proof of no retrieval.
- The same displayed model name does not guarantee the same internal model version or tool pipeline. Search mode can change behavior beyond source retrieval.
- There are no API request IDs or machine-verifiable raw provider JSON. Treat ChatGPT UI captures as **observable interface tests**, weaker-controlled than pinned API calls.
- Answers can change between runs and with account settings, rate limits, tool availability, time and location.
- Original SXF's eight-case *editorial demonstrations* in the article are not model outputs and do not become measured evidence because this protocol exists.
- The only publishable finding before captured, verified transcripts is that the **protocol has been defined**.

After a completed real run, add the date, observable model label, answer transcripts, link checks, exclusions, counts, and scope of the result to the article. If too many cases lack a verifiable no-web baseline, report a **descriptive search-enabled case study** rather than a valid paired experiment.
