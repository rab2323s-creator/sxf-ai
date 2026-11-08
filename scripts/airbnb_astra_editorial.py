"""Airbnb GPT-6 Astra reviewed news editorial; stable across scheduled builds."""
import json
import re
from html import escape
CANONICAL = "https://sxf.si/signals/airbnb-widens-access-to-gpt-6-astra-and-openai-frontier-models-ea9ea2f/"
TITLE = "Airbnb & GPT-6 Astra: OpenAI Partnership, Results | SXF"
H1 = "Airbnb and GPT-6 Astra: OpenAI Partnership, AI Tools & Results"
DESCRIPTION = "Airbnb expands GPT-6 Astra via OpenAI API and AWS Bedrock. Explore the 80% feature-shipping claim, Codex agents, real use cases and SXF's analysis."
SOURCES = ["https://news.airbnb.com/expanding-access-to-openai-frontier-models-including-gpt-6-astra","https://openai.com/index/airbnb-gpt-6-astra/","https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-astra.html","https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html","https://developers.openai.com/api/docs/models","https://openai.com/index/gpt-6-astra/","https://developers.openai.com/api/docs/guides/your-data","https://www.nist.gov/itl/ai-risk-management-framework"]
KEYWORDS = ["Airbnb GPT-6 Astra","Airbnb OpenAI partnership 2026","Airbnb uses GPT-6","Airbnb OpenAI models","Airbnb Amazon Bedrock","Airbnb Codex remote coding agents","Airbnb AI feature productivity 80%","GPT-6 Astra enterprise adoption","Airbnb GPT-5.6 Sol Terra Luna","Airbnb OpenAI APIs"]
FAQ = [["What did Airbnb and OpenAI announce in September 2026?","A September 23 agreement expands access to GPT-6 Astra and other OpenAI frontier models for Airbnb engineering and product-development teams via OpenAI APIs and Amazon Bedrock."],["How does Airbnb use GPT-6 Astra?","The companies report difficult bug investigations, system-design work and brainstorming. OpenAI also describes one strategic-document case with fewer revision passes."],["Did GPT-6 Astra cause Airbnb to ship 80% more features?","No causation was established. Airbnb's CTO reported roughly 80% more features shipped year on year and described OpenAI models as a key part of developer tooling, without isolating Astra's impact."],["What does the 3–4 versus 20+ passes claim mean?","OpenAI reports one user's experience completing a strategic-document task in three to four passes with Astra versus over twenty with other models. It is not a controlled reproducible benchmark."],["Does Airbnb use Codex and remote AI agents?","Yes. Airbnb describes an internal coding platform creating remote AI agents powered by Codex and models such as GPT-5.6 Sol, Terra and Luna."],["Why is Amazon Bedrock part of the agreement?","Airbnb says AWS is its preferred cloud provider and its expanded model access includes Amazon Bedrock as well as OpenAI APIs. Specific request routing and costs were not disclosed."],["Is GPT-6 Astra running Airbnb search, fraud detection and support?","The statements confirm OpenAI-model uses in these product areas, but do not say all use cases or model-assisted decisions use GPT-6 Astra."],["Is the deal's price or ROI public?","No contract value, model-specific return on investment or controlled enterprise performance comparison is published in the two company announcements."]]
BRIEF = r'''<section class="signal-layout shell"><article class="signal-brief"><p class="eyebrow">SXF VERIFIED ENTERPRISE AI BRIEF · NOVEMBER 8, 2026</p>
<p class="signal-summary"><strong>Airbnb expanded access to OpenAI GPT-6 Astra</strong> for engineering and product development under an agreement announced September 23, 2026. The company already used Codex-powered remote coding agents and GPT-5.6 models. The expansion adds broader access through OpenAI APIs and Amazon Bedrock. Airbnb's CTO reported <strong>roughly 80% more features shipped year over year</strong>, but no published experiment isolates GPT-6 Astra's causal contribution.</p>
<div class="signal-context"><span>WHAT IS DOCUMENTED</span><p>Airbnb describes engineering uses in debugging and system design. OpenAI describes one non-coding example needing 3–4 revision passes with Astra versus 20+ with other models. This is an individual observation, not a general benchmark.</p></div>
<div class="signal-context"><span>SXF INTERPRETATION</span><p>Frontier-model access matters when outputs survive testing, review, deployment and operational monitoring. The important question is whether accepted work improves without additional defects, costs or security exposure.</p></div></article>
<aside class="source-card"><span class="source-card-label">PRIMARY SOURCES</span><strong>Airbnb + OpenAI</strong><p>Published September 23, 2026. Product facts and editorial judgments are separately identified.</p><a href="https://news.airbnb.com/expanding-access-to-openai-frontier-models-including-gpt-6-astra" target="_blank" rel="noopener noreferrer">Airbnb announcement ↗</a><p><a href="https://openai.com/index/airbnb-gpt-6-astra/" target="_blank" rel="noopener noreferrer">OpenAI announcement ↗</a></p><p><small>Checked November 8, 2026; no SXF independent benchmark claimed.</small></p></aside></section>'''
BODY = r'''<section class="signal-deep-dive shell ab-astra" data-sxf-airbnb-astra="2026-11-08" aria-labelledby="ab-overview">
<div class="intel-section-head"><div><p class="eyebrow">SXF / ORIGINAL ENTERPRISE AI ANALYSIS</p><h2 id="ab-overview">Airbnb, GPT-6 Astra and OpenAI: what the partnership actually demonstrates.</h2></div><span>Verified November 8, 2026</span></div>
<p class="ab-deck">On September 23, 2026, <strong>Airbnb and OpenAI announced a new agreement</strong> giving Airbnb's engineering and product-development teams wider access to <strong>GPT-6 Astra and frontier AI models</strong> through OpenAI APIs and Amazon Bedrock. Searchers looking for <strong>“Airbnb GPT-6 Astra,” “Airbnb OpenAI partnership,”</strong> and <strong>“Airbnb AI productivity”</strong> should know this is an internal enterprise tooling expansion, not a new publicly announced travel assistant. The key facts are in <a href="https://news.airbnb.com/expanding-access-to-openai-frontier-models-including-gpt-6-astra" target="_blank" rel="noopener noreferrer">Airbnb's official release</a> and <a href="https://openai.com/index/airbnb-gpt-6-astra/" target="_blank" rel="noopener noreferrer">OpenAI's matching account</a>. Below, SXF separates reported facts from analysis and the results that have not been independently demonstrated.</p>
<div class="ab-facts"><div><span>ANNOUNCED</span><strong>September 23, 2026</strong><small>Both companies</small></div><div><span>AI MODEL</span><strong>GPT-6 Astra</strong><small>Access expansion for internal teams</small></div><div><span>ACCESS ROUTES</span><strong>OpenAI API + AWS Bedrock</strong><small>Internal allocation not published</small></div><div><span>PRODUCTIVITY CLAIM</span><strong>~80% more features</strong><small>Year-over-year company statement, not Astra-only causation</small></div></div>
<nav class="ab-toc" aria-label="Jump to section"><strong>Explore this analysis</strong><a href="#ab-agreement">Agreement</a><a href="#ab-codex">Codex agents</a><a href="#ab-80">80% claim</a><a href="#ab-passes">3–4 vs 20+</a><a href="#ab-marketplace">Use cases</a><a href="#ab-api">API and AWS</a><a href="#ab-sxf">SXF framework</a><a href="#ab-privacy">Governance</a><a href="#ab-faq">FAQ</a></nav>
<section id="ab-agreement"><h2>What changed in Airbnb's OpenAI agreement?</h2>
<p>Airbnb announced broader internal access to frontier models, <strong>including GPT-6 Astra</strong>, for software engineers and product teams. Its preferred cloud provider is AWS; the new access routes include both the <strong>OpenAI API and Amazon Bedrock</strong>. The companies did not reveal the contract price, exact number of users, usage volumes, migration schedule or which departments will adopt Astra first. These omissions matter when a press release is used to justify a technology investment elsewhere.</p>
<p>This is not Airbnb's first AI developer initiative. Its engineers already used an internal AI assistant or tooling platform supporting software development and remote agents built on Codex and GPT-5.6 Sol, Terra and Luna. The new agreement broadens access rather than beginning model-powered engineering from zero. It also does not establish that every Airbnb consumer experience is now served by GPT-6 Astra.</p>
<h3>Is this a public ChatGPT or Airbnb product launch?</h3>
<p>No new traveler-facing GPT-6 Astra product, special ChatGPT subscription for hosts or public model picker was announced. It is a commercial and engineering access expansion. That distinction is central to the intent behind searches about the deal: the business value may lie in faster internal creation of features rather than in a model surfaced by name to guests.</p></section>
<section id="ab-codex"><h2>How does Airbnb use Codex, GPT-6 Astra and remote coding agents?</h2>
<p>The companies describe early Astra applications in <strong>hard-bug investigation, system design and brainstorming engineering approaches</strong>. Airbnb's internal AI tooling also supports remote software agents. These are separate operations: a debugging assistant should locate a reproducible failure and propose a testable patch; architecture assistance should distinguish requirements from assumptions; an agent that edits files needs tool permissions and review safeguards. <a href="https://openai.com/index/airbnb-gpt-6-astra/" target="_blank" rel="noopener noreferrer">Source: OpenAI's Airbnb report</a>.</p>
<div class="ab-grid"><article><span>ENGINEERING 01</span><h3>Debugging</h3><p>Trace complex issues across files and logs. Judge usefulness by verified fixes and relevant test results, not by explanation quality alone.</p></article><article><span>ENGINEERING 02</span><h3>System architecture</h3><p>Explore designs, integration boundaries and trade-offs. A plausible diagram still requires performance, privacy and maintainability review.</p></article><article><span>ENGINEERING 03</span><h3>Remote coding agents</h3><p>Delegate scoped changes in approved environments. Codex capabilities do not automatically reveal Airbnb's internal permission and approval architecture.</p></article><article><span>ENGINEERING 04</span><h3>Strategy work</h3><p>Use models to synthesize and revise complex documents. The published example is useful context, not a measured improvement across all knowledge work.</p></article></div>
<p><strong>What remains private:</strong> tool architecture, exact prompt and workflow designs, distribution of tasks by model, security controls, test harness and error rates. The right way to assess agentic development is to evaluate the complete workflow, as explained by SXF's <a href="/guides/what-is-agentic-ai/">agentic AI guide</a> and <a href="/research/ai-agent-reliability/">agent reliability research</a>.</p></section>
<section id="ab-80"><h2>Did GPT-6 Astra increase Airbnb's feature output by 80%?</h2>
<p><strong>No such causal result has been published.</strong> Airbnb CTO Ahmad Al-Dahle said that the company's development teams were <strong>shipping roughly 80% more features than a year earlier</strong>, and described OpenAI frontier models, including Astra, as important developer tooling. This is a year-over-year observation and leadership assessment; it is not a controlled, model-specific before-and-after test. <a href="https://news.airbnb.com/expanding-access-to-openai-frontier-models-including-gpt-6-astra" target="_blank" rel="noopener noreferrer">Airbnb's own statement</a>.</p>
<div class="ab-note"><strong>SXF evidence check:</strong> Neither company reports how a “feature” was counted, the number of developers, feature size or quality, how much the model stack changed during the comparison period, changes to processes or staffing, or control-group results. Therefore an 80% increase in observed output must not be marketed as “GPT-6 Astra makes engineers 80% more productive.”</div>
<div class="ab-scroll"><table class="ab-table"><thead><tr><th>Claim</th><th>Documented</th><th>Not documented</th></tr></thead><tbody>
<tr><th>Feature output</th><td>~80% more shipped than the previous year</td><td>Exact definition, quality and causal attribution</td></tr>
<tr><th>Model help</th><td>Early debugging and system-design experiences</td><td>Task pass rate, effort saved and regression frequency</td></tr>
<tr><th>Document iterations</th><td>One user's 3–4 vs 20+ experience</td><td>Blinded sample, comparison models and repeated trials</td></tr>
<tr><th>Platform access</th><td>API and Bedrock both named</td><td>Contract, costs and production traffic split</td></tr>
</tbody></table></div>
<p>A credible productivity metric should count <em>accepted and sustained</em> changes per engineering hour, alongside deployment failure rates, review time and defect leakage. Simply increasing ticket completions can look positive while creating long-term maintenance costs. These are SXF recommendations, not measurements from Airbnb.</p></section>
<section id="ab-passes"><h2>What does “3–4 passes instead of 20+” actually mean?</h2>
<p>OpenAI's account includes an anecdote not detailed in the shorter Airbnb article: one user described reaching a strong result on a strategic-document or other non-coding task in <strong>three or four passes using Astra</strong> rather than more than twenty iterations using unspecified other models. That suggests a better experience for that individual task. It is <strong>not</strong> a scientifically controlled sixfold speedup, because the model identities, criteria, task bundle and number of repeated tests are not disclosed. <a href="https://openai.com/index/airbnb-gpt-6-astra/" target="_blank" rel="noopener noreferrer">Primary report</a>.</p>
<p>To investigate this effect, SXF would hold input materials fixed, use comparable prompt budgets, blind reviewers to the model, measure every correction and record time to accepted work. Running multiple design briefs and code-review tasks would show the result's distribution rather than one person's best experience. Such a trial might confirm, reduce or reverse the apparent benefit depending on task complexity and reviewer expectations.</p></section>
<section id="ab-marketplace"><h2>Does Airbnb use OpenAI models for search, fraud prevention and support?</h2>
<p><strong>Yes, but the announcements do not say these are all GPT-6 Astra services.</strong> Airbnb describes OpenAI-model uses in search, fraud prevention, guest and host support, and insurance claims. It says AI can help understand traveler intent, flag suspect content, support disrupted plans and simplify host payouts. The statements do not identify each model ID, user-facing automation level or measured outcomes for each service.</p>
<div class="ab-scroll"><table class="ab-table"><thead><tr><th>Airbnb use</th><th>Reported aim</th><th>SXF risk question</th></tr></thead><tbody>
<tr><th>Search</th><td>Relevant options for travelers</td><td>How are ranking quality and misleading suggestions evaluated?</td></tr>
<tr><th>Fraud</th><td>Flag potentially fraudulent claims or content</td><td>How are false positives and appeals handled?</td></tr>
<tr><th>Support</th><td>Help hosts and guests with problems</td><td>Where is human escalation mandatory?</td></tr>
<tr><th>Claims</th><td>Simpler host insurance reimbursements</td><td>How are evidence and consequential decisions verified?</td></tr>
</tbody></table></div>
<p>These are marketplace application areas, not a public commitment to release a single Astra-driven assistant. The design and safety needs differ: an irrelevant search result is not the same risk as a wrongful account restriction or a disputed payment.</p></section>
<section id="ab-api"><h2>Why is AWS Bedrock important to the Airbnb–OpenAI deal?</h2>
<p>The agreement supplies access through <strong>OpenAI's APIs and Amazon Bedrock</strong>, and Airbnb names AWS as its preferred cloud provider. AWS's <a href="https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-astra.html" target="_blank" rel="noopener noreferrer">GPT-6 Astra Bedrock model card</a> documents supported interfaces, pricing tiers, context length and endpoints. Its <a href="https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html" target="_blank" rel="noopener noreferrer">OpenAI model catalog</a> confirms supported OpenAI families. OpenAI's <a href="https://developers.openai.com/api/docs/models" target="_blank" rel="noopener noreferrer">model list</a> describes direct API access and public developer prices. These documents verify general capabilities, not Airbnb's internal allocation of requests.</p>
<p>There are different technical and commercial decisions across the two delivery channels, including IAM permissions, region controls, service billing, token caching and latency. Access to both can give a large organization integration choices, but the public agreement does not reveal whether teams use different routes for different workloads. Nor does it disclose an enterprise purchase price. Pricing a private deal solely from public API rates would be misleading.</p>
<h3>What should an enterprise measure as total model cost?</h3>
<p>Compare <strong>cost per accepted development task</strong>, incorporating model usage, cloud infrastructure, retries, tools, tests and reviewer time. The <a href="/tools/ai-model-cost-calculator/">SXF AI Model Cost Calculator</a> helps illustrate public model-token prices, but cannot infer contract discounts or true enterprise return on investment.</p></section>
<section id="ab-sxf"><h2>SXF analysis: six tests before scaling frontier-model access</h2>
<p><strong>Our assessment:</strong> Airbnb's move exemplifies a shift from isolated code completion toward integrated engineering agents. The model matters, but useful adoption also needs repository context, safe tools, test infrastructure, approvals and ongoing monitoring. The broader developer-tooling stack may create advantages that cannot be assigned to a single model. SXF proposes the following review framework; it does not describe Airbnb's unpublished internal procedures.</p>
<div class="ab-grid"><article><span>01 / COMPARABILITY</span><h3>Same starting point</h3><p>Compare identical bug reports and design tasks using frozen code snapshots and equivalent tool permissions.</p></article><article><span>02 / ACCEPTANCE</span><h3>Verified correctness</h3><p>Require tests, reviewed diffs, constraints met and a check for regressions or invented dependencies.</p></article><article><span>03 / HUMAN TIME</span><h3>Complete elapsed work</h3><p>Include planning, prompt iterations, reviewer corrections, resets and failed tool calls.</p></article><article><span>04 / ECONOMICS</span><h3>Full operating cost</h3><p>Count model calls, infrastructure, context overhead, review labor and downstream support.</p></article><article><span>05 / SECURITY</span><h3>Controlled authorization</h3><p>Test secret protection, repository access, tool permissions and approvals for risky changes.</p></article><article><span>06 / QUALITY OVER TIME</span><h3>Durable product value</h3><p>Monitor escaped bugs, incidents, maintainability, customer feedback and rollback frequency.</p></article></div>
<div class="ab-note"><strong>SXF decision principle:</strong> Widen adoption only when measured gains in accepted work are reproducible and do not create unacceptable security, quality or review burdens. Treat the 80% claim and the document anecdote as starting hypotheses, not a substitute for this evaluation.</div>
<p>Astra may be worthwhile for hard, ambiguous engineering work, while a lower-cost model could handle simple high-volume transformations. The existing mix of Sol, Terra and Luna is consistent with a multi-model approach, but Airbnb's exact routing policies remain undisclosed. Read <a href="/models/gpt-6-astra/">SXF's model reference</a> and <a href="/models/pricing/">pricing overview</a> before comparing public unit costs.</p></section>
<section id="ab-privacy"><h2>Data privacy, agent security and user impact</h2>
<p>Airbnb's business touches sensitive guest, host, support and claim information. The public statements do not disclose its exact model data flows, retention settings or approval rules. Do not assume all customer data is forwarded to Astra or, conversely, that every workflow is risk-free.</p>
<p>OpenAI's <a href="https://developers.openai.com/api/docs/guides/your-data" target="_blank" rel="noopener noreferrer">API data-controls documentation</a> says API inputs and outputs are not used for training by default unless explicitly opted in, while describing logging and retention details. That is a platform-wide policy, not proof of Airbnb's private settings or AWS's data-processing terms. The <a href="https://www.nist.gov/itl/ai-risk-management-framework" target="_blank" rel="noopener noreferrer">NIST AI Risk Management Framework</a> is an independent voluntary reference for governance, not a certification of Airbnb's systems.</p>
<p>SXF recommends least-privilege tools for coding agents, protected credentials, human review of critical deployments and auditable logs. For fraud or claims, responsible workflows should also evaluate false positives, explainable escalation paths and human oversight for significant consequences. See <a href="/guides/ai-agent-security/">AI Agent Security</a> for related technical risks.</p></section>
<section id="ab-perspective"><h2>What this partnership tells us about enterprise AI in 2026</h2>
<p>Airbnb's reported shift illustrates a wider change: companies increasingly evaluate frontier models in the context of complete developer systems rather than isolated prompts. An agent may reason well but still fail due to weak requirements, incorrect tools, missing tests or bad integration. Good operational design and model choice must improve together.</p>
<p>The most defensible takeaway is that Airbnb has expanded available model capability and reported encouraging operational observations. <strong>Neither a controlled, model-specific 80% uplift nor independently verified ROI was published.</strong> The case should inspire task-level measurement, not provide a guaranteed productivity forecast. For a contrasting research use case, see <a href="/signals/how-jump-trading-is-scaling-quant-research-with-chatgpt-342677a/">Jump Trading and ChatGPT</a>; the two firms' outcomes cannot be directly compared from their announcements.</p></section>
<section id="ab-faq"><h2>Frequently asked questions about Airbnb and GPT-6 Astra</h2>
<h3>What did Airbnb agree with OpenAI?</h3><p>To widen engineering and product teams' access to GPT-6 Astra and other models through OpenAI APIs and Amazon Bedrock.</p>
<h3>How is Airbnb using Astra?</h3><p>Early use involves difficult debugging, systems design and engineering ideas. OpenAI cites one document-revision example.</p>
<h3>Did Astra make Airbnb ship 80% more features?</h3><p>Not established. The CTO reported a year-over-year increase and said frontier models were important, but no causal study isolates Astra.</p>
<h3>What is the 3–4 versus 20+ example?</h3><p>One person's reported drafting experience. The models compared and test methodology were not published.</p>
<h3>Does Airbnb already use Codex?</h3><p>Yes. Its internal developer platform supports remote agents powered by Codex and GPT-5.6 family models.</p>
<h3>Why is Amazon Bedrock involved?</h3><p>Airbnb's preferred cloud provider is AWS, and both AWS Bedrock and direct OpenAI APIs are named access routes.</p>
<h3>Does every Airbnb customer interaction now use Astra?</h3><p>No. The source describes broader OpenAI-model usage and an internal engineering expansion, not model IDs for each customer-facing feature.</p>
<h3>Are costs and ROI disclosed?</h3><p>No. The companies did not publish contract values or independently audited model-specific productivity figures.</p></section>
<section id="ab-sources"><h2>Primary sources, verification and editorial transparency</h2>
<p><strong>Last source review: November 8, 2026.</strong> The named company announcements support access and first-party productivity statements. AWS and OpenAI documentation supports general product features, not Airbnb's deployment configuration; NIST is a general risk-management reference. The six-test protocol is SXF's original editorial analysis, not firsthand evidence of Airbnb operations.</p>
<ol class="ab-sources">
<li><a href="https://news.airbnb.com/expanding-access-to-openai-frontier-models-including-gpt-6-astra" target="_blank" rel="noopener noreferrer">Airbnb Newsroom — September 23, 2026</a>: Agreement, existing developer tools, 80% claim and marketplace AI uses.</li>
<li><a href="https://openai.com/index/airbnb-gpt-6-astra/" target="_blank" rel="noopener noreferrer">OpenAI — Airbnb expands GPT-6 Astra access</a>: Agreement and reported 3–4 versus 20+ experience.</li>
<li><a href="https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-astra.html" target="_blank" rel="noopener noreferrer">AWS — GPT-6 Astra model card</a>: Model interfaces, regions and published pricing tiers.</li>
<li><a href="https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html" target="_blank" rel="noopener noreferrer">AWS — OpenAI models in Bedrock</a>: Supported Bedrock access.</li>
<li><a href="https://developers.openai.com/api/docs/models" target="_blank" rel="noopener noreferrer">OpenAI API — Model directory</a>: Model features and direct API rates.</li>
<li><a href="https://openai.com/index/gpt-6-astra/" target="_blank" rel="noopener noreferrer">OpenAI — GPT-6 Astra announcement</a>: Product positioning and vendor evaluations.</li>
<li><a href="https://developers.openai.com/api/docs/guides/your-data" target="_blank" rel="noopener noreferrer">OpenAI API — Data controls</a>: General data processing and retention guidance.</li>
<li><a href="https://www.nist.gov/itl/ai-risk-management-framework" target="_blank" rel="noopener noreferrer">NIST — AI Risk Management Framework</a>: Independent voluntary governance reference.</li>
</ol>
<p>Related reading: <a href="/models/gpt-6-astra/">GPT-6 Astra</a> · <a href="/guides/what-is-agentic-ai/">Agentic AI</a> · <a href="/research/ai-agent-reliability/">Agent Reliability</a> · <a href="/guides/ai-agent-security/">Agent Security</a> · <a href="/topics/openai/">OpenAI Signals</a>.</p></section>
</section>'''
CSS = r'''<style id="airbnb-gpt6-editorial-css">.ab-astra-page .ab-astra{margin:35px auto 55px}.ab-astra section{margin:42px 0;max-width:1020px;scroll-margin-top:95px}.ab-astra p,.ab-astra li{line-height:1.82}.ab-astra a{text-decoration:underline;text-underline-offset:3px}.ab-astra section>h2{font-size:clamp(1.48rem,2.3vw,2.05rem);line-height:1.3;margin:0 0 17px}.ab-astra h3{font-size:1.13rem;line-height:1.45;margin:25px 0 9px}.ab-deck{font-size:1.1rem;max-width:935px;line-height:1.84!important;color:#c7d8e8}.ab-facts,.ab-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:25px 0}.ab-facts>div,.ab-grid>article{padding:19px;border:1px solid rgba(138,186,225,.25);border-radius:16px;background:linear-gradient(135deg,rgba(77,128,179,.17),rgba(8,15,26,.46))}.ab-facts span,.ab-grid span{display:block;font-size:.75rem;letter-spacing:.075em;color:#99e9d8;font-weight:800}.ab-facts strong{display:block;margin:9px 0 4px;font-size:1.05rem;color:#eef6fe}.ab-facts small{color:#acbfd1;line-height:1.55}.ab-grid h3{margin:9px 0}.ab-grid p{margin:0}.ab-toc{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0;padding:18px 19px;border:1px solid rgba(132,193,215,.26);border-radius:16px;background:rgba(30,63,90,.17)}.ab-toc strong{width:100%;margin-bottom:3px}.ab-toc a{padding:7px 12px;border:1px solid rgba(130,203,210,.28);border-radius:25px;text-decoration:none}.ab-scroll{overflow-x:auto;border:1px solid rgba(131,185,220,.28);border-radius:15px;margin:24px 0}.ab-table{width:100%;min-width:720px;border-collapse:collapse;font-size:.9rem}.ab-table th,.ab-table td{padding:14px 16px;border-bottom:1px solid rgba(142,185,228,.17);line-height:1.6;vertical-align:top;text-align:left}.ab-table thead th{background:#172c42;color:#e4f0ff}.ab-table tbody th{color:#9cf0dc}.ab-note{padding:19px 22px;background:rgba(94,166,166,.1);border-left:3px solid #91e9d8;border-radius:0 14px 14px 0;margin:25px 0;line-height:1.8}.ab-sources{padding-left:1.5rem}.ab-sources li{margin:13px 0}.ab-astra-page a:focus-visible{outline:2px solid #97eddb;outline-offset:4px}@media(max-width:760px){.ab-facts,.ab-grid{grid-template-columns:1fr}.ab-table{min-width:580px}.ab-astra section{margin:34px 0}}</style>'''

def enrich(page: str) -> str:
    """Replace the thin feed summary while preserving this signal URL."""
    marker = 'data-sxf-airbnb-astra="2026-11-08"'
    if marker in page:
        return page
    required = ['class="intel-page signal-page"',
                '<h1>Airbnb widens access to GPT-6 Astra and OpenAI frontier models</h1>',
                '<section class="signal-layout shell">',
                '<section class="signal-taxonomy shell">',
                '<meta name="twitter:card" content="summary" />']
    if any(s not in page for s in required):
        raise ValueError("Airbnb signal generator layout changed")
    page = page.replace('class="intel-page signal-page"',
                        'class="intel-page signal-page ab-astra-page"', 1)
    page, n = re.subn(r'<title>.*?</title>', '<title>'+escape(TITLE)+'</title>',
                      page, count=1, flags=re.S)
    if n != 1:
        raise ValueError("HTML title not found")
    for key, value in [('description', DESCRIPTION), ('og:title', TITLE),
                       ('og:description', DESCRIPTION), ('twitter:title', TITLE),
                       ('twitter:description', DESCRIPTION)]:
        pat = r'(<meta (?:property|name)="' + re.escape(key) + r'" content=")[^"]*(" />)'
        page, n = re.subn(pat,
            lambda m: m.group(1)+escape(value, quote=True)+m.group(2),
            page, count=1)
        if n != 1:
            raise ValueError("Meta tag missing: "+key)
    page = page.replace('<meta name="twitter:card" content="summary" />',
        '<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />'
        '<meta property="og:image:alt" content="SXF AI research on Airbnb and GPT-6 Astra" />'
        '<meta name="twitter:card" content="summary_large_image" />'
        '<meta name="twitter:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />', 1)
    css_link = '<link rel="stylesheet" href="/intelligence.css" />'
    if css_link not in page:
        raise ValueError("Missing site CSS link")
    page = page.replace(css_link, css_link+'\n'+CSS, 1)
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("Missing JSON-LD data")
    ld = json.loads(match.group(1))
    graph = ld['@graph']
    if len(graph) != 3:
        raise ValueError("Expected WebPage Article BreadcrumbList")
    graph[0].update(name=TITLE, description=DESCRIPTION,
                    breadcrumb={'@id':CANONICAL+'#breadcrumb'})
    graph[1].update(headline=H1, description=DESCRIPTION,
                    dateModified='2026-11-08', keywords=KEYWORDS,
                    citation=SOURCES, isBasedOn=SOURCES[:2],
                    about=[{'@type':'Organization','name':'Airbnb'},
                           {'@type':'Organization','name':'OpenAI'},
                           {'@type':'Thing','name':'GPT-6 Astra'},
                           {'@type':'SoftwareApplication','name':'Amazon Bedrock'}])
    graph[2]['itemListElement'].append({'@type':'ListItem','position':4,
        'name':'Airbnb and GPT-6 Astra analysis','item':CANONICAL})
    graph.append({'@type':'FAQPage','@id':CANONICAL+'#faq',
        'mainEntity':[{'@type':'Question','name':q,
          'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]})
    page = (page[:match.start()]+'<script type="application/ld+json">'+
            json.dumps(ld, ensure_ascii=False, separators=(',', ':'))+
            '</script>'+page[match.end():])
    page = page.replace('<h1>Airbnb widens access to GPT-6 Astra and OpenAI frontier models</h1>',
                        '<h1>'+escape(H1)+'</h1>', 1)
    page, n = re.subn(r'<section class="signal-layout shell">.*?</section>',
                      lambda _:BRIEF,page,count=1,flags=re.S)
    if n != 1:
        raise ValueError("Signal summary replacement failed")
    page = page.replace('<section class="signal-taxonomy shell">',
                        BODY+'\n<section class="signal-taxonomy shell">', 1)
    if page.count(marker) != 1:
        raise ValueError("Editorial marker lost or repeated")
    for url in SOURCES:
        if url not in page:
            raise ValueError("Missing primary source "+url)
    return page
