"""Source-verified LFM2.5-24B-A2B model reference, rendered on every build.

The SXF weight-fit tool intentionally reports file-size feasibility, not tested
VRAM, throughput, or full context capacity. All benchmark numbers are vendor data.
"""
from __future__ import annotations

from html import escape

SLUG = "lfm2-5-24b-a2b"
URL = "https://sxf.si/models/lfm2-5-24b-a2b/"
TITLE = "LFM2.5-24B-A2B: Specs, Benchmarks, VRAM & Setup | SXF"
DESCRIPTION = ("LFM2.5-24B-A2B explained: 24B MoE, 2.45B active, 131K context, "
               "local RAM/VRAM by quantization, official benchmarks, llama.cpp setup, "
               "API pricing and SXF memory checker.")
PUBLISHED = "2026-10-13"
MODIFIED = "2026-11-01"
SOURCES = {
    "launch": "https://www.liquid.ai/blog/lfm2-5-24b-a2b",
    "model": "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B",
    "gguf": "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF",
    "base": "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-Base",
    "fp8": "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-FP8",
    "predecessor": "https://www.liquid.ai/blog/lfm2-24b-a2b",
    "docs": "https://docs.liquid.ai/",
    "license": "https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/main/LICENSE",
}
# Decimal GB of *GGUF weight files* in the first-party Hugging Face repo.
# Never present these as actual benchmarked RAM/VRAM requirements.
QUANTS = [
    ("Q4_0 (QAD)", 13.6, "4-bit, quantization-aware distillation"),
    ("Q4_K_M", 14.5, "4-bit, balanced file size"),
    ("Q5_K_M", 17.0, "5-bit, larger weights"),
    ("Q6_K", 19.7, "6-bit, larger weights"),
    ("Q8_0", 25.5, "8-bit, large weights"),
    ("BF16 / F16", 48.0, "16-bit, baseline-sized weights"),
]
# Official vendor table; task scores cannot be combined into a single ranking.
BENCHMARKS = [
    ("AutomationBench", "Agent automation", "27.69", "8.72", "LFM higher"),
    ("BFCLv4", "Function calling", "65.01", "65.00", "Approximately tied"),
    ("ToolSandbox", "Tool interactions", "80.71", "75.02", "LFM higher"),
    ("LiveClaw", "Agent workflows", "48.09", "38.19", "LFM higher"),
    ("PinchBench", "Agent workflows", "83.18", "89.93", "Qwen higher"),
    ("WebArena Verified", "Web agents", "26.75", "37.62", "Qwen higher"),
    ("IFEval", "Instruction following", "96.75", "93.06", "LFM higher"),
    ("GPQA Diamond", "Expert knowledge", "74.42", "83.69", "Qwen higher"),
    ("SWE-Bench Verified (OpenCode)", "Software engineering", "51.00", "66.20", "Qwen higher"),
]
FAQ = [
    ("What is LFM2.5-24B-A2B?",
     "It is Liquid AI's 24-billion-parameter text-only mixture-of-experts reasoning model, released October 13, 2026, with about 2.45 billion active parameters per generated token. It is optimized for local tool-using agents."),
    ("How many parameters are active in LFM2.5-24B-A2B?",
     "The official model card lists 24.0B total parameters and 2.45B active parameters per token. The model name rounds the active count to A2B; the full weight set still needs storage or offloading."),
    ("What is the context window for LFM2.5-24B-A2B?",
     "The model card specifies 131,072 tokens. That is a supported model limit, not a guarantee that 131K tokens fit in a particular laptop's RAM or deliver perfect recall."),
    ("How much RAM or VRAM do I need to run LFM2.5-24B-A2B locally?",
     "Liquid AI's official GGUF files range from about 13.6 GB for Q4_0 to 48 GB for BF16/F16. Total runtime memory is higher because the KV cache, compute buffers, context length and software need space. There is no single officially verified minimum across configurations."),
    ("Can LFM2.5-24B-A2B run on a 16 GB laptop?",
     "A 13.6 GB Q4_0 or 14.5 GB Q4_K_M weight file leaves very little space in a 16 GB unified-memory system. Full offload and long contexts are not established as usable; consider less context, partial offload or a smaller model and verify measured peak memory."),
    ("Is LFM2.5-24B-A2B better than Qwen3.6-35B-A3B?",
     "It depends on the task. Liquid AI reports higher scores for LFM2.5 on AutomationBench, LiveClaw and ToolSandbox, but lower results on WebArena Verified, GPQA Diamond and SWE-Bench Verified. These are vendor-reported comparisons, not independent SXF tests."),
    ("How fast is LFM2.5-24B-A2B?",
     "Liquid AI reports 184 tokens per second on an Apple M5 Max and 114 on AMD Ryzen AI Max+ 395 with Q4_K_M and a 4K prompt. It also reports more than 21K aggregate output tokens per second on one NVIDIA B300 at high concurrency. Those are different workloads, not interchangeable per-user speeds."),
    ("Can I use LFM2.5-24B-A2B with llama.cpp or Ollama?",
     "Liquid AI publishes GGUF checkpoints and an official llama-cli command. Other supported ecosystems include MLX, vLLM and SGLang. Use a current runtime with lfm2moe support and the checkpoint's recommended sampling settings."),
    ("Is LFM2.5-24B-A2B open source and free for commercial use?",
     "The weights are publicly distributed under LFM Open License v1.0 (lfm1.0), whose exact commercial and redistribution terms must be reviewed. Open weights are not automatically an unrestricted OSI-approved open-source license."),
    ("What does the Liquid AI API cost for LFM2.5-24B-A2B?",
     "At the October 13, 2026 launch, Liquid AI advertised $0.10 per million input tokens, $0.05 per million cached input tokens, and $1.00 per million output tokens. These are dated announced rates; confirm current console billing."),
    ("What is the difference between LFM2.5-24B-A2B and LFM2-24B-A2B?",
     "LFM2.5 expands context from 32,768 to 131,072 tokens, doubles vocabulary from about 65K to 128K, and adds further training and reasoning-focused post-training. It keeps the 40-layer hybrid MoE architecture."),
    ("Does LFM2.5-24B-A2B support image or audio input?",
     "No. The official LFM2.5-24B-A2B card identifies it as text-only. For image and audio tasks, investigate Liquid AI's separate multimodal model families."),
]


def schema():
    return {"@context": "https://schema.org", "@graph": [
        {
            "@type": "WebPage", "@id": URL+"#webpage", "url": URL,
            "name": TITLE, "description": DESCRIPTION,
            "inLanguage": "en", "dateModified": MODIFIED,
            "isPartOf": {"@id":"https://sxf.si/#website"},
            "mainEntity": {"@id":URL+"#article"},
            "about": {"@id":URL+"#model"},
        },
        {
            "@type": "TechArticle", "@id":URL+"#article", "headline":TITLE,
            "description": DESCRIPTION, "datePublished": PUBLISHED, "dateModified":MODIFIED,
            "inLanguage":"en", "mainEntityOfPage":{"@id":URL+"#webpage"},
            "author":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
            "publisher":{"@type":"Organization","name":"SXF / AI","url":"https://sxf.si/"},
            "about":{"@id":URL+"#model"},
            "citation":list(SOURCES.values()),
            "keywords":["LFM2.5-24B-A2B", "Liquid AI 24B A2B", "LFM2.5 24B VRAM",
                        "LFM2.5-24B-A2B GGUF", "LFM2.5 24B benchmarks",
                        "LFM2.5-24B-A2B llama.cpp", "LFM2.5 24B API pricing",
                        "24B MoE 2B active", "LFM2.5-24B-A2B local inference"],
        },
        {
            "@type":"Thing","@id":URL+"#model","name":"LFM2.5-24B-A2B",
            "description":"24B total, 2.45B active, 131072-token text-only sparse MoE agentic reasoning model from Liquid AI",
            "sameAs":[SOURCES["model"],SOURCES["gguf"]],
        },
        {
            "@type":"BreadcrumbList","@id":URL+"#breadcrumbs",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":"https://sxf.si/"},
                {"@type":"ListItem","position":2,"name":"Models","item":"https://sxf.si/models/"},
                {"@type":"ListItem","position":3,"name":"LFM2.5-24B-A2B","item":URL},
            ],
        },
        {
            "@type":"FAQPage","@id":URL+"#faq",
            "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}
                          for q,a in FAQ],
        },
    ]}


def quant_rows():
    return "".join(
        '<tr><th scope="row">'+escape(name)+'</th><td>'+str(size)+' GB</td><td>'
        +escape(note)+'</td></tr>' for name,size,note in QUANTS
    )


def benchmark_rows():
    return "".join(
        '<tr><th scope="row">'+escape(task)+'</th><td>'+escape(category)+'</td><td>'
        +our+'</td><td>'+qwen+'</td><td>'+escape(note)+'</td></tr>'
        for task,category,our,qwen,note in BENCHMARKS
    )


ARTICLE = r'''
<section class="shell lfm24-hero" aria-labelledby="lfm24-title" id="top">
  <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>LFM2.5-24B-A2B</span></nav>
  <p class="eyebrow">MODEL INTELLIGENCE / LIQUID AI / SOURCE-VERIFIED</p>
  <h1 id="lfm24-title">LFM2.5-24B-A2B <span>explained.</span></h1>
  <p class="lfm24-intro"><strong>24 billion total parameters. About 2.45 billion active per token. 131K context.</strong> Liquid AI's October 2026 open-weight reasoning model targets fast, private tool-using agents on consumer hardware. Compare the official benchmarks, weight sizes, running instructions, licensing and API rates—then test your device's weight budget in the original SXF Local Fit Lab.</p>
  <p class="lfm24-reality"><strong>Critical memory distinction:</strong> 2.45B <em>active</em> parameters do not mean that a 2.45B-size weight file is enough. Sparse experts need to be stored or offloaded. The quantized 24B weight files are roughly <strong>13.6–25.5 GB</strong>; 16-bit files are around <strong>48 GB</strong>, before runtime and KV cache.</p>
  <div class="lfm24-metrics" aria-label="Confirmed model statistics">
    <div><strong>24.0B</strong><span>Total parameters</span></div>
    <div><strong>2.45B</strong><span>Active per token</span></div>
    <div><strong>131,072</strong><span>Context tokens</span></div>
    <div><strong>64</strong><span>Experts per MoE block</span></div>
  </div>
  <div class="lfm24-actions"><a class="lfm24-primary" href="#fit-lab">Check local memory fit</a><a href="#benchmarks">See benchmarks</a><a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B" target="_blank" rel="noopener noreferrer">Official model card ↗</a></div>
  <p class="lfm24-small">Released October 13, 2026 · Sources reviewed November 1, 2026 · Benchmarks are Liquid AI's published measurements, not independent SXF testing.</p>
</section>
<div class="shell lfm24-layout">
<aside class="lfm24-sidebar"><div class="lfm24-nav"><strong>ON THIS PAGE</strong><nav aria-label="Article contents">
  <a href="#overview">Quick answer</a><a href="#specifications">Specifications</a><a href="#moe">How MoE works</a><a href="#fit-lab">SXF Local Fit Lab</a><a href="#quantization">Quantization sizes</a><a href="#benchmarks">Benchmarks</a><a href="#speed">Speed tests</a><a href="#run-local">Local setup</a><a href="#api">API cost</a><a href="#comparisons">Model comparisons</a><a href="#use-cases">Use cases</a><a href="#limitations">Limitations</a><a href="#faq">FAQ</a><a href="#sources">Sources</a>
</nav></div></aside>
<div class="lfm24-article">
<section class="lfm24-section" id="overview">
  <p class="eyebrow">DIRECT ANSWER</p><h2>What is LFM2.5-24B-A2B?</h2>
  <p><strong>LFM2.5-24B-A2B is Liquid AI's text-only, mixture-of-experts (MoE) reasoning model designed for local agents and tool use.</strong> It contains about 24B total parameters, of which 2.45B are active for each token. Released on October 13, 2026, it is the largest final member of the LFM2.5 series. The post-trained checkpoint is tuned for multi-step tool workflows; a separate <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-Base" target="_blank" rel="noopener noreferrer">base model</a> supports customization. <a href="https://www.liquid.ai/blog/lfm2-5-24b-a2b" target="_blank" rel="noopener noreferrer">Liquid AI's launch announcement</a> provides the architectural and evaluation background.</p>
  <p>It is <strong>not a vision-language or speech model</strong>. Its documented interface is text in, text out. A tool-using agent can combine it with external code, web retrieval or document processing—but those capabilities depend on the agent harness, permissions, connectors and prompt format, not on native image or microphone input.</p>
  <div class="lfm24-callout"><strong>Best fit:</strong> local instruction-following and agentic automation where tool reliability, data control and decode efficiency matter. <strong>Less certain:</strong> knowledge-intensive questions, challenging web navigation, complex software engineering and low-memory laptops running long contexts.</div>
</section>
<section class="lfm24-section" id="specifications">
  <p class="eyebrow">OFFICIAL MODEL CARD</p><h2>LFM2.5-24B-A2B specifications and context window</h2>
  <div class="lfm24-table-wrap"><table><caption>Published model attributes; specific numbers from the Liquid AI model card</caption><tbody>
    <tr><th scope="row">Model ID</th><td><code>LiquidAI/LFM2.5-24B-A2B</code></td></tr>
    <tr><th scope="row">Developer / release</th><td>Liquid AI · October 13, 2026</td></tr>
    <tr><th scope="row">Modality / behavior</th><td>Text input and output; reasoning-first post-trained agent model</td></tr>
    <tr><th scope="row">Total / active parameters</th><td>24.0B total / 2.45B active per token; A2B is a rounded product label</td></tr>
    <tr><th scope="row">Context window</th><td><strong>131,072 tokens</strong> (model limit, not guaranteed usable memory)</td></tr>
    <tr><th scope="row">Layers</th><td>40: 30 double-gated short convolution blocks and 10 grouped-query attention blocks</td></tr>
    <tr><th scope="row">Expert routing</th><td>64 experts per MoE block, top-4 routing</td></tr>
    <tr><th scope="row">Vocabulary</th><td>128,000 tokens</td></tr>
    <tr><th scope="row">Training</th><td>Official model card: 36T-token training budget. Launch blog details 33T pre-training plus mid-training phases.</td></tr>
    <tr><th scope="row">Official generation preset</th><td><code>temperature 0.1</code>, <code>top_k 50</code>, <code>repetition_penalty 1.05</code></td></tr>
    <tr><th scope="row">Distribution</th><td>Native safetensors; official FP8; official GGUF quantizations; MLX ecosystem support</td></tr>
    <tr><th scope="row">License</th><td>LFM Open License v1.0 (<code>lfm1.0</code>); inspect commercial and redistribution terms</td></tr>
  </tbody></table></div>
  <p class="lfm24-evidence">Model-card evidence: <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B" target="_blank" rel="noopener noreferrer">LiquidAI/LFM2.5-24B-A2B</a>. The context value is a <em>maximum model specification</em>; long-context recall and actual runtime capacity must be measured separately.</p>
</section>
<section class="lfm24-section" id="moe">
  <p class="eyebrow">ARCHITECTURE EXPLAINED</p><h2>24B total vs 2.45B active: how the MoE model works</h2>
  <p>The sparse MoE router chooses <strong>four of 64 experts</strong> at each applicable expert block for a token. This reduces work per token relative to evaluating all experts, but every expert still occupies weight storage unless the runtime offloads or streams it. Lower computation does not imply the same RAM requirements as a dense 2B model.</p>
  <div class="lfm24-flow" role="list" aria-label="Simplified LFM2.5 architecture stages">
    <div role="listitem"><span>01 / INPUT</span><strong>Tokenize</strong><p>Text is converted with the updated 128K-token vocabulary.</p></div>
    <div role="listitem"><span>02 / MIX</span><strong>Hybrid layers</strong><p>30 gated short-convolution blocks and 10 GQA blocks process context.</p></div>
    <div role="listitem"><span>03 / ROUTE</span><strong>Select top 4 experts</strong><p>Sparse expert paths execute for each token in MoE blocks.</p></div>
    <div role="listitem"><span>04 / REASON</span><strong>Generate answer</strong><p>The post-trained model generates reasoning and an eventual final answer; a harness controls tool execution.</p></div>
  </div>
  <p>Compared with <a href="https://www.liquid.ai/blog/lfm2-24b-a2b" target="_blank" rel="noopener noreferrer">LFM2-24B-A2B</a>, the later LFM2.5 release extends context from <strong>32,768 to 131,072</strong>, expands vocabulary from roughly 65K to 128K, and adds more pretraining and agentic post-training while retaining the 40-layer hybrid design. The October announcement describes a five-stage post-training process including SFT, distillation and agentic reinforcement learning; it also reports reward-hacking during training and tighter evaluation sandboxes.</p>
</section>
<section class="lfm24-section" id="fit-lab">
  <p class="eyebrow">ORIGINAL SXF INTERACTIVE EXPERIENCE</p><h2>SXF Local MoE Fit Lab: which quantization fits your machine?</h2>
  <p>Choose an official GGUF file, your available <strong>RAM or VRAM budget</strong>, and a reserve for the operating system, runtime and KV cache. The result compares <strong>file size against the remaining budget</strong>—it is <em>not</em> a measured memory test or an FPS/tokens-per-second prediction. The tool runs entirely in the browser; no data leaves this page.</p>
  <div class="lfm24-fit" data-lfm24-fit>
    <div class="lfm24-controls">
      <label for="lfm24-quant">Official GGUF quantization<select id="lfm24-quant" data-quant>
        <option value="13.6">Q4_0 / QAD · 13.6 GB</option>
        <option value="14.5" selected>Q4_K_M · 14.5 GB</option>
        <option value="17">Q5_K_M · 17.0 GB</option>
        <option value="19.7">Q6_K · 19.7 GB</option>
        <option value="25.5">Q8_0 · 25.5 GB</option>
        <option value="48">BF16 / F16 · 48.0 GB</option>
      </select></label>
      <label for="lfm24-budget">Available memory budget (decimal GB)<input id="lfm24-budget" data-budget type="number" inputmode="decimal" min="4" max="512" step="1" value="24" /></label>
      <label for="lfm24-reserve">Reserve for runtime, KV cache and OS (GB)<input id="lfm24-reserve" data-reserve type="range" min="2" max="32" step="1" value="6" /><output data-reserve-output for="lfm24-reserve">6 GB</output></label>
      <p class="lfm24-fit-note">Use <em>available</em> memory, not disk capacity. On a dedicated GPU enter its VRAM if you want full GPU residency. Partial CPU/GPU offloading is a separate, more complex scenario.</p>
    </div>
    <div class="lfm24-result">
      <span>WEIGHT BUDGET RESULT</span><strong data-fit-label aria-live="polite">Weights fit this illustrative budget</strong>
      <div class="lfm24-meter" role="meter" aria-label="Weight file share of usable memory budget" aria-valuemin="0" aria-valuemax="100" aria-valuenow="81"><i data-meter-bar style="width:81%"></i></div>
      <div class="lfm24-result-numbers"><div><small>File size</small><b data-weight>14.5 GB</b></div><div><small>Budget after reserve</small><b data-free>18.0 GB</b></div><div><small>Remaining after weights</small><b data-remaining>3.5 GB</b></div></div>
      <p data-fit-explain>File weights fit the selected budget on paper; real runtime, context and kernel allocations must be tested.</p>
      <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF" target="_blank" rel="noopener noreferrer">Open official GGUF downloads ↗</a>
    </div>
  </div>
  <p class="lfm24-small">SXF calculation: <code>available weight budget = selected memory − reserve</code>; <code>headroom = budget − published file size</code>. Both input units and GGUF file sizes use decimal GB. The reserve is user-supplied, <strong>not</strong> a validated KV cache estimator. For 131K contexts, real memory may greatly exceed the chosen reserve.</p>
</section>
<section class="lfm24-section" id="quantization">
  <p class="eyebrow">REAL DOWNLOAD SIZE</p><h2>LFM2.5-24B-A2B GGUF sizes: Q4, Q5, Q6, Q8 and BF16</h2>
  <p>Liquid AI distributes first-party quantized builds. The numbers below are the published <strong>download weight sizes</strong>, not end-to-end RAM or GPU VRAM requirements. GGUF variants may have different fidelity; speed and quality should be tested on your real tasks.</p>
  <div class="lfm24-table-wrap"><table><caption>Official LiquidAI GGUF model listing, decimal GB</caption><thead><tr><th scope="col">Quantization</th><th scope="col">Published file</th><th scope="col">What it changes</th></tr></thead><tbody><!-- QUANT_ROWS --></tbody></table></div>
  <p>The official <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF" target="_blank" rel="noopener noreferrer">Q4_0 Quantization-Aware Distillation (QAD)</a> variant has a distinct fine-tuned checkpoint designed to recover quantization accuracy; it is not necessarily equivalent to naive Q4_0 quantization. As a starting point, <strong>Q4_K_M weighs about 14.5 GB</strong>, while <strong>BF16 is around 48 GB</strong>. A 16GB laptop may not have adequate headroom to fully load a 14.5GB weight file plus runtime, OS and KV cache.</p>
  <h3>Why the model may not fit despite “2B active”</h3>
  <p>For MoE inference, the full collection of experts must be available in RAM/VRAM or offloaded to slower storage. The active parameter count primarily predicts a portion of compute, not how many bytes the entire model occupies. Very long contexts can add substantial cache pressure even when weight quantization is aggressive. Use actual peak RSS and GPU allocation measurements to confirm your deployment.</p>
</section>
<section class="lfm24-section" id="benchmarks">
  <p class="eyebrow">BENCHMARKS / REPORTED BY LIQUID AI</p><h2>LFM2.5-24B-A2B benchmarks vs Qwen3.6-35B-A3B</h2>
  <p>Liquid AI published <strong>16 benchmark comparisons</strong>. The subset below intentionally includes <em>both wins and losses</em>, using scores from the same vendor-published table. A higher score is better within each listed test, but task suites have different definitions, agent harnesses and sampling policies. SXF did not reproduce these evaluations.</p>
  <div class="lfm24-table-wrap"><table><caption>Selected official October 2026 evaluation scores; not a cross-benchmark average</caption><thead><tr><th scope="col">Test</th><th scope="col">Task</th><th scope="col">LFM2.5</th><th scope="col">Qwen3.6</th><th scope="col">Finding</th></tr></thead><tbody><!-- BENCH_ROWS --></tbody></table></div>
  <p><strong>Where it looks strongest:</strong> tool use, structured instructions, certain local-agent loops. <strong>Where it trails:</strong> harder web-agent navigation, expert knowledge and software-engineering evaluations in the published comparison. Notably, <strong>PinchBench (83.18 vs 89.93)</strong> is another published agent benchmark where Qwen scores higher; agentic performance is not one uniform dimension. <a href="https://www.liquid.ai/blog/lfm2-5-24b-a2b" target="_blank" rel="noopener noreferrer">Verify the complete 16-test table and settings ↗</a>.</p>
  <div class="lfm24-callout"><strong>Reproducibility checklist:</strong> match prompts, tool schema, sample counts, model revision, chat template, sampler, context budget, and harness. Liquid AI documents using vLLM, with temperature varying from 0 to 1 across tests and workload-specific generation caps. Do not compare these vendor results to arbitrary community charts without normalizing conditions.</div>
</section>
<section class="lfm24-section" id="speed">
  <p class="eyebrow">DECODE VS AGGREGATE THROUGHPUT</p><h2>Is LFM2.5-24B-A2B fast on a laptop or GPU?</h2>
  <div class="lfm24-speed"><article><span>APPLE M5 MAX</span><strong>184 tok/s</strong><p>Liquid AI's reported <em>edge decode</em> speed on-device using llama.cpp Q4_K_M and a 4K input prompt.</p></article><article><span>AMD RYZEN AI MAX+ 395</span><strong>114 tok/s</strong><p>Liquid AI's edge decode result in the same family of local benchmarks.</p></article><article><span>NVIDIA B300</span><strong>21K+ tok/s</strong><p>Aggregate output throughput at <em>high concurrency</em> with SGLang 0.5.22, BF16, 1,024 input / up to 256 output tokens.</p></article></div>
  <p><strong>Do not compare these as equal “chat speed” measurements.</strong> M5 Max and Ryzen numbers concern local single-workload decode. B300 figures sum output across many requests under sustained load; they do not mean one user's answer arrives at 21,000 tokens per second. Prompt processing, tool latency, CPU/GPU offload, context and model quantization all affect a real agent's wall-clock task time.</p>
</section>
<section class="lfm24-section" id="run-local">
  <p class="eyebrow">OFFICIAL CHECKPOINTS AND COMMANDS</p><h2>How to run LFM2.5-24B-A2B locally with llama.cpp</h2>
  <p>Use a recent llama.cpp build supporting <code>lfm2moe</code>, enough memory for the selected quantization, and the official model repo. This command follows Liquid AI's published GGUF instructions and includes its recommended generation preset:</p>
  <div class="lfm24-code"><div><span>Terminal · official GGUF</span><button type="button" data-lfm24-copy="gguf" aria-label="Copy llama.cpp GGUF command">Copy</button></div><pre id="lfm24-code-gguf"><code>llama-cli -hf LiquidAI/LFM2.5-24B-A2B-GGUF \
  --temp 0.1 --top-k 50 --repeat-penalty 1.05</code></pre></div>
  <p>To select the separately trained QAD variant explicitly:</p>
  <div class="lfm24-code"><div><span>Terminal · first-party QAD Q4_0</span><button type="button" data-lfm24-copy="qad" aria-label="Copy QAD command">Copy</button></div><pre id="lfm24-code-qad"><code>llama-cli -hf LiquidAI/LFM2.5-24B-A2B-GGUF \
  --hf-file LFM2.5-24B-A2B-QAD-Q4_0.gguf \
  --temp 0.1 --top-k 50 --repeat-penalty 1.05</code></pre></div>
  <h3>MLX, vLLM, SGLang and FP8</h3>
  <p>Liquid AI lists day-one support for <strong>MLX on Apple Silicon</strong>, <strong>vLLM / SGLang for GPU serving</strong>, and cross-platform <strong>ONNX</strong>. For multi-request serving, use the native <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B" target="_blank" rel="noopener noreferrer">safetensors model</a> or the official <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-FP8" target="_blank" rel="noopener noreferrer">FP8 checkpoint</a> according to runtime support. Do not use GGUF sample commands with a native vLLM model server without converting the setup.</p>
  <p>To make a private agent, connect a trusted local inference endpoint to an agent harness and narrowly scoped tools. Require confirmation before shell execution, deleting files, sending messages or authorizing payments; save an audit trail and measure tool-call correctness separately from text fluency. Local weights do not automatically make a tool-enabled agent safe.</p>
  <h3>Base vs post-trained: which checkpoint?</h3>
  <div class="lfm24-two"><article><h4>Post-trained LFM2.5-24B-A2B</h4><p>Choose for ordinary inference, reasoning and tool-using local agents. Instruction and agent behavior is already post-trained.</p><a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B" target="_blank" rel="noopener noreferrer">Post-trained checkpoint ↗</a></article><article><h4>Base LFM2.5-24B-A2B-Base</h4><p>Choose as a foundation for specialized continued training. The base model is not a drop-in instruct-chat replacement.</p><a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-Base" target="_blank" rel="noopener noreferrer">Base checkpoint ↗</a></article></div>
</section>
<section class="lfm24-section" id="api">
  <p class="eyebrow">PUBLISHED COMMERCIAL RATES</p><h2>LFM2.5-24B-A2B API pricing vs local inference</h2>
  <p>At its <strong>October 13, 2026</strong> launch, Liquid AI announced these Liquid Console rates. Treat them as dated evidence; check the current billing dashboard for the up-to-date model price and availability.</p>
  <div class="lfm24-prices"><div><strong>$0.10</strong><span>per 1M input tokens</span></div><div><strong>$0.05</strong><span>per 1M cached input tokens</span></div><div><strong>$1.00</strong><span>per 1M output tokens</span></div></div>
  <p>Self-hosted inference does not incur Liquid Console token fees, but does cost electricity, device memory, maintenance and engineering time. Reasoning-first models can produce additional output tokens; measure actual billable outputs instead of assuming the final visible answer length captures cost. See the <a href="/models/pricing/">SXF model pricing reference</a> for a broader cross-provider perspective.</p>
</section>
<section class="lfm24-section" id="comparisons">
  <p class="eyebrow">FAIR MODEL CHOICES</p><h2>LFM2.5-24B-A2B vs LFM2-24B-A2B, Qwen and LFM3</h2>
  <div class="lfm24-table-wrap"><table><caption>Comparison questions have different evidence bases</caption><thead><tr><th scope="col">Model</th><th scope="col">Meaningful difference</th><th scope="col">Best evaluation</th></tr></thead><tbody>
    <tr><th scope="row">LFM2-24B-A2B</th><td>Older related 24B MoE with 32,768 context; LFM2.5 extends context and tokenizer and adds further agentic training.</td><td>Compare identical tasks with matching quantization and memory.</td></tr>
    <tr><th scope="row">Qwen3.6-35B-A3B</th><td>Larger MoE in Liquid AI's published table; wins certain knowledge, web and software tasks, loses others.</td><td>Read individual benchmark rows; independently test your own agent workflow.</td></tr>
    <tr><th scope="row"><a href="/models/lfm3/">LFM3 family</a></th><td>Later compact model family spanning text, vision, audio and decisions; different architectures and parameter scales.</td><td>Choose by input type and actual workload, not raw name/version.</td></tr>
    <tr><th scope="row"><a href="/models/lfm2-5-vl-dspark/">LFM2.5-VL-DSpark</a></th><td>A <em>drafting accelerator</em> for a separate vision-language model, not another 24B agent.</td><td>Do not compare its speculative-decoding speedup with language-model accuracy scores.</td></tr>
  </tbody></table></div>
</section>
<section class="lfm24-section" id="use-cases">
  <p class="eyebrow">APPLICATION ENGINEERING</p><h2>Best uses for LFM2.5-24B-A2B local agents</h2>
  <div class="lfm24-use"><article><span>01 · TOOL AUTOMATION</span><h3>Local workflow agent</h3><p>Parse instructions, select a small whitelisted tool, confirm risky actions and record outcomes. Evaluate the actual tool-call success rate, not whether the reasoning narrative sounds plausible.</p></article><article><span>02 · PRIVATE DATA</span><h3>On-device document assistant</h3><p>Pair local weights with retrieval over permitted documents. Verify citations against source passages, especially on knowledge-heavy requests where the model trails stronger competitors.</p></article><article><span>03 · STRUCTURED OUTPUT</span><h3>Text extraction pipeline</h3><p>Use a schema validator, retries and deterministic acceptance checks. Report exact field accuracy and failure types on held-out customer data.</p></article><article><span>04 · MULTILINGUAL</span><h3>International support routing</h3><p>The expanded tokenizer supports a broader non-Latin vocabulary. Test Arabic, Chinese and other target languages with native examples; vocabulary size does not guarantee language parity.</p></article></div>
  <h3>SXF reproducible local-agent test protocol</h3>
  <ol><li>Pick 20–50 representative, permission-safe tasks and record expected outcomes.</li><li>Freeze the model revision, quantization, prompt template, sampler, context length and tool definitions.</li><li>Run tasks with and without external retrieval; record success, tool calls, retries, latency and failure cost.</li><li>Repeat each test under controlled conditions, including adversarial requests and attempts to bypass tool permissions.</li><li>Only then compare hardware cost and throughput; vendor performance numbers are not task-success guarantees.</li></ol>
</section>
<section class="lfm24-section" id="limitations">
  <p class="eyebrow">WHAT NOT TO ASSUME</p><h2>Limitations, licensing and benchmark caveats</h2>
  <ul>
    <li><strong>24B still needs memory:</strong> only 2.45B parameters are active per token, but stored expert weights are much larger.</li>
    <li><strong>Long context costs RAM:</strong> 131,072 tokens is a model specification, not a verified 131K-token laptop configuration or guarantee of perfect recall.</li>
    <li><strong>Text-only:</strong> images and audio require a separate model or preprocessing components.</li>
    <li><strong>Reasoning text is not proof:</strong> explicit reasoning generation can still contain errors and may consume additional output tokens.</li>
    <li><strong>Different benchmark domains disagree:</strong> its published agentic strengths do not translate automatically to expert Q&A, difficult browsing and coding.</li>
    <li><strong>Safety:</strong> Liquid AI reports discovering reward-hacking during training; restrict tools and revalidate behavior in your own environment.</li>
    <li><strong>Open-weight license:</strong> review <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">LFM Open License v1.0</a>; accessible weights are not automatically unrestricted open-source software.</li>
    <li><strong>API pricing changes:</strong> published launch rates and credits may not reflect later billing or regional availability.</li>
  </ul>
</section>
<section class="lfm24-section" id="faq">
  <p class="eyebrow">DIRECT SEARCH ANSWERS</p><h2>LFM2.5-24B-A2B frequently asked questions</h2>
  <div class="lfm24-faq">
    <details><summary>What is LFM2.5-24B-A2B?</summary><p>Liquid AI's text-only 24B-parameter MoE reasoning model with approximately 2.45B active parameters per token, released on October 13, 2026 for tool-using local agents.</p></details>
    <details><summary>Why is it called A2B if 2.45B parameters are active?</summary><p>A2B is a rounded name. The official model card reports 2.45B active and 24.0B total parameters. The full weight set still needs memory or offloading.</p></details>
    <details><summary>What is the context length?</summary><p>131,072 tokens as published by Liquid AI. Actual machine capacity and long-context retrieval quality require separate verification.</p></details>
    <details><summary>Can I run it with 16 GB RAM?</summary><p>Its official Q4_0 file is about 13.6 GB, and Q4_K_M is about 14.5 GB, leaving little room for the OS and KV cache in a 16 GB configuration. Full on-device fit is not guaranteed.</p></details>
    <details><summary>Which GGUF quantization should I try first?</summary><p>Choose based on available memory and quality requirements. Liquid AI publishes Q4_0/QAD, Q4_K_M, Q5_K_M, Q6_K and higher-precision versions. The SXF fit tool compares their weight sizes but does not predict total RAM usage.</p></details>
    <details><summary>Is it faster than Qwen3.6-35B-A3B?</summary><p>Liquid AI claims up to 1.7 times faster on certain edge measurements; benchmark accuracy varies by task. Qwen wins some of the vendor's WebArena, knowledge and coding evaluations.</p></details>
    <details><summary>Can I run it with llama.cpp?</summary><p>Yes, using a compatible recent build and the official LiquidAI GGUF repository. A verified command and sampling preset are shown above.</p></details>
    <details><summary>Does it support image input?</summary><p>No. It is a text-only reasoning model, separate from Liquid AI's vision-language family.</p></details>
    <details><summary>How much is the API?</summary><p>At launch, Liquid AI reported $0.10 per million input tokens, $0.05 cached input and $1.00 output. Verify current rates with Liquid Console.</p></details>
    <details><summary>Is it commercially unrestricted open-source?</summary><p>It is distributed as open weights under LFM Open License v1.0. Read that license's commercial and redistribution conditions before deploying.</p></details>
    <details><summary>What changed from LFM2-24B-A2B?</summary><p>The successor offers 131,072 instead of 32,768 context tokens, a 128K instead of roughly 65K vocabulary, and more reasoning/agent training.</p></details>
    <details><summary>Is there a separately trainable base model?</summary><p>Yes. Liquid AI distributes LFM2.5-24B-A2B-Base for customization, separately from the post-trained agent model.</p></details>
  </div>
</section>
<section class="lfm24-section" id="sources">
  <p class="eyebrow">PRIMARY EVIDENCE REGISTER</p><h2>Official sources and SXF verification standard</h2>
  <p>Editorial evidence reviewed <strong>November 1, 2026</strong>. Vendor-reported figures are labeled as such. The interactive weight-budget tool and local evaluation protocol are original SXF explanatory work; they do not represent an independently tested model or a measured hardware configuration.</p>
  <div class="lfm24-sources">
    <a href="https://www.liquid.ai/blog/lfm2-5-24b-a2b" target="_blank" rel="noopener noreferrer"><strong>Liquid AI launch report</strong><span>Architecture, training, official benchmarks, speed and October API rates ↗</span></a>
    <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B" target="_blank" rel="noopener noreferrer"><strong>Official post-trained model card</strong><span>Precise active parameters, 131K context, benchmarks and generation settings ↗</span></a>
    <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF" target="_blank" rel="noopener noreferrer"><strong>Official GGUF quantization repository</strong><span>Weight file sizes, QAD notes and llama.cpp commands ↗</span></a>
    <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-Base" target="_blank" rel="noopener noreferrer"><strong>Base checkpoint</strong><span>Pre-trained starting point for model adaptation ↗</span></a>
    <a href="https://www.liquid.ai/blog/lfm2-24b-a2b" target="_blank" rel="noopener noreferrer"><strong>Previous-generation LFM2-24B-A2B release</strong><span>Earlier model, 32K context and prior positioning ↗</span></a>
    <a href="https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/main/LICENSE" target="_blank" rel="noopener noreferrer"><strong>LFM license</strong><span>Read the actual use and redistribution terms ↗</span></a>
  </div>
  <p class="lfm24-related"><strong>More SXF model intelligence:</strong> <a href="/models/lfm3/">LFM3 family</a> · <a href="/models/lfm2-5-vl-dspark/">LFM2.5-VL-DSpark</a> · <a href="/guides/open-source-ai-models/">Open-weight AI models</a> · <a href="/guides/run-ai-models-locally/">Running models locally</a> · <a href="/guides/llm-quantization-explained/">LLM quantization</a> · <a href="/signals/run-fast-private-agents-on-device-with-lfm2-5-24b-a2b-550c4c0/">Original SXF release signal</a>.</p>
</section>
</div></div>
'''


def render_page(items, *, page_head, page_header, page_footer):
    head = page_head(
        TITLE, DESCRIPTION, URL, schema(), "article",
        "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
    )
    head = head.replace(
        "</head>", '<link rel="stylesheet" href="/assets/lfm25-24b-model.css" /></head>', 1
    )
    recent = ""
    if items:
        latest = items[0]
        title = escape(latest.get("title", "LFM2.5-24B-A2B release news"))
        slug = escape(latest.get("signal_slug", ""), quote=True)
        recent = (
            '<section class="shell lfm24-recent"><p class="eyebrow">LATEST SXF NEWS</p>'
            '<h2>Latest LFM2.5-24B-A2B source signal</h2><p>' + title + '</p>'
            '<a href="/signals/' + slug + '/">Read the dated release signal ↗</a></section>'
        )
    article = (ARTICLE.replace("<!-- QUANT_ROWS -->", quant_rows())
                      .replace("<!-- BENCH_ROWS -->", benchmark_rows()))
    return (
        '<!doctype html><html lang="en">' + head
        + '<body class="intel-page model-page sxf-lfm24">' + page_header("models")
        + '<main id="main-content">' + article + recent + '</main>'
        + page_footer()
        + '<script src="/assets/lfm25-24b-model.js" defer></script></body></html>'
    )
