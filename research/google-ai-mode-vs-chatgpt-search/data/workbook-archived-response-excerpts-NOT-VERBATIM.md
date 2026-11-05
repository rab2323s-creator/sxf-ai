# Extracted answer text from the study workbook — NOT a verbatim chat archive

**Provenance warning:** The source workbook uses normalized, edited, or summarized responses in some cases. Do not treat these extracts as raw original AI outputs, and do not use them for a truly blind reassessment until compared with the original messages exported from this conversation. These text values are copied exactly **from spreadsheet archive cells**, not copied directly from the chat transcript.

## T01

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary checked source:** https://www.anthropic.com/research/investigating-vault-particles-with-claude | https://www.anthropic.com/research/investigating-vault-particles-with-claude
- **Original user-supplied response:** Google response (formatting normalized) | ChatGPT response (formatting normalized)
- **Score result:** 100/100 | 100/100
- **Editorial note:** Correct, concise, 3 citations (2 original and 1 secondary). | Correct, more detailed, primary link; additional facts checked.

### Google AI Mode (workbook cell only)

Anthropic reported that prokaryotic and bacteriophage-derived homologs of the major vault protein can assemble into complete vault-like particles. The phage-derived structure (L05) is formed by 96 protein copies and was mapped using cryo-electron microscopy. For more details, read the full report at Anthropic.

Sources:
[1] https://www.anthropic.com/research/investigating-vault-particles-with-claude
[2] https://www-cdn.anthropic.com/76e55fbe85697afbaae16b839498dc00797dec30.pdf
[3] https://superpowerdaily.com/posts/anthropic-uses-claude-to-map-a-96-protein-vault-from-a-bacteria-infecting-virus

### ChatGPT Search (workbook cell only)

On November 4, 2026, Anthropic reported that its biology research team, assisted by Claude, had determined the first 3D structure of a vault particle associated with prokaryotic cells.

Vault particles are large, hollow, barrel-shaped protein structures whose biological function remains unknown. Anthropic demonstrated that proteins from bacteria and bacteriophages (viruses that infect bacteria) can assemble into these structures.

- Protein copies: The phage-derived vault contains 96 copies of a single protein called L05, arranged as 48 copies in each half. By comparison, human vaults contain 78 copies.
- Experimental technique: Cryo-electron microscopy (cryo-EM), which uses electron images of flash-frozen particles to reconstruct their three-dimensional structure.
- Claude's contribution: Claude assisted with protein searches, DNA design, particle purification, and microscopy data processing. The team reduced purification time from approximately three days to 90 minutes and produced an initial structural model in 34 hours.

Original research post: Anthropic, Investigating vault particles with Claude, published November 4, 2026.
https://www.anthropic.com/research/investigating-vault-particles-with-claude?utm_source=chatgpt.com

## T02

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary checked source:** https://www.anthropic.com/research/provable-inference | https://www.anthropic.com/research/provable-inference
- **Original user-supplied response:** Google response (formatting normalized) | ChatGPT response (formatting normalized)
- **Score result:** 100/100 | 100/100
- **Editorial note:** All three requested facts correct; links to Anthropic and secondary sources. | All three requested facts correct; extra precision/quantization details supported by Anthropic.
- **Method note:** No verified exact test timestamp; region not independently captured. | No verified exact test timestamp; region not independently captured.
- **Fact-check note:** Research metrics belong to Anthropic's experimental evaluation, not an independent SXF reproduction. | Research metrics belong to Anthropic's experimental evaluation, not an independent SXF reproduction.

### Google AI Mode (workbook cell only)

In the FlashProve announcement, Anthropic tested a large 400B-parameter mixture-of-experts model called Llama 4 Maverick. [1] https://www.anthropic.com/research/provable-inference [2] https://www.bankless.com/read/news/anthropic-unveils-flashprove-for-proving-which-model-answered-you

- Proof Throughput: The system achieved a throughput of around 110 tokens per second on a single H100 GPU.
- Extra GPU Time: Generating the proofs required roughly 70 to 95 times the GPU time compared to running normal model inference on vLLM. [1] https://dev.to/gabrielanhaia/anthropics-flashprove-proves-which-model-answered-you-at-70-95x-vllms-gpu-time-44ae [2] https://www.anthropic.com/research/provable-inference

You can read the complete publication in Anthropic's research post, Progress on provable inference for large language models:
https://www.anthropic.com/research/provable-inference

If you want to dive deeper into the technical details, I can provide more information on:
- The specific cryptographic techniques (like STARKs) used behind FlashProve.
- How they used the Lean proof assistant for formal verification.
- The differences between in-line vs. post-hoc proving architectures.

Let me know which aspect you would like to explore next!

Google AI Mode disclaimer: AI responses may contain errors.

### ChatGPT Search (workbook cell only)

In its November 2, 2026 announcement, Anthropic reported the following results for FlashProve, its cryptographic proof system for AI inference:

- Model tested: Meta's Llama 4 Maverick, a 400-billion-parameter mixture-of-experts model using 4-bit quantization.
- Proof throughput: Approximately 110 tokens per second on a single NVIDIA H100 GPU.
- Additional GPU time: Roughly 70–95 times as much GPU time as ordinary inference using vLLM (approximately 72× in its standard batch comparison and 94× at the highest tested load).

FlashProve generated proofs of approximately 19 MB per 1,024-token request, allowing users to cryptographically verify that a response came from the claimed model without revealing its weights.

Original source: Anthropic, Progress on provable inference for large language models
https://www.anthropic.com/research/provable-inference?utm_source=chatgpt.com
November 2, 2026.

## T03

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Official source verified:** https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/ | https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/
- **Original user-supplied response:** Google answer (formatting normalized) | ChatGPT answer (formatting normalized)
- **Score result:** 100/100 | 100/100
- **Editorial note:** Four supported updates; one of five omitted, still exceeds at-least-two requested items. | Five supported updates; includes extra related-article thumbnail detail.
- **Method note:** No exact test timestamp or location independently captured. | No exact test timestamp or location independently captured.
- **Fact-check note:** Compared against Google primary publication dated 2026-10-15. | Compared against Google primary publication dated 2026-10-15.

### Google AI Mode (workbook cell only)

On October 15, 2026, Google announced several major updates aimed at enhancing link prominence and source discovery within AI Mode and AI Overviews. [1] https://screpy.com/blog/google-ai-search-links-october-2026/

According to the official Google Search Product Blog, the key changes included:

1. Higher Placement for Inline Links: Google shifted the layout of source links, giving them an increased presence and placing them higher up within the text responses so users can find references earlier in the answer. Sources: https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/ ; https://screpy.com/blog/google-ai-search-links-october-2026/
2. Dedicated Sections for Official Web Pages: They introduced a planned test for a dedicated top section that highlights links to official websites for task-based questions, providing additional utility context. Sources: https://screpy.com/blog/google-ai-search-links-october-2026/ ; https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/
3. Global Expansion of Timely-Article Carousels: Google expanded its news and reporting carousels to more countries and languages, highlighting current articles and giving visibility to a user's Preferred Sources. Sources: https://screpy.com/blog/google-ai-search-links-october-2026/ ; https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/
4. Clickable Creator Profiles on Videos: In AI Mode, Google began testing clickable creator and publisher names on video results, allowing users to open the creator's Search profile directly. Sources: https://screpy.com/blog/google-ai-search-links-october-2026/ ; https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/

Would you like to know more about how these changes affect SEO and traffic measurement in Google Search Console, or how the Preferred Sources feature works?

### ChatGPT Search (workbook cell only)

On October 15, 2026, Google announced five updates to AI Mode and AI Overviews designed to make website links more visible and improve source discovery.

1. More inline links, positioned higher: Google increased the number of clickable links embedded in AI-generated responses and began placing them higher in answers so users could access sources more easily.

2. Prominent links to official websites: Google announced a test of a dedicated section at the top of AI responses highlighting one or two authoritative pages, with explanations of why each link is useful.

3. Expanded news article carousels: Google began rolling out carousels featuring timely news articles to additional countries and languages, highlighting users' selected Preferred Sources.

4. More visible related-article links: Links at the end of some AI responses received larger, more clickable designs and image thumbnails to encourage further exploration.

5. Clickable creator and publisher names: Google began testing links from creator and publisher names in AI Mode video results directly to their Google Search profiles.

These updates included both features being rolled out and experimental features still undergoing testing.

Official Google source: More ways to connect with the web from Search
https://blog.google/products-and-platforms/products/search/updates-ai-mode-overviews-explore-web/?utm_source=chatgpt.com
Published October 15, 2026, by Hema Budaraju, VP of Product Management at Google.

## T04

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary fact-check source:** https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers | https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers
- **Original answers:** Google AI Mode (links preserved) | ChatGPT Search (links preserved)
- **Score result:** 96/100 | 100/100
- **Editorial note:** Application/enforcement dates right; authority distinction imprecise under Art. 88. | Dates and 2027 legacy-model transition verified; narrower enforcement attribution.
- **Independent sources:** EU AI Office Article 88; EU AI Act Service Desk timeline | EU Commission GPAI guidelines; Article 111

### Google AI Mode (workbook cell only)

Under the EU AI Act, the date when obligations for general-purpose AI (GPAI) models entered into application is legally distinct from the date when full regulatory enforcement begins.

According to the official European Commission AI Act Service Desk Implementation Timeline:
https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act

- Application of Obligations: The rules and obligations for providers of general-purpose AI models officially started applying on August 2, 2025 (12 months after the Act entered into force). From this date, GPAI providers were legally required to have compliance frameworks and necessary governance structures in place.
- Enforcement of Rules: The formal powers of the European AI Office and national competent authorities to actively enforce these GPAI rules and levy penalties did not begin until August 2, 2026 (24 months after entry into force).

Sources:
https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/when-does-enforcement-start
https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act

As detailed in the European Commission's Enforcement FAQ, the provisions governing GPAI models only became legally enforceable at the EU and national levels on this latter date, aligning with the activation of the AI Act's overarching market surveillance mechanisms.

### ChatGPT Search (workbook cell only)

As of November 5, 2026, the European Commission confirms two distinct dates for the EU AI Act's general-purpose AI (GPAI) model rules:

Milestone | Date | Meaning
Obligations began applying | August 2, 2025 | Providers placing GPAI models on the EU market became subject to transparency, documentation, copyright, and applicable systemic-risk obligations.
Enforcement began | August 2, 2026 | The European Commission's AI Office gained powers to enforce compliance, including imposing fines for violations.

The Commission explicitly distinguishes these dates in its GPAI guidelines.

Important exception: GPAI models already placed on the EU market before August 2, 2025 have until August 2, 2027 to comply with the applicable obligations.

Official European Commission sources:
1. Guidelines for providers of general-purpose AI models:
https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers?utm_source=chatgpt.com
2. Commission starts enforcing AI Act rules and new transparency requirements on 2 August:
https://digital-strategy.ec.europa.eu/en/news/commission-starts-enforcing-ai-act-rules-and-new-transparency-requirements-2-august?utm_source=chatgpt.com
3. EU rules on general-purpose AI models start to apply:
https://digital-strategy.ec.europa.eu/en/news/eu-rules-general-purpose-ai-models-start-apply-bringing-more-transparency-safety-and-accountability?utm_source=chatgpt.com

Bottom line: The GPAI obligations became applicable on August 2, 2025, but the Commission's enforcement powers began one year later, on August 2, 2026. These are not interchangeable dates.

## T05

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary fact-check source:** https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html | https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html
- **Original answers:** Google AI Mode (links normalized) | ChatGPT Search (links normalized)
- **Score result:** 100/100 | 100/100
- **Editorial note:** Core facts correct; equal-contributor note is a useful documented nuance. | Core facts correct; canonical proceedings link.
- **Independent verification:** https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html | https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html

### Google AI Mode (workbook cell only)

The seminal paper "Attention Is All You Need" appeared in 2017 in the conference proceedings of Advances in Neural Information Processing Systems 30 (NIPS 2017).
Sources: https://papers.nips.cc/paper/7181-attention-is-all-you-need

The first two authors listed on the paper are Ashish Vaswani and Noam Shazeer (notably, all eight authors were marked as equal contributors with a randomized order).
Sources: https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
https://en.wikipedia.org/wiki/Attention_Is_All_You_Need

Original proceedings entry:
https://papers.nips.cc/paper/7181-attention-is-all-you-need

Additional Google Search links were supplied for the conference and each author. The response offered optional follow-ups about Transformer mechanics and remaining authors.

### ChatGPT Search (workbook cell only)

“Attention Is All You Need” was published in 2017 in the proceedings of Advances in Neural Information Processing Systems 30 (NIPS 2017), now known as NeurIPS.

- Year: 2017
- Conference proceedings: Advances in Neural Information Processing Systems 30 (NIPS 2017)
- First author: Ashish Vaswani
- Second author: Noam Shazeer
- Publisher: Curran Associates, Inc.

Original proceedings page: Attention is All you Need — NeurIPS Proceedings (2017)
https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html?utm_source=chatgpt.com

The paper introduced the Transformer architecture, which relies on attention mechanisms rather than recurrent or convolutional neural networks.
Source tag also mentioned research.google.

## T06

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Independent references:** NASA; Schmidt 2025; Stevenson 2025; Hänni 2024 | NASA; Schmidt 2025; Stevenson 2025; Welbanks 2026; Pica-Ciamarra 2026
- **User answer record:** Edited only for formatting and reduced redundant citation tags | Edited only for formatting; unrelated copied T05 answer excluded
- **Score result:** 78/100 | 100/100
- **Editorial note:** Correct verdict, but missed direct peer-reviewed reanalysis citation and overstated two disputed details. | Direct source-backed discussion of contrary findings; no substantive error identified.

### Google AI Mode (workbook cell only)

As of November 5, 2026, viral posts claiming NASA's James Webb Space Telescope has "confirmed life" on K2-18 b are false. Webb observed atmospheric chemistry, not definitive biology.

Google said that methane and carbon dioxide were robustly detected, and that a tentative DMS feature was not a definitive discovery. The answer said DMS is exclusively produced by microbial life and that K2-18 b might be a Hycean world.

For reanalysis, Google summarized an analysis led by Jake Taylor, claiming the faint DMS signal was statistically indistinguishable from noise; it cited NPR rather than directly linking the peer-reviewed paper. It mentioned the original team's roughly three-sigma feature, that more evidence would be needed for discovery, and possible nonbiological DMS mechanisms. It concluded that confirmation of life would need more observations.

User-provided links included:
NASA: https://science.nasa.gov/missions/webb/webb-discovers-methane-carbon-dioxide-in-atmosphere-of-k2-18-b/
NASA: https://science.nasa.gov/blogs/webb/2025/04/18/how-nasas-webb-telescope-supports-our-search-for-life-beyond-earth/
NPR: https://www.npr.org/2025/04/25/g-s1-62610/biosignatures-k2-18b-james-webb-exoplanet-doubt
BBC: https://www.bbc.com/news/articles/c39jj9vkr34o
ScienceDaily: https://www.sciencedaily.com/releases/2026/09/260909005212.htm

Google offered an optional follow-up on JWST spectroscopy and Hycean worlds.

### ChatGPT Search (workbook cell only)

The user-pasted ChatGPT response begins with an unrelated copy of T05; only the T06 answer was evaluated.

Fact-check: False. As of November 5, 2026, NASA's JWST has not confirmed life on K2-18 b.

The response explains transit spectroscopy and notes methane is supported, CO2 was initially reported but has been disputed, and DMS was tentative.

It describes the April 2025 Cambridge team proposal of DMS/DMDS at about three sigma, stressing the team did not claim life.

Independent peer-reviewed reanalyses are named:
Stevenson et al., 2025, The Astronomical Journal: 87.5% of tested retrievals with preferred MIRI processing did not favor DMS/DMDS.
Schmidt et al., 2025, The Astronomical Journal: 60 data treatments and >250 retrievals, robust methane but no reliable CO2 or DMS.
Welbanks et al., 2026, Nature Astronomy: biosignature preference vanishes with wider model space.
Fernández et al., 2026, Astronomy & Astrophysics: supports robust methane and weak, model-dependent CO2.
Pica-Ciamarra et al., May 2026: DMS is comparatively favored in a 661-molecule search, but more observations remain necessary.

Discusses spectral ambiguity, data processing, abiotic chemistry, and unconfirmed habitability, concluding no life or firm biosignature found.

User-provided direct sources include:
NASA: https://science.nasa.gov/missions/webb/webb-discovers-methane-carbon-dioxide-in-atmosphere-of-k2-18-b/
NASA: https://science.nasa.gov/blogs/webb/2024/06/05/reconnaissance-of-potentially-habitable-worlds-with-nasas-webb/
Stevenson: https://doi.org/10.3847/1538-3881/ae0338
Schmidt: https://doi.org/10.3847/1538-3881/ae019a
Welbanks: https://www.nature.com/articles/s41550-025-02730-4
Pica-Ciamarra: https://doi.org/10.3847/2041-8213/ae5dcc
Original study: https://doi.org/10.3847/2041-8213/adc1c8

## T07

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary cross-check sources:** NASA Hubble vs. Webb; STScI Hubble technical status; NASA servicing Q&A | NASA Hubble vs. Webb; NASA Webb orbit; NASA Hubble by the Numbers
- **Answer records:** User-pasted Google response, citations preserved in listed links | User-pasted ChatGPT response, citations preserved in listed links
- **Score result:** 92/100 | 100/100
- **Editorial note:** Both answer the requested comparison; NASA currently lists Hubble at approx 483 km (not 547 km). The absolute 'cannot be physically repaired' claim overstates NASA's more cautious servicing position. | Accurate orbit, bands, and tradeoffs; correctly frames servicing as impractical, not physically impossible.
- **Independent sources:** https://science.nasa.gov/mission/hubble/observatory/hubble-vs-webb/ ; https://www.nasa.gov/universe/how-hardy-is-webb-a-qa-about-the-toughness-of-nasas-webb-telescope/ | https://science.nasa.gov/mission/hubble/overview/hubble-by-the-numbers/ ; https://science.nasa.gov/mission/webb/orbit/

### Google AI Mode (workbook cell only)

NASA’s Hubble Space Telescope and James Webb Space Telescope (JWST) are fundamentally different instruments designed to complement each other rather than replace one another. According to official NASA data:

1. Operational Orbit and Distance
- Hubble: Low Earth Orbit, roughly 340 miles (547 km) above Earth's surface.
- James Webb: Second Sun–Earth Lagrange Point (L2), around 1 million miles (1.5 million km) from Earth.

2. Wavelength Optimization
- Hubble: ultraviolet and visible light, with some near-infrared coverage (0.1–2.5 microns).
- Webb: infrared light, from 0.6–28.5 microns, with some visible red light.

3. Design Trade-Offs
- Hubble's LEO allows servicing and upgrades by astronauts; its environment is warmer and is subject to stray light and Earth's heat.
- Webb must remain exceptionally cold for infrared astronomy; L2 and its sunshield support its thermal design. Google stated that 'Webb is entirely unserviced and cannot be physically repaired' if a structural or mechanical component fails.

Cited links:
https://science.nasa.gov/mission/hubble/observatory/hubble-vs-webb/
https://www.asc-csa.gc.ca/eng/satellites/jwst/webb-hubble-successor.asp
https://www.planetary.org/articles/jwst-versus-hubble
https://spacenexus.us/blog/james-webb-vs-hubble-telescope-comparison
https://pmc.ncbi.nlm.nih.gov/articles/PMC10892943/

Google also offered a follow-up about mirror designs.

### ChatGPT Search (workbook cell only)

According to NASA, the Hubble Space Telescope (HST) and the James Webb Space Telescope (JWST) are complementary observatories.

Comparison:
- Hubble: low Earth orbit around 480 km (300 miles); Webb: halo orbit near Sun–Earth L2 around 1.5 million km (1 million miles).
- Hubble orbital period roughly 95 minutes; Webb about 168 days around L2.
- Hubble primarily ultraviolet and visible, some near-infrared (0.1–2.5 μm); Webb primarily near/mid infrared, some visible red (0.6–28.5 μm).
- Primary mirror: Hubble 2.4 m; Webb 6.5 m.

Tradeoffs:
- Webb's infrared instruments see through cosmic dust and highly redshifted light, but not the ultraviolet region observed by Hubble.
- Webb requires cold temperatures to prevent thermal interference, with the five-layer sunshield protecting it at L2.
- Hubble could be serviced by astronauts, while Webb's L2 location makes conventional astronaut servicing impractical.

NASA sources:
https://science.nasa.gov/mission/hubble/observatory/hubble-vs-webb/?utm_source=chatgpt.com
https://science.nasa.gov/mission/hubble/observatory/?utm_source=chatgpt.com
https://science.nasa.gov/mission/webb/science-overview/science-explainers/webbs-scientific-instruments/?utm_source=chatgpt.com
https://science.nasa.gov/mission/webb/orbit/?utm_source=chatgpt.com

## T08

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary cross-check sources:** Royal Swedish Academy (Oct 7, 2026) | Royal Swedish Academy (Oct 7, 2026)
- **Answer records:** User-pasted Google response; citations retained below | User-pasted ChatGPT response; citations retained below
- **Score result:** 98/100 | 100/100
- **Editorial note:** Broadly correct. Real sentence from press release was placed in quotes as though it were the precise formal award reason. | Correct official award quotation and carefully qualified scientific explanation.
- **Independent sources:** https://www.kva.se/en/news/the-nobel-prize-in-chemistry-2026/ | https://www.kva.se/en/news/the-nobel-prize-in-chemistry-2026/

### Google AI Mode (workbook cell only)

The 2026 Nobel Prize in Chemistry was jointly awarded to Henri B. Kagan and Kenso Soai 'for discoveries that have enabled chemists to drive chemical reactions that lead to homochirality.' The answer linked the official Nobel Prize 2026 Chemistry press release.

It explained Kagan's discovery of non-linear effects in 1986 and Soai's asymmetric autocatalysis, including how a small imbalance between molecular mirror images may amplify until one dominates.

Google cited:
https://www.nobelprize.org/prizes/chemistry/2026/press-release/
https://axial.acs.org/multidisciplinary/nobel-prize-chemistry-2026
https://www.nobelprize.org/prizes/chemistry/2026/popular-information/
Google also linked Google Search cards for both laureates and offered follow-ups on mechanism and origin-of-life chirality.

Editorial note: the quoted explanatory phrase appears in the official press release, but the precise prize motivation is 'for the discovery of non-linear effects and autocatalysis in asymmetric organic synthesis.'

### ChatGPT Search (workbook cell only)

The 2026 Nobel Prize in Chemistry, announced October 7, 2026, was jointly awarded to Henri B. Kagan (Université Paris-Sud, France) and Kensō Soai (Tokyo University of Science, Japan).

It quoted the Royal Swedish Academy's official prize motivation verbatim: 'for the discovery of non-linear effects and autocatalysis in asymmetric organic synthesis.'

The explanation described chiral molecular mirror images, Kagan's amplification mechanism, Soai's asymmetric autocatalysis, practical relevance to selective organic synthesis, and careful limits on claims concerning life's origins.

ChatGPT supplied these primary links:
https://www.nobelprize.org/prizes/chemistry/2026/press-release/?utm_source=chatgpt.com
https://www.kva.se/en/news/the-nobel-prize-in-chemistry-2026/?utm_source=chatgpt.com

## T09

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not provided | Not provided
- **Primary cross-check sources:** NIST e-Handbook section 1.3.5.2 | NIST e-Handbook sections 1.3.5.2 and 7.1.4
- **Answer records:** User-pasted Google response, summarized; sources retained below | User-pasted ChatGPT response, summarized; sources retained below
- **Score result:** 100/100 | 100/100
- **Editorial note:** Substantively correct, direct, and intuitive. The expression '0% or 100% probability' refers to a fixed fact, not a frequentist probability measure for this parameter. | Substantively correct, includes mathematical notation, a calibrated illustration, and an explicit assumption qualifier.
- **Independent sources:** https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm | https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm

### Google AI Mode (workbook cell only)

Google: 'No, the claim is incorrect.' In frequentist statistics the fixed parameter is not a random variable; the procedure has 95% repeated-sampling coverage, but a realized interval either contains the true parameter or not. Uses an extended sticky-note / Ace of Spades card analogy to illustrate why one particular fixed interval cannot be assigned a frequentist probability of 95%. Explicitly cites the NIST Engineering Statistics Handbook. Offers follow-ups on Bayesian credible intervals and sample size.
Source: https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm

### ChatGPT Search (workbook cell only)

ChatGPT: 'No. The claim is incorrect under the frequentist interpretation of a 95% confidence interval.' Gives repeated-sampling coverage interpretation and P_theta(L(X) <= theta <= U(X)) = 0.95 prior to observation. Illustrates 100 independent surveys of a fixed mean of 170 cm: approximately 95 of the intervals contain the parameter in expectation; 5 do not (not an actual simulation). Offers a careful corrected phrasing mentioning model assumptions and distinguishes Bayesian credible intervals.
Sources: https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm ; https://itl.nist.gov/div898/handbook/prc/section1/prc14.htm ; https://online.stat.psu.edu/stat200/Lesson04

## T10

### Workbook archive notes

- **Date received (not necessarily test date):** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not supplied | Not supplied
- **Primary cross-check sources:** Codex original pass@k and tau-bench original pass^k | tau-bench ICLR 2025 paper
- **Answer records:** User-pasted answer summarized; original full response retained in conversation | User-pasted answer summarized; original full response retained in conversation
- **Score result:** 97/100 | 100/100
- **Editorial note:** Correct arithmetic; slight primary-source specificity penalty. Oracle requirement relates to recognizing correct sample, not mathematical event. | Correct arithmetic, precise original citation and task-level caveat.
- **Independent sources:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html | https://arxiv.org/abs/2107.03374

### Google AI Mode (workbook cell only)

Google: all 5 successes = 0.8^5 = 0.32768 (32.77%); >=1 success = 1-0.2^5 = 0.99968 (99.97%). Explains pass^k for repeated reliability and pass@k for any success among k generated samples. States independence, stationary probability, evaluator-oracle availability. Cites OpenAI original Codex paper (pass@k) rather than the original tau-bench source (pass^k).
Original research cited: https://arxiv.org/abs/2107.03374

### ChatGPT Search (workbook cell only)

ChatGPT: pass^5=32.768%; pass@5=99.968%. Distinguishes repeated-run consistency from possibility of any successful sample; explicitly notes that correlated failures/task-to-task heterogeneity invalidate naive use of pooled p^k. Names original tau-bench authors and ICLR 2025 conference. 
Original research cited: https://arxiv.org/abs/2406.12045 ; https://openreview.net/pdf?id=roNSXZpUDN

## T11

### Workbook archive notes

- **Date received:** 2026-11-05 | 2026-11-05
- **Actual test timestamp:** Not supplied | Not supplied
- **Primary verification:** OpenAI official model/pricing; Anthropic pricing | OpenAI official model/pricing; Anthropic pricing
- **Answer records:** User-provided answer summarized; full original remains in conversation | User-provided answer summarized; full original remains in conversation
- **Key citation URLs:** https://developers.openai.com/api/docs/pricing ; https://platform.claude.com/docs/en/about-claude/pricing | https://developers.openai.com/api/docs/pricing ; https://platform.claude.com/docs/en/about-claude/pricing
- **Score result:** 58/100 | 100/100
- **Main issue / merit:** Selected GPT-6 Astra ULTRAFAST rates from a published pricing table despite explicit STANDARD constraint. Its math was correct for its wrongly selected tier. | Correct STANDARD rates for both providers; warned about GPT-6 Astra's >272k-token-per-request long-context surcharge.
- **Independent sources:** https://developers.openai.com/api/docs/models/gpt-6-astra ; https://developers.openai.com/api/docs/pricing | https://platform.claude.com/docs/en/about-claude/pricing
- **Editorial warning:** Scores are preliminary, set by ChatGPT, which is one of the compared products. | Conduct independent blinded second-pass before publishing any winner.

### Google AI Mode (workbook cell only)

GPT-6 Astra input $60/output $300 per 1M; Claude Sonnet 4.6 input $3/output $15 per 1M.

### ChatGPT Search (workbook cell only)

GPT-6 Astra input $10/output $50 per 1M; Claude Sonnet 4.6 input $3/output $15 per 1M.

## T12

### Workbook archive notes

- **Date received:** 2026-11-05 | 2026-11-05
- **Exact test timestamp:** Not supplied | Not supplied
- **Official verification:** Python 3.14 official docs | Python 3.14 official docs
- **Verdict:** False: Python 3.14 did not remove GIL by default. | False: Python 3.14 did not remove GIL by default.
- **Sources cited:** https://docs.python.org/3/howto/free-threading-python.html ; https://docs.python.org/3/whatsnew/3.14.html | https://docs.python.org/3.14/howto/free-threading-python.html ; https://docs.python.org/3.14/howto/free-threading-extensions.html
- **Score:** 100/100 | 100/100
- **Evaluation note:** Correct answer to all specified requirements. Length is not extra credit. | Correct answer to all specified requirements. Pasted code lost line breaks; not graded because runnable code not requested.
- **Official checked source:** https://docs.python.org/3.14/whatsnew/3.14.html | https://docs.python.org/3.14/howto/free-threading-python.html
- **Editorial caution:** Ratings assigned by ChatGPT, which is one of the evaluated tools. | Perform anonymous external review before any strong conclusion.

### Google AI Mode (workbook cell only)

Optional free-threaded build (e.g., python3.14t); standard builds retain GIL.

### ChatGPT Search (workbook cell only)

Optional free-threaded build; --disable-gil; check runtime using sys._is_gil_enabled().

## T13

### Workbook archive notes

- **Date received:** 2026-11-05 | 2026-11-05
- **Exact run timestamp:** Not supplied | Not supplied
- **Claim 1: llms.txt mandatory:** False; Google Search does not use llms.txt for AI Mode/AI Overviews | False; explicitly cites Google Search Central mythbusting guidance
- **Eligibility interpretation:** Googlebot, indexed, snippet eligible; neglected the additional Search Console inclusion setting | Googlebot, indexed, snippet eligible AND Search Console generative-AI inclusion enabled
- **Primary citations:** https://developers.google.com/search/docs/fundamentals/ai-optimization-guide ; https://developers.google.com/search/docs/appearance/ai-features | https://developers.google.com/search/docs/fundamentals/ai-optimization-guide ; https://support.google.com/webmasters/answer/16908024?hl=en
- **Score:** 94/100 | 100/100
- **Editorial notes:** Penalty for omitting 2026 opt-in/out control when explaining all technical eligibility conditions; original myth claims correct. | Complete answer to requested criteria with new official inclusion control; correct sources.
- **Evaluator disclosure:** Scored by ChatGPT, one of the compared tools. | Rescore anonymized before publication.
- **Fact-check sources:** https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | https://support.google.com/webmasters/answer/16908024?hl=en
- **Review rule:** A fixed 14-prompt exploratory sample; scores are editorial and not independent blinded adjudication. | SXF should disclose rubric, answer evidence and sample-selection limitations.

### Google AI Mode (workbook cell only)

Not mentioned

### ChatGPT Search (workbook cell only)

Correctly reports global release Aug 31, 2026; default inclusion, option to exclude

## T14

### Workbook archive notes

- **Date received:** 2026-11-05 | 2026-11-05
- **Exact run timestamp:** Not supplied | Not supplied
- **Rules proposed:** Allow Googlebot/OAI-SearchBot; disallow Google-Extended/GPTBot | Same four-agent rules, correct
- **Google-Extended:** Presented as a ‘crawler’ with model-training focus; incomplete | Correctly describes product-use token, not standalone HTTP crawler; notes Gemini grounding
- **Future shared AI training preference:** Claims joint Google/OpenAI standard and ‘legally recognized’ status without support | Describes Google Oct 30 2026 announcement as upcoming IETF-aligned preference; 2027 planned support
- **Reliability caveats:** Notes no retroactive deletion and ChatGPT-User exceptions | Notes search inclusion not guaranteed; existing data, third parties and user-initiated access unaffected
- **Official source references:** https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers ; https://developers.openai.com/api/docs/bots | https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers ; https://developers.openai.com/api/docs/bots ; https://support.google.com/webmasters/answer/16908024?hl=en ; https://developers.google.com/search/blog/2026/10/ai-training-control
- **Provisional score:** 83/100 | 100/100
- **Primary evidence context:** Google search documents: Google-Extended is robots token; disallowing Googlebot is not equivalent to deindexing. | Google Search Console control and OpenAI bots doc substantiate distinctions.
- **Review status:** Provisional editorial rating; blind second evaluation needed | Provisional editorial rating; blind second evaluation needed
- **Editorial conclusion:** Useful answer and correct robots.txt, but misses nuances relevant to site owners. | More complete explanation with source-supported limitations.

### Google AI Mode (workbook cell only)

Separated correctly

### ChatGPT Search (workbook cell only)

Separated correctly; also mentions server/CDN IP allowlists
