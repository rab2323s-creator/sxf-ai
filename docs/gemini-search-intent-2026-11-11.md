# Gemini family search-intent strategy and editorial maintenance

**Canonical hub:** https://sxf.si/models/gemini/

**Evidence:** User-supplied Google Search Console web search export, last 3 months, exported November 11, 2026. The query-filtered `+gemini` report contains 55 unique reported rows, **127 impressions and 0 clicks**. These represent observed visibility only, **not search-volume estimates**. The unfiltered export has 1,000 exported query rows and 352 page rows (export limits apply); do not treat the sum of filtered queries as total site search traffic.

## Primary intent and ownership

- **Family landing page /models/gemini/:** "Google Gemini models", model versions, what Gemini is, which model to use, family feature matrix, model/API distinction, family-level pricing navigation, source-led model-selection criteria. Evergreen H1: `Google Gemini Models — Versions, Pricing, Features & API`; page title: `Google Gemini Models: Versions, API Pricing & Features | SXF / AI`.
- **/compare/gemini-3-8-flash-vs-gemini-3-7-flash/:** "gemini flash 3.8 que mejoró vs flash 3.7" (18 impressions), "gemini 3.7 vs 3.8" (2), pricing comparison (2), "gemini 3.8 vs 3.7" (1). Link with a descriptive anchor; don't rebuild a duplicate full comparison on the hub.
- **/models/gemini-3-8-flash-tts/:** "gemini 3.8 flash tts" (10), "gemini 3.8 flash tts api" (6), variants (3 additional observed impressions). /models/gemini-3-8-flash-lite-tts/ owns Lite TTS.
- **/models/gemini-embedding-001/:** "gemini-embedding-001" (8), "gemini embedding-001 pricing" (3), dimensions variants. **/models/gemini-embedding-2/**: "gemini embedding 2 in seo" (7), "gemini embedding 2 pricing" (3), "gemini-embedding-2 api" (1). Link to Google embeddings documentation, explain incompatible embedding vector spaces.
- **/models/gemini-3-7-flash/** and **/models/gemini-3-6-flash/**: model-specific API/pricing queries (3.7 API: 6; 3.6 API: 6).
- **/models/gemini-4/**: Gemini 4, Carbon, Argon, access status and published family-level pricing; hub includes only dated orientation.
- **/models/pricing/** and **/tools/ai-model-cost-calculator/**: all-provider pricing and cost-calculator demand. The Gemini hub's local calculator is a focused, transparent tool with date-based rates; do not imply benchmark evidence.
- **/providers/google/**: Google provider portfolio. Distinct from the Gemini-only family hub.

Do not force the exact Spanish comparison query into the English H1; keep natural-language English anchors and link to the precise comparison page. Broad model-family keywords are *targets* not empirically validated search demand in the provided dataset.

## Editorial preservation

The ongoing feed generator owns `models/gemini/index.html`. Durable editorial source of truth: `data/model-page-content/gemini-family.html`. The `scripts/gemini_family_page.py` rendering hook injects it and maintains reciprocal links. Update both the source and the generated HTML when making an editorial change; run `python tests/test_gemini_family_seo.py` and the GitHub Actions job. The feed generator must be able to regenerate the page without deleting the authored reference.

Preserve:
- Canonical URL and index/follow policy unless evidence demands otherwise.
- Existing signal timeline and model-change history.
- Useful dated API pricing, limits and citations to Google documentation; recheck time-sensitive facts.
- Browser-based SXF calculator and mobile table handling.
- Visible FAQs matching FAQ schema, without promising Google FAQ rich results.

Avoid: year in evergreen H1, sitewide keyword dumping, duplicating specialist landing pages, unmeasured model rankings, invented Search Console search volumes, artificial dateModified freshness, or redirecting the family canonical to an individual model.

## Review cadence

Recheck verified model IDs, access status, retirement notices and token rates against official Google documentation whenever the model catalog updates or official changes are reported. Retain price effective dates. Review the landing page's own Search Console impressions, CTR and queries after Google has recrawled and enough data has accrued. Consider title changes only when the observed page/query pairing justifies them; Google controls ranking, indexing and displayed title.
