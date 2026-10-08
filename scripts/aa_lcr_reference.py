"""Editorial reference for the AA-LCR v1.1 evaluation. Called from the canonical generator."""
from html import escape

def render_aa_lcr_reference(benchmark, observations, verified, base):
    h = lambda x: escape(str(x), quote=True)
    source = "https://artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning"
    method = "https://artificialanalysis.ai/methodology/intelligence-benchmarking"
    dataset = "https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR"
    def link(url, name):
        return f'<a href="{h(url)}" target="_blank" rel="noopener noreferrer">{h(name)} ↗</a>'
    faqs = [
        ("What is AA-LCR v1.1?", "AA-LCR v1.1 is Artificial Analysis Long Context Reasoning, a benchmark of 100 open-answer questions requiring reasoning across large sets of real documents, typically around 100,000 input tokens per document set."),
        ("How is AA-LCR v1.1 scored?", "Artificial Analysis grades model answers with an LLM-based equality checker and reports pass@1 accuracy aggregated across three runs. Higher percentages indicate more correct answers under the benchmark's rules; they do not measure percentage of human-level intelligence."),
        ("What changed between AA-LCR v1.0 and v1.1?", "Version 1.1 adds a system prompt to clarify grading instructions, corrects 16 answer keys and uses GPT-5.6 Luna at medium reasoning effort as the equality checker. Results across the two versions should not be compared directly."),
        ("Does AA-LCR measure needle-in-a-haystack retrieval?", "Not by itself. AA-LCR asks questions that require synthesis and reasoning across long real-world documents. Retrieval is involved, but a single copied fact or isolated document match is not sufficient for many questions."),
        ("Is the SXF leaderboard the complete AA-LCR leaderboard?", "No. SXF shows only the observations stored in its evaluation dataset, grouped by comparable evidence and configuration. Artificial Analysis maintains the official live leaderboard, which may include additional models and more recent scores."),
        ("Can I reproduce the benchmark?", "The dataset is publicly available on Hugging Face with question and document references. Reproducing the publisher's scores requires matching document order, prompt formatting, model settings, three repeats and the v1.1 equality-checker protocol; an alternative judge or harness can produce different results."),
        ("What is a good AA-LCR score?", "A higher pass@1 result means a greater share of benchmark questions was answered correctly in the reported setting. Interpret gaps using the exact evaluation version, reasoning effort, tool conditions and scoring date; do not treat them as universal model rankings."),
    ]
    faq_html = "".join(f'<details><summary>{h(q)}</summary><p>{h(a)}</p></details>' for q,a in faqs)
    faq_schema = [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]
    html = f"""
    <section class="model-reference model-reference-deep shell" id="aa-lcr-overview">
      <div class="model-section-head"><p class="eyebrow">QUICK ANSWER</p><h2>What is the AA-LCR v1.1 benchmark?</h2></div>
      <p><strong>AA-LCR v1.1 (Artificial Analysis Long Context Reasoning)</strong> tests whether an AI language model can reason accurately across long collections of real-world documents. It contains <strong>100 open-answer questions</strong> organized across <strong>30 document sets and 234 documents</strong>, with roughly <strong>100,000 tokens per set</strong>. Models need a context window of at least <strong>128K tokens</strong> for the official evaluation. This is a synthesis-and-reasoning test, not simply a context-window-size leaderboard.</p>
      <p>The publisher, Artificial Analysis, reports <strong>pass@1 accuracy</strong> after three repeats and uses an LLM equality checker to judge answers. SXF does not independently re-run the evaluation: the results lower on this page are a <strong>dated subset of sourced observations</strong>, not the complete official live ranking.</p>
      <nav class="model-related-links" aria-label="AA-LCR article navigation"><a href="#aa-lcr-method"><strong>Method ↓</strong></a><a href="#aa-lcr-v11"><strong>v1.1 changes ↓</strong></a><a href="#aa-lcr-interpret"><strong>Read scores ↓</strong></a><a href="#aa-lcr-faq"><strong>FAQ ↓</strong></a><a href="#aa-lcr-sources"><strong>Sources ↓</strong></a></nav>
    </section>
    <section class="model-reference model-reference-deep shell" id="aa-lcr-method">
      <div class="model-section-head"><p class="eyebrow">BENCHMARK DESIGN</p><h2>Dataset, tasks, documents and scoring protocol</h2></div>
      <div class="guide-table-wrap"><table class="guide-table"><thead><tr><th scope="col">Parameter</th><th scope="col">Official AA-LCR v1.1 specification</th></tr></thead><tbody>
      <tr><th scope="row">Publisher</th><td>Artificial Analysis</td></tr><tr><th scope="row">Dataset</th><td>100 questions / 30 document sets / 234 source documents</td></tr>
      <tr><th scope="row">Input</th><td>Approximately 100K tokens per document set, based on cl100k_base counting</td></tr>
      <tr><th scope="row">Required context</th><td>At least 128K tokens to be scored by the publisher</td></tr>
      <tr><th scope="row">Answer type</th><td>Free-form written answer; not multiple-choice</td></tr>
      <tr><th scope="row">Metric</th><td>Pass@1 accuracy, higher is better</td></tr>
      <tr><th scope="row">Repeats</th><td>3 per question, aggregated for the published score</td></tr>
      <tr><th scope="row">Grading</th><td>LLM equality checker: GPT-5.6 Luna, medium effort, in v1.1</td></tr>
      <tr><th scope="row">Tools</th><td>No tools in the official benchmark configuration</td></tr>
      <tr><th scope="row">SXF coverage</th><td>{len(observations)} stored observations, source verified {h(verified)}; not the full official leaderboard</td></tr>
      </tbody></table></div>
      <h3>What makes long-context reasoning difficult?</h3><p>A model must use information scattered across long reports, contracts, company documents, government consultations, academic material and other real documents. The challenge is to retain relevant evidence, reconcile details across documents, follow precise question constraints and produce a correct answer. A million-token window alone does not guarantee correctness.</p>
      <h3>Document categories and dataset access</h3><p>The seven published source categories include company documents, industry reports, government consultations, academia, legal, marketing and survey reports. Company documents account for most questions. The dataset is publicly accessible on Hugging Face, but underlying document rights are distinct from the benchmark's question-set license. {link(dataset, "Open public dataset")}</p>
    </section>
    <section class="model-reference model-reference-deep shell" id="aa-lcr-v11">
      <div class="model-section-head"><p class="eyebrow">VERSION CONTROL</p><h2>AA-LCR v1.1 versus v1.0: what changed?</h2></div>
      <p>The v1.1 revision <strong>added a system prompt for grading instructions</strong>, <strong>corrected 16 reference answers</strong> and uses <strong>GPT-5.6 Luna (medium)</strong> as the equality checker. Artificial Analysis says scores are <strong>not directly comparable with v1.0</strong>. Do not chart old v1.0 scores as if they came from the same judge and answer keys.</p>
      <p>Question selection and source-document sets remain the same across the versions, but evaluation rules affect the outcome. A score difference can therefore reflect grading changes, inference settings or sampling rather than an actual model improvement. When quoting a percentage, always attach the version and the exact model configuration.</p>
      <p>The benchmark is a component of the Artificial Analysis Intelligence Index: in the published v4.3.2 methodology, it contributes <strong>5%</strong> of the composite. That weighting should not be confused with an AA-LCR score or an independent importance ranking for your own use case.</p>
    </section>
    <section class="model-reference model-reference-deep shell" id="aa-lcr-interpret">
      <div class="model-section-head"><p class="eyebrow">RESULTS GUIDE</p><h2>How to interpret AA-LCR scores and model rankings</h2></div>
      <h3>What a 80% score means</h3><p>Under a comparable published v1.1 test, an 80% pass@1 score corresponds to correct answers on approximately four out of five evaluated attempts. It does <strong>not</strong> mean the model understands 80% of all long documents, is 80% as intelligent as a human, or will deliver 80% reliability in your industry.</p>
      <h3>Why the highest score is not automatically the right choice</h3><p>For procurement and deployment, compare model quality with price per million tokens, latency on long prompts, cache behavior, document privacy, retrieval architecture and error severity. A slightly lower benchmark score can be preferable when it delivers cheaper or more reliable performance on your real tasks.</p>
      <h3>Comparable groups, tools and reasoning effort</h3><p>SXF preserves the source, effort and tool configuration for each imported observation. The same model at different reasoning effort levels is not the same experimental condition. A third-party reproduction with a different grader should never be silently merged into the publisher's official leaderboard. Do not infer absent models scored zero.</p>
      <h3>Dataset openness and contamination risk</h3><p>The question-answer set is public. Exposure in training or tuning data is therefore a plausible limitation when interpreting model rankings. Public data helps researchers audit tasks, but it does not establish a contamination-free test. The equality-checker judge can also have its own interpretation errors.</p>
      <div class="model-related-links"><a href="/evaluations/">Other AI evaluations ↗</a><a href="/evaluations/explorer/">Evaluation explorer ↗</a><a href="/models/">Model directory ↗</a><a href="/compare/">Cross-model comparison ↗</a></div>
    </section>
    <section class="benchmark-faq shell" id="aa-lcr-faq"><div class="intel-section-head"><div><p class="eyebrow">FAQ</p><h2>AA-LCR v1.1: frequently asked questions</h2></div></div><div class="benchmark-faq-list">{faq_html}</div></section>
    <section class="benchmark-sources shell" id="aa-lcr-sources"><div class="intel-section-head"><div><p class="eyebrow">PRIMARY SOURCES</p><h2>Official leaderboard, methodology and dataset</h2></div></div><p>Use Artificial Analysis for the live official ranking and benchmarking protocol. SXF keeps source-linked historical observations and does not claim that its partial model table is live or comprehensive.</p><div class="benchmark-source-links">
      <a href="{h(source)}" target="_blank" rel="noopener noreferrer"><strong>Artificial Analysis AA-LCR leaderboard</strong><span>Official current model results ↗</span></a>
      <a href="{h(method)}" target="_blank" rel="noopener noreferrer"><strong>Artificial Analysis benchmarking methodology</strong><span>Prompts, score definitions, version changes ↗</span></a>
      <a href="{h(dataset)}" target="_blank" rel="noopener noreferrer"><strong>ArtificialAnalysis/AA-LCR dataset</strong><span>Public questions, answers and dataset information ↗</span></a>
      <a href="/data/model-evaluations.json"><strong>SXF model evaluation observations</strong><span>Stored source and configuration metadata ↗</span></a>
    </div></section>"""
    return html, faq_schema
