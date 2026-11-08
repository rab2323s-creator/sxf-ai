"""Verified SXF Claude Haiku 5.5 Copilot editorial, preserved across Signals builds.

The source publication is October 7, 2026; editorial review is November 8.
Plan, credit and price claims cite GitHub; benchmark claims cite Anthropic.
"""
import json
import re
from html import escape
CANONICAL = "https://sxf.si/signals/claude-haiku-5-5-in-github-copilot-86f546d/"
TITLE = "Claude Haiku 5.5 in GitHub Copilot: Plans & Cost | SXF"
H1 = "Claude Haiku 5.5 in GitHub Copilot: Availability, Pricing & Use Cases"
DESCRIPTION = "Claude Haiku 5.5 is in GitHub Copilot. Check eligible plans, VS Code and CLI support, AI credit pricing, 100K token threshold and SXF's coding analysis."
SOURCES = ["https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/","https://github.blog/changelog/2026-10-09-github-copilot-weekly-releases-october-5/","https://docs.github.com/en/copilot/reference/ai-models/supported-models","https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing","https://docs.github.com/en/copilot/reference/ai-models/model-comparison","https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-access-to-ai-models","https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-default-models","https://docs.github.com/en/copilot/how-tos/github-copilot-app/choose-a-model","https://www.anthropic.com/claude-haiku-5-5","https://www.anthropic.com/claude/haiku","https://www.anthropic.com/transparency"]
KEYWORDS = ["Claude Haiku 5.5 GitHub Copilot","Claude Haiku 5.5 in Copilot","GitHub Copilot Haiku 5.5 availability","GitHub Copilot Haiku 5.5 pricing","Claude Haiku 5.5 VS Code","Claude Haiku 5.5 Copilot CLI","Claude Haiku 5.5 GitHub Business Enterprise","Haiku 5.5 vs Sonnet 5.5 Copilot","Claude Haiku 5.5 AI Credits","Claude Haiku 5.5 100k tokens pricing","GitHub Copilot model picker Claude","Anthropic Haiku 5.5 coding model"]
FAQ = [["Is Claude Haiku 5.5 available in GitHub Copilot?","Yes. GitHub announced general availability on October 7, 2026 for eligible Copilot subscriptions, with a gradual rollout across supported clients."],["Which Copilot plans support Claude Haiku 5.5?","GitHub's announcement names Copilot Pro, Pro+, Max, Business and Enterprise. GitHub documents that Free and Student generally rely on auto model selection rather than direct manual selection."],["Where can I select Claude Haiku 5.5 in Copilot?","GitHub lists Visual Studio Code, Visual Studio, Copilot CLI, cloud agent, the Copilot app, github.com, GitHub Mobile, JetBrains IDEs, Xcode and Eclipse. Client support and availability can change."],["Why can't I see Claude Haiku 5.5 in the model picker?","The rollout is gradual, eligibility depends on plan and supported client, and organization or enterprise policies can disable the model. Check GitHub's supported-model list and admin settings."],["How much does Claude Haiku 5.5 cost in GitHub Copilot?","GitHub's listed default prices for prompts at or below 100K input tokens are $0.10 per million uncached input tokens, $0.01 per million cached input tokens, $0.125 per million cache-write tokens and $0.50 per million output tokens. Larger prompts have higher long-context tier rates. Costs are converted into GitHub AI credits, with 1 credit equivalent to $0.01."],["Is the model free with Copilot Pro?","Copilot plans include varying allowances of GitHub AI Credits. Model usage consumes credits under usage-based billing, and additional spending may apply after an allowance is exhausted depending on plan and budget settings. It is not accurate to promise unlimited free Haiku 5.5 chat usage."],["Is Haiku 5.5 better than Sonnet 5.5 for coding?","Haiku 5.5 is optimized for fast scoped edits and subagent tasks. Anthropic reports Sonnet 5.5 substantially higher on demanding Terminal-Bench 4.0 agentic coding work, so performance and total cost must be evaluated by task."],["Can an organization enable Haiku 5.5 for Business or Enterprise users?","Yes. GitHub supports model access policies for organizations and enterprises. An administrator can enable or disable models where the enterprise has delegated the setting."],["Is Anthropic API pricing the same as GitHub Copilot billing?","The displayed per-token rates are similar to Anthropic's published model rates, but GitHub Copilot measures use in AI credits within Copilot plans; Anthropic direct API billing is a separate service. Do not use a Claude subscription price to estimate Copilot cost."],["What is a good task to test Claude Haiku 5.5 first?","SXF suggests a small test-covered code edit, a documentation update, a simple terminal explanation or a narrow subagent task. Record correctness, latency, tool use, reviewer time, token usage and total cost before routing wider work to the model."]]
BRIEF = r'''<section class="signal-layout shell">
<article class="signal-brief">
<p class="eyebrow">SXF / VERIFIED COPILOT MODEL BRIEF · REVIEWED NOVEMBER 8, 2026</p>
<p class="signal-summary"><strong>Claude Haiku 5.5 became generally available in GitHub Copilot on October 7, 2026.</strong> GitHub lists access for <strong>Pro, Pro+, Max, Business and Enterprise</strong> users through supported editors, Copilot CLI and other Copilot surfaces, with a <strong>gradual rollout</strong>. The lightweight Anthropic model targets fast edits, short terminal tasks and narrowly scoped subagents—not guaranteed replacement of stronger models on complex coding work.</p>
<div class="signal-context"><span>PRICING FACT</span><p>Copilot uses <strong>AI Credits</strong> with token-based billing. For input prompts of <strong>100K tokens or fewer</strong>, GitHub lists Haiku 5.5 at <strong>$0.10 / 1M input</strong> and <strong>$0.50 / 1M output</strong>; larger inputs use a higher rate. Cached reads and cache writes have separate prices. Plan allowances and budget controls determine possible extra charges.</p></div>
<div class="signal-context"><span>SXF EDITORIAL VIEW</span><p>Haiku 5.5 is most interesting for <strong>frequent, bounded engineering steps</strong>. Measure accepted edits, retries, human review and total AI-credit usage. More expensive models can still be a better value for difficult multi-file debugging or long-running architecture changes.</p></div>
</article><aside class="source-card"><span class="source-card-label">PRIMARY ANNOUNCEMENT</span><strong>GitHub · October 7, 2026</strong><p>GitHub's release, current model pricing and Anthropic's technical announcement underpin this analysis.</p>
<a href="https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/" target="_blank" rel="noopener noreferrer">Read GitHub's original announcement ↗</a><p><a href="https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing" target="_blank" rel="noopener noreferrer">Current GitHub model prices ↗</a></p>
<p><small>Last checked November 8, 2026. SXF does not claim independent Copilot benchmark runs.</small></p></aside></section>'''
BODY = r'''<section class="signal-deep-dive shell haiku55-report" data-sxf-haiku55-copilot="2026-11-08" aria-labelledby="haiku55-summary">
<div class="intel-section-head"><div><p class="eyebrow">SXF / INDEPENDENT CODING AI ANALYSIS</p><h2 id="haiku55-summary">Claude Haiku 5.5 in GitHub Copilot: a fast coding model with a clear cost trade-off.</h2></div><span>Source-checked November 8, 2026</span></div>
<p class="h55-lead">GitHub announced <strong>Claude Haiku 5.5 in GitHub Copilot</strong> on <time datetime="2026-10-07">October 7, 2026</time>, calling the Anthropic lightweight model <strong>generally available</strong> to eligible Copilot users, subject to rollout. Searchers asking <strong>“Does Copilot support Haiku 5.5?”, “What plans can use it?”, “How much does it cost?”</strong> or <strong>“Haiku vs Sonnet for coding?”</strong> need different answers. This SXF guide verifies the supported plans and clients, documents GitHub's usage-based AI Credits and 100K-token pricing threshold, and explains why a faster and cheaper model may be a better subagent than a lead agent. Our analysis is distinct from GitHub's and Anthropic's own performance claims. <a href="https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/" target="_blank" rel="noopener noreferrer">Primary source: GitHub Changelog</a>.</p>
<div class="h55-facts"><div><span>GITHUB RELEASE</span><strong>October 7, 2026</strong><small>Generally available · phased rollout</small></div>
<div><span>ELIGIBLE PLANS</span><strong>Pro · Pro+ · Max</strong><small>Plus Business and Enterprise</small></div>
<div><span>BEST STARTING USE</span><strong>Quick, scoped edits</strong><small>Subagents · terminal assistance</small></div><div><span>COPILOT PRICING</span><strong>Token-based AI Credits</strong><small>Higher rates over 100K input tokens</small></div></div>
<nav class="h55-toc" aria-label="Article navigation"><strong>Sections</strong><a href="#h55-launch">Launch</a><a href="#h55-access">Plans</a><a href="#h55-enable">How to enable</a><a href="#h55-workflows">Use cases</a><a href="#h55-prices">Pricing</a><a href="#h55-compare">Sonnet vs Haiku</a><a href="#h55-claims">Evidence</a><a href="#h55-sxf">SXF analysis</a><a href="#h55-faq">FAQ</a></nav>
<section id="h55-launch">
<h2>When did Claude Haiku 5.5 launch in GitHub Copilot?</h2>
<p><strong>October 7, 2026</strong> is the official GitHub Copilot release date. GitHub's changelog says Anthropic's new lightweight model is generally available for supported paid Copilot plans, and describes its main target as <strong>fast, high-volume work</strong>: subagents, small code edits and terminal tasks. GitHub's <a href="https://github.blog/changelog/2026-10-09-github-copilot-weekly-releases-october-5/" target="_blank" rel="noopener noreferrer">October 5 weekly-release roundup</a>, published October 9, repeats the Haiku availability announcement. That recap is a secondary GitHub source, not a different launch date.</p>
<p>The phrase <em>generally available</em> describes the release status. GitHub separately states the <strong>rollout is gradual</strong>, so a user meeting plan requirements may not see the model immediately. This is not an experimental model-only preview. The original GitHub announcement also reports early testing in which Haiku 5.5 matched Claude Sonnet 5 on many coding tasks while requiring fewer tokens and steps. It does not publish enough details there to infer equal results on all tasks, across all repositories or against <em>Sonnet 5.5</em>. <a href="https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/" target="_blank" rel="noopener noreferrer">Check the exact GitHub wording</a>.</p>
<h3>Is Haiku 5.5 a GitHub model or an Anthropic model?</h3><p><strong>It is made by Anthropic and offered as a choice inside GitHub Copilot.</strong> Anthropic separately released Haiku 5.5 on its own API and Claude products that day. Selecting it within Copilot uses GitHub's supported model integrations, policy layer and billing. It is not the same action as buying an Anthropic API subscription or calling Anthropic's <code>claude-haiku-5-5</code> model identifier directly. <a href="https://www.anthropic.com/claude-haiku-5-5" target="_blank" rel="noopener noreferrer">Anthropic's model announcement</a>.</p>
</section>
<section id="h55-access">
<h2>Which GitHub Copilot plans and editors support Haiku 5.5?</h2>
<p>GitHub's announcement explicitly lists <strong>Copilot Pro, Pro+, Max, Business and Enterprise</strong>. Its current supported-model guide confirms plan and client eligibility can change. <strong>Copilot Free and Student</strong> use auto model selection rather than the same direct manual model picker, so this is not a promise of independently selecting Haiku 5.5 on those plans. Organization restrictions can also override what appears in the model picker. <a href="https://docs.github.com/en/copilot/reference/ai-models/supported-models" target="_blank" rel="noopener noreferrer">Supported models by plan and client</a>.</p>
<div class="h55-scroll"><table class="h55-table"><thead><tr><th>Surface or client</th><th>Listed in October 7 announcement?</th><th>Practical note</th></tr></thead><tbody>
<tr><th>Visual Studio Code</th><td>Yes</td><td>Choose the model in supported Copilot Chat / agent model pickers</td></tr>
<tr><th>Visual Studio</th><td>Yes</td><td>Client version and model-list rollout affect visibility</td></tr>
<tr><th>Copilot CLI</th><td>Yes</td><td>Use the CLI's available model selector in a supported session</td></tr>
<tr><th>Cloud agent and Copilot app</th><td>Yes</td><td>Which session allows changing the model depends on product workflow</td></tr>
<tr><th>GitHub.com and GitHub Mobile</th><td>Yes</td><td>Supported web and iOS/Android experiences</td></tr>
<tr><th>JetBrains IDEs</th><td>Yes</td><td>Choose within the supported Copilot client</td></tr>
<tr><th>Xcode and Eclipse</th><td>Yes</td><td>GitHub lists both; verify local extension support and rollout</td></tr>
</tbody></table></div>
<p>This list concerns <strong>where the model was announced as selectable</strong>. It does not mean that every Copilot feature, such as inline next-edit suggestions, exposes the same per-model control or uses the same billing method. GitHub's <a href="https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing" target="_blank" rel="noopener noreferrer">billing reference</a> treats code completions and next-edit suggestions differently from metered AI-credit interactions.</p>
</section>
<section id="h55-enable">
<h2>How to enable or select Claude Haiku 5.5 in Copilot</h2>
<p>For an eligible individual user, start in a supported Copilot client, open a chat or agent session with a model picker, select <strong>Claude Haiku 5.5</strong> and give it a bounded coding task. On the GitHub Copilot app, GitHub documents selecting the current model near the prompt box and choosing another available model; a choice may take effect after an active turn finishes. The exact controls differ among VS Code, JetBrains and the CLI. <a href="https://docs.github.com/en/copilot/how-tos/github-copilot-app/choose-a-model" target="_blank" rel="noopener noreferrer">Official Copilot app selection steps</a>.</p>
<ol class="h55-steps"><li><strong>Check plan:</strong> confirm a currently supported Pro, Pro+, Max, Business or Enterprise seat.</li>
<li><strong>Check client:</strong> update or open the Copilot interface listed by GitHub and locate its model picker.</li>
<li><strong>For work accounts:</strong> check whether an organization or enterprise policy permits this Anthropic model.</li>
<li><strong>Select Haiku 5.5:</strong> use the named model rather than assuming an Auto/Fusion route will pick it.</li>
<li><strong>Start with a testable request:</strong> for example, improve one function and run its existing unit tests in an authorized workspace.</li>
<li><strong>Review cost and output:</strong> assess the patch, failures and AI-credit consumption before making it a team default.</li></ol>
<h3>What if Haiku 5.5 is missing from the model picker?</h3><p>First check the <a href="https://docs.github.com/en/copilot/reference/ai-models/supported-models" target="_blank" rel="noopener noreferrer">current GitHub model list</a>. Then confirm your plan, supported client, software version and gradual rollout status. For Copilot Business and Enterprise, admins can configure model access in GitHub Copilot settings. GitHub's <a href="https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-access-to-ai-models" target="_blank" rel="noopener noreferrer">model access guide</a> explains that policy controls can prevent a model from appearing even if the member has a seat.</p>
<h3>How do organization admins manage it?</h3><p>GitHub's docs describe an organization owner's path through <strong>Organization Settings → Copilot → Models</strong>. When delegated by enterprise policy, a model may be marked Enabled, Disabled or inherit a Default availability setting. An enforced enterprise policy cannot be overridden at the organization level. <a href="https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-default-models" target="_blank" rel="noopener noreferrer">Official model admin controls</a>.</p>
</section>
<section id="h55-workflows">
<h2>Best Claude Haiku 5.5 use cases in GitHub Copilot</h2>
<p>The model's advantage is not that it makes expensive engineering judgment unnecessary. It is positioned for <strong>small, well-defined steps that occur often</strong>. The examples below combine GitHub's stated focus with SXF's recommended acceptance checks; they are proposed uses, not firsthand benchmark results.</p>
<div class="h55-grid">
<article><span>01 / QUICK EDIT</span><h3>Small code changes</h3><p>Rename a function, update validation logic or refactor a small module with explicit expected behavior. Accept only a reviewed diff with relevant passing tests.</p></article>
<article><span>02 / TERMINAL HELP</span><h3>Command explanations and narrow fixes</h3><p>Ask for a concise explanation of a test failure or command. Inspect any suggested shell action before running it, especially destructive commands.</p></article>
<article><span>03 / SUBAGENTS</span><h3>Focused delegated work</h3><p>Let a stronger planner delegate log summarization, file lookup or documentation synthesis while retaining architecture and final integration decisions.</p></article>
<article><span>04 / REPEATED WORK</span><h3>Documentation and triage</h3><p>Produce change summaries, classify straightforward issues or update structured documentation under a clear schema and validation rules.</p></article>
</div>
<p>GitHub's <a href="https://docs.github.com/en/copilot/reference/ai-models/model-comparison" target="_blank" rel="noopener noreferrer">official model comparison</a> recommends Haiku 5.5 for quick, reliable responses to lightweight coding questions. Anthropic separately highlights classification, summarization, compaction and browser-oriented tasks; those are capabilities of the <em>base model</em>, not a guarantee that every Anthropic API feature is exposed identically inside every Copilot client. For agent context see <a href="/guides/what-is-agentic-ai/">SXF's agentic AI guide</a>.</p>
<h3>Example prompt for a focused Copilot task</h3>
<div class="h55-example"><p><strong>Original SXF sample:</strong> “In <code>src/formatDate.ts</code>, fix the empty-input behavior without changing valid date formatting. Reproduce with a failing unit test, update only the function and its test file, run the relevant tests, and report the diff plus any unverified cases. Do not modify dependencies or deployment settings.”</p></div>
<p>This prompt is deliberately narrow. It defines the permitted files, the test, and the evidence expected on completion. A model that merely explains a change without producing or validating it should not be counted as a successful coding agent run.</p>
</section>
<section id="h55-prices">
<h2>Claude Haiku 5.5 GitHub Copilot pricing and AI Credits explained</h2>
<p>GitHub moved Copilot model interactions to <strong>per-token usage-based billing</strong>: input, output, cached-input reads and cache writes can contribute to the price. Usage converts to <strong>GitHub AI Credits</strong>, where <strong>1 credit = $0.01 USD</strong>. Included credit allowances vary by Copilot plan, and overages depend on budget controls and billing settings. These facts come from GitHub's <a href="https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing" target="_blank" rel="noopener noreferrer">current Models and pricing documentation</a>, not an estimate by SXF.</p>
<div class="h55-scroll"><table class="h55-table"><thead><tr><th>Copilot Haiku 5.5 price</th><th>Up to 100K input tokens</th><th>Over 100K input tokens</th></tr></thead><tbody>
<tr><th>Input (uncached)</th><td>$0.10 / 1M tokens</td><td>$0.50 / 1M tokens</td></tr>
<tr><th>Cached input read</th><td>$0.01 / 1M tokens</td><td>$0.05 / 1M tokens</td></tr>
<tr><th>Cache write</th><td>$0.125 / 1M tokens</td><td>$0.625 / 1M tokens</td></tr>
<tr><th>Output</th><td>$0.50 / 1M tokens</td><td>$2.50 / 1M tokens</td></tr>
</tbody></table></div>
<p><strong>Critical threshold:</strong> The higher tier applies to requests whose input length exceeds 100,000 tokens. Do not assume a long repository context keeps the lower unit price. The table presents GitHub's listed token rates for this model as reviewed November 8, 2026. Plan allowances, routing, tools and caching affect actual credit use. Direct Anthropic API billing is a different service even when its public model token rates resemble GitHub's.</p>
<h3>Worked example: what would a short Copilot task cost?</h3>
<p>For an <em>illustrative</em> task using 20,000 <strong>uncached</strong> input tokens and 2,000 output tokens, with no cache writes, retries or extra tool charges, the listed rate calculation is: input <strong>$0.002</strong> (0.02 million × $0.10), plus output <strong>$0.001</strong> (0.002 million × $0.50), or <strong>$0.003 total</strong>. At GitHub's conversion, that is <strong>0.3 AI Credits</strong>. This is pure token arithmetic, <strong>not a measured Copilot session bill</strong> or a guarantee of how many requests a subscription includes.</p>
<p>For a prompt over 100K input tokens, rates change substantially. Before sending huge contexts to a lightweight model, ask whether a smaller relevant file selection, a task-specific summary or a better retrieval strategy could reduce cost <em>and</em> improve relevance. See <a href="/tools/ai-model-cost-calculator/">SXF's AI model cost calculator</a> and <a href="/models/pricing/">model pricing directory</a> for broader comparisons; verify any platform-specific fees directly in GitHub.</p>
<h3>Are inline code completions billed the same way?</h3><p>No. GitHub's billing page says <strong>code completions and next-edit suggestions are not billed in AI Credits</strong> and remain unlimited for paid Copilot plans under their existing counting method. That distinction does not turn model-selected chat and agent work into unlimited usage; it prevents confusing different product surfaces. Enterprise administrators can set AI-credit budgets to limit surprise spending.</p>
</section>
<section id="h55-compare">
<h2>Claude Haiku 5.5 vs Sonnet 5.5 vs Opus 5.5 in Copilot</h2>
<p>The three Claude tiers cover different kinds of engineering work. <strong>Haiku 5.5</strong> emphasizes cheap, low-latency scoped tasks. <strong>Sonnet 5.5</strong> offers greater capability for general multistep development, and <strong>Opus 5.5</strong> targets harder long-horizon agentic tasks. Anthropic's October 7 report explicitly says Sonnet and Opus remain the stronger choice for difficult agentic coding like Terminal-Bench. GitHub's <a href="https://docs.github.com/en/copilot/reference/ai-models/model-comparison" target="_blank" rel="noopener noreferrer">model guide</a> broadly aligns with that task split.</p>
<div class="h55-scroll"><table class="h55-table"><thead><tr><th>Decision</th><th>Haiku 5.5</th><th>Sonnet 5.5</th><th>Opus 5.5</th></tr></thead><tbody>
<tr><th>Best starting workload</th><td>Small edits, triage, subagent work</td><td>General coding and complex fixes</td><td>Demanding architecture and long-horizon agents</td></tr>
<tr><th>Listed uncached input / 1M</th><td>$0.10 ≤100K; $0.50 over</td><td>$2.00</td><td>$4.00</td></tr>
<tr><th>Listed output / 1M</th><td>$0.50 ≤100K; $2.50 over</td><td>$10.00</td><td>$20.00</td></tr>
<tr><th>Primary trade-off</th><td>Lower model spend; verify edge cases</td><td>Higher per-token rates; broader tasks</td><td>Highest of these listed costs; deeper tasks</td></tr>
<tr><th>SXF evaluation gate</th><td>Can it complete the bounded task correctly?</td><td>Does it reduce retries and reviewer work?</td><td>Does depth justify total compute and latency?</td></tr>
</tbody></table></div>
<p>These are <strong>listed Copilot unit prices</strong>, not a claim that Sonnet or Opus costs exactly 20× or 40× more to solve a task. Output length, context, cache writes, tool use and retries change end-to-end expense. For related SXF reporting, read <a href="/signals/claude-sonnet-5-5-in-github-copilot-c579283/">Claude Sonnet 5.5 in Copilot</a>, <a href="/signals/claude-opus-5-5-is-now-available-in-github-copilot-d6baa9e/">Claude Opus 5.5 in Copilot</a> and <a href="/models/claude-haiku-5-5/">Claude Haiku 5.5 model specs</a>.</p>
<h3>What did the published benchmarks really measure?</h3>
<p>Anthropic reports <strong>39.2%</strong> for Haiku 5.5 and <strong>70.6%</strong> for Sonnet 5.5 on its published <strong>Terminal-Bench 4.0</strong> evaluation. This is provider-published benchmark evidence on a specific task setup, not a Copilot customer outcome or a universal coding accuracy score. GitHub's separate launch claim compares Haiku 5.5 with <strong>Sonnet 5</strong> on many early tasks, <em>not</em> Sonnet 5.5 across every difficult repository test. Those statements are not contradictory; they evaluate different task sets and baselines. <a href="https://www.anthropic.com/claude-haiku-5-5" target="_blank" rel="noopener noreferrer">Anthropic's official benchmark discussion</a>.</p>
</section>
<section id="h55-claims">
<h2>What is verified, and what remains unknown about Haiku 5.5 in Copilot?</h2>
<div class="h55-scroll"><table class="h55-table"><thead><tr><th>Claim</th><th>Source-supported status</th><th>Evidence missing</th></tr></thead><tbody>
<tr><th>General availability</th><td>GitHub October 7 announcement; phased rollout</td><td>Exact account-by-account activation time</td></tr>
<tr><th>Pro/Pro+/Max/Business/Enterprise</th><td>Explicitly listed in launch post</td><td>Overrides from organization or enterprise policies</td></tr>
<tr><th>Faster for scoped work</th><td>GitHub and Anthropic describe early speed and efficiency</td><td>Controlled SXF test of typical Copilot tasks</td></tr>
<tr><th>Matches Sonnet 5 in some cases</th><td>GitHub reports early test results on many coding tasks</td><td>Test cases, statistical spread and generalization to every repo</td></tr>
<tr><th>Cheaper per token than Sonnet 5.5</th><td>Published prices support lower unit rates</td><td>End-to-end accepted-task cost with retries and human review</td></tr>
<tr><th>Suitable for every complex agent run</th><td>Not established; providers favor larger tiers for hard work</td><td>Independent long-horizon task success rates and reliability</td></tr>
</tbody></table></div>
<p>Anthropic says Haiku 5.5 averages roughly <strong>75% lower cost than Haiku 4.5</strong> across its usage assumptions and gives different unit-price reductions for prompts at or below 100K versus longer prompts. Those figures are provider claims about its pricing and workloads; they should <strong>not</strong> be turned into a promise that a Copilot team cuts its total invoice by 75%. For system-level safety and model evaluation details consult <a href="https://www.anthropic.com/transparency" target="_blank" rel="noopener noreferrer">Anthropic's transparency disclosures</a> and <a href="/guides/ai-model-benchmarks-explained/">SXF's model benchmark guide</a>.</p>
</section>
<section id="h55-sxf">
<h2>SXF original analysis: when should a coding team route work to Haiku 5.5?</h2>
<p><strong>Our interpretation:</strong> GitHub's Haiku integration is an architectural opportunity as much as a new entry in a model list. Teams can use a powerful model as an accountable planner and a cheaper model for small repeated subtasks. Yet every handoff creates another potential error: selecting the wrong file, misreading context, producing untested code or losing the goal. A routing system must verify outputs instead of assuming that a lower unit rate translates into lower engineering cost.</p>
<div class="h55-grid">
<article><span>GATE 01 / SCOPE</span><h3>Is the task bounded?</h3><p>Use clear files, inputs, output schemas and permissions. Ambiguous architecture work should escalate rather than silently expand the subagent's authority.</p></article>
<article><span>GATE 02 / CORRECTNESS</span><h3>Did tests really pass?</h3><p>Demand a reproducible test and a reviewed diff. Count fully accepted patches, not model-generated patches alone.</p></article>
<article><span>GATE 03 / LATENCY</span><h3>Was the full task quicker?</h3><p>Measure time to accepted change, including re-prompts, failed tool calls, switching models and reviewer effort.</p></article>
<article><span>GATE 04 / BILLING</span><h3>What was the total spend?</h3><p>Use Copilot credits across all calls. Long context and retries can erase much of the savings from cheap prompts.</p></article>
<article><span>GATE 05 / SAFETY</span><h3>Could the agent exceed its role?</h3><p>Check permissions, untrusted repository instructions, secret protection and human approval of high-impact edits.</p></article>
<article><span>GATE 06 / ESCALATION</span><h3>When must stronger models take over?</h3><p>Set triggers for uncertain requirements, repeated failed tests, security-sensitive code or broad cross-module changes.</p></article>
</div>
<h3>An SXF pilot study that can actually test the trade-off</h3>
<p>A practical starting experiment is <strong>30 task attempts</strong> distributed among documentation changes, focused bug fixes, unit-test improvements, data extraction and moderate cross-file work. Compare Haiku 5.5 and Sonnet 5.5 using fixed starting repository snapshots, the same permissions and prewritten acceptance tests. Log the failed attempts as well as successful ones. For high-risk tasks, include a senior reviewer who does not know which model produced the patch. This is a proposed SXF methodology, <strong>not an experiment conducted for this article</strong>.</p>
<p>Measure <strong>accepted-task rate, median and p95 time, credits consumed, human review minutes, failure severity and regression rate</strong>. The winning model is not the one that generates the most code. It is the one delivering the best risk-adjusted number of accepted results at a price the team can sustain.</p>
<h3>A useful escalation rule</h3><p>Begin with Haiku for a narrow change. Escalate to Sonnet when a unit test fails repeatedly for nontrivial reasons, the change spans several architectural layers, or the model cannot justify an assumption using code evidence. Try Opus for genuinely complex and high-risk work where the incremental reasoning value has already proved useful in your test set. The named thresholds should be defined by each team's data; SXF does not claim that these are GitHub's or Anthropic's internal routing rules.</p>
<p>GitHub's later <a href="/signals/route-and-orchestrate-models-with-github-copilot-fusion-194ab4b/">Copilot Fusion routing news</a> provides separate context on managed model orchestration. Do not assume enabling Haiku alone activates Fusion or that the two experiences select identical underlying models. For safe automated edits see <a href="/guides/ai-agent-security/">AI Agent Security</a> and <a href="/research/ai-agent-reliability/">AI Agent Reliability</a>.</p>
</section>
<section id="h55-security">
<h2>Privacy, model policies and security for business Copilot teams</h2>
<p>Choosing Haiku 5.5 should not be treated as permission to expose secrets or grant broad filesystem and network access. A capable model can still follow malicious instructions embedded in issue text or repository files, propose destructive commands or introduce incorrect dependencies. Restrict agent permissions and validate changes at the same standard as human-written code. <a href="https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-access-to-ai-models" target="_blank" rel="noopener noreferrer">GitHub's organization model controls</a> are one layer of governance, not a complete security evaluation.</p>
<p>Business teams should review provider-hosting and data-handling documentation, enterprise policies, agent sandboxing, repository permissions and logging. The GitHub release does not constitute an independent audit of every organization using the model, nor does Anthropic's system card prove the absence of coding errors. Before broad adoption, decide which datasets are allowed in prompts and which tool actions need explicit human approval.</p>
</section>
<section id="h55-faq">
<h2>Frequently asked questions about Claude Haiku 5.5 and Copilot</h2>
<h3>Is Claude Haiku 5.5 available in GitHub Copilot?</h3><p>Yes. It reached general availability on October 7, 2026 for named Copilot plans, with a gradual rollout across clients.</p>
<h3>Which plans can select Haiku 5.5?</h3><p>GitHub names Pro, Pro+, Max, Business and Enterprise. Free and Student plans rely on auto selection rather than equivalent direct model choice.</p>
<h3>Can I use it in VS Code, Copilot CLI and JetBrains?</h3><p>Yes, GitHub explicitly lists those clients, together with Visual Studio, Xcode, Eclipse, cloud agent, Copilot app, github.com and Mobile.</p>
<h3>Why is it not appearing in my model picker?</h3><p>Check the gradual rollout, plan, supported client and administrator policy. Use GitHub's current supported-model documentation.</p>
<h3>Is Haiku 5.5 cheaper than Sonnet 5.5?</h3><p>Its published per-token rates are lower for default prompts. Actual cost per accepted task depends on context size, output, caching, retries and human review.</p>
<h3>What does it cost in Copilot AI Credits?</h3><p>For inputs up to 100K tokens GitHub lists $0.10 per million input and $0.50 output, plus cache-specific rates. One AI Credit equals $0.01; subscription allowances and additional spend vary.</p>
<h3>Are requests longer than 100K tokens priced differently?</h3><p>Yes. GitHub lists a more expensive long-context tier above 100K input tokens; check the live pricing table before budgeting.</p>
<h3>Is Haiku 5.5 as capable as Sonnet 5.5 for agentic coding?</h3><p>Not across the board. Anthropic reports stronger Sonnet 5.5 performance on Terminal-Bench 4.0; Haiku targets faster, narrower tasks.</p>
<h3>Can administrators restrict this model?</h3><p>Yes. Organization and enterprise owners can enable or disable supported Copilot models according to delegated or enforced policies.</p>
<h3>What should a development team test first?</h3><p>Start with test-covered small edits and compare accepted output, review burden, latency and credits with a stronger-model baseline.</p>
</section>
<section id="h55-sources">
<h2>Official sources and editorial methodology</h2>
<p><strong>Verification date: November 8, 2026.</strong> Copilot plan eligibility, deployment surfaces, policy controls and pricing come from GitHub; model capabilities and benchmark values come from Anthropic. SXF's six-gate evaluation and example requests are original editorial recommendations, <strong>not</strong> results of our own Haiku-versus-Sonnet benchmark or verification of GitHub's internal tests. Because subscriptions, AI Credits and prices can change, consult the linked live references when buying.</p>
<ol class="h55-sources">
<li><a href="https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/" target="_blank" rel="noopener noreferrer">GitHub Changelog, October 7 — Claude Haiku 5.5 in GitHub Copilot</a>. Release status, supported plans and clients, provider pricing and rollout.</li>
<li><a href="https://github.blog/changelog/2026-10-09-github-copilot-weekly-releases-october-5/" target="_blank" rel="noopener noreferrer">GitHub October 5 weekly releases, published October 9</a>. Independent dated GitHub follow-up that reconfirms model availability.</li>
<li><a href="https://docs.github.com/en/copilot/reference/ai-models/supported-models" target="_blank" rel="noopener noreferrer">GitHub Docs — Supported AI models</a>. Current plan and client eligibility.</li>
<li><a href="https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing" target="_blank" rel="noopener noreferrer">GitHub Docs — Models and pricing</a>. AI Credits, 100K-token threshold and per-token rates.</li>
<li><a href="https://docs.github.com/en/copilot/reference/ai-models/model-comparison" target="_blank" rel="noopener noreferrer">GitHub Docs — AI model comparison</a>. Task-based guidance across Haiku, Sonnet and larger models.</li>
<li><a href="https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-access-to-ai-models" target="_blank" rel="noopener noreferrer">GitHub Docs — Configuring model access</a>. User, organization and enterprise policy effects.</li>
<li><a href="https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-default-models" target="_blank" rel="noopener noreferrer">GitHub Docs — Managing model availability</a>. Organization controls and default policy.</li>
<li><a href="https://docs.github.com/en/copilot/how-tos/github-copilot-app/choose-a-model" target="_blank" rel="noopener noreferrer">GitHub Docs — Choosing a model in Copilot app</a>. How current model selection works.</li>
<li><a href="https://www.anthropic.com/claude-haiku-5-5" target="_blank" rel="noopener noreferrer">Anthropic, October 7 — Introducing Claude Haiku 5.5</a>. Provider claims, benchmarks, pricing and safety discussion.</li>
<li><a href="https://www.anthropic.com/claude/haiku" target="_blank" rel="noopener noreferrer">Anthropic — Claude Haiku model overview</a>. Current positioning, API details and usage categories.</li>
<li><a href="https://www.anthropic.com/transparency" target="_blank" rel="noopener noreferrer">Anthropic Transparency Hub</a>. Model summary and safety evaluation context.</li>
</ol>
<p><strong>Explore on SXF:</strong> <a href="/models/claude-haiku-5-5/">Haiku 5.5 specs</a> · <a href="/models/claude-sonnet-5-5/">Sonnet 5.5 specs</a> · <a href="/signals/claude-sonnet-5-5-in-github-copilot-c579283/">Sonnet 5.5 in Copilot</a> · <a href="/signals/github-copilot-weekly-releases-october-5-8e5ec29/">October Copilot updates</a> · <a href="/topics/github-copilot/">GitHub Copilot topic</a> · <a href="/guides/ai-agent-security/">Agent security</a>.</p>
</section></section>'''
CSS = r'''<style id="haiku55-copilot-sxf-editorial-css">
.haiku55-copilot-page .haiku55-report{margin:34px auto 58px}.haiku55-report section{margin:43px 0;max-width:1035px;scroll-margin-top:92px}.haiku55-report p,.haiku55-report li{line-height:1.82}.haiku55-report a{text-decoration:underline;text-underline-offset:3px}.haiku55-report section>h2{font-size:clamp(1.5rem,2.35vw,2.07rem);line-height:1.29;margin:0 0 17px}.haiku55-report h3{font-size:1.12rem;line-height:1.43;margin:24px 0 10px}.h55-lead{font-size:1.09rem;max-width:945px;line-height:1.85!important;color:#cbd9e8}.h55-facts,.h55-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:25px 0}.h55-facts>div,.h55-grid>article{padding:19px;border:1px solid rgba(140,191,223,.27);border-radius:16px;background:linear-gradient(140deg,rgba(72,124,166,.16),rgba(6,13,24,.48))}.h55-facts span,.h55-grid span{display:block;color:#a2e9da;font-size:.75rem;font-weight:800;letter-spacing:.08em}.h55-facts strong{display:block;margin:8px 0 5px;color:#f2f7ff;font-size:1.06rem}.h55-facts small{color:#b6c7d7;line-height:1.55}.h55-grid h3{margin:9px 0 8px}.h55-grid p{margin:0}.h55-toc{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0;padding:18px 20px;border:1px solid rgba(137,196,219,.27);border-radius:16px;background:rgba(32,64,89,.15)}.h55-toc strong{width:100%;margin-bottom:4px}.h55-toc a{border:1px solid rgba(135,202,206,.27);border-radius:28px;padding:7px 12px;text-decoration:none}.h55-scroll{overflow-x:auto;border:1px solid rgba(137,191,221,.26);border-radius:14px;margin:23px 0}.h55-table{width:100%;min-width:735px;border-collapse:collapse;font-size:.91rem}.h55-table th,.h55-table td{border-bottom:1px solid rgba(140,182,217,.18);padding:14px 16px;text-align:left;vertical-align:top;line-height:1.6}.h55-table thead th{background:#172d43;color:#e3f3ff}.h55-table tbody th{color:#a7ebdf}.h55-steps,.h55-sources{padding-left:1.55rem}.h55-steps li,.h55-sources li{margin:12px 0}.h55-example{background:#102438;border:1px solid rgba(138,190,217,.29);border-radius:15px;margin:20px 0;padding:19px 23px}.h55-example p{margin:0}.haiku55-copilot-page a:focus-visible{outline:2px solid #98eedb;outline-offset:4px}@media(max-width:760px){.h55-facts,.h55-grid{grid-template-columns:1fr}.h55-table{min-width:570px}.haiku55-report section{margin:34px 0}}
</style>'''

def enrich(page: str) -> str:
    marker = 'data-sxf-haiku55-copilot="2026-11-08"'
    if marker in page:
        return page
    expected = ['class="intel-page signal-page"',
        '<h1>Claude Haiku 5.5 in GitHub Copilot</h1>',
        '<section class="signal-layout shell">',
        '<section class="signal-taxonomy shell">',
        '<meta name="twitter:card" content="summary" />']
    if any(s not in page for s in expected):
        raise ValueError("Claude Haiku 5.5 Copilot source template changed")
    page = page.replace('class="intel-page signal-page"',
        'class="intel-page signal-page haiku55-copilot-page"', 1)
    page, n = re.subn(r'<title>.*?</title>', '<title>'+escape(TITLE)+'</title>',
                       page, count=1, flags=re.S)
    if n != 1:
        raise ValueError("No title")
    for key, value in [('description', DESCRIPTION), ('og:title', TITLE),
                       ('og:description', DESCRIPTION), ('twitter:title', TITLE),
                       ('twitter:description', DESCRIPTION)]:
        pattern = r'(<meta (?:property|name)="' + re.escape(key) + r'" content=")[^"]*(" />)'
        page, n = re.subn(pattern,
            lambda m:m.group(1)+escape(value, quote=True)+m.group(2),
            page, count=1)
        if n != 1:
            raise ValueError("Missing SEO tag "+key)
    page = page.replace('<meta name="twitter:card" content="summary" />',
        '<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />'
        '<meta property="og:image:alt" content="SXF analysis of Claude Haiku 5.5 availability and pricing in GitHub Copilot" />'
        '<meta name="twitter:card" content="summary_large_image" />'
        '<meta name="twitter:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />',1)
    css_link = '<link rel="stylesheet" href="/intelligence.css" />'
    if css_link not in page:
        raise ValueError("Missing shared stylesheet")
    page = page.replace(css_link, css_link+'\n'+CSS, 1)
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("Missing article schema")
    ld = json.loads(match.group(1))
    graph = ld['@graph']
    if len(graph) != 3:
        raise ValueError("Unexpected article schema")
    graph[0].update(name=TITLE,description=DESCRIPTION,
        breadcrumb={'@id':CANONICAL+'#breadcrumb'})
    graph[1].update(headline=H1,description=DESCRIPTION,
        dateModified='2026-11-08',keywords=KEYWORDS,citation=SOURCES,
        isBasedOn=SOURCES[0],about=[
          {'@type':'SoftwareApplication','name':'GitHub Copilot'},
          {'@type':'SoftwareApplication','name':'Claude Haiku 5.5'},
          {'@type':'Organization','name':'Anthropic'},
          {'@type':'Thing','name':'AI coding agents'}])
    graph[2]['itemListElement'].append({'@type':'ListItem','position':4,
        'name':'Claude Haiku 5.5 in GitHub Copilot: pricing and analysis',
        'item':CANONICAL})
    graph.append({'@type':'FAQPage','@id':CANONICAL+'#faq',
        'mainEntity':[{'@type':'Question','name':q,
             'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]})
    page = page[:match.start()]+'<script type="application/ld+json">'+(
        json.dumps(ld,ensure_ascii=False,separators=(',',':')))+(
        '</script>')+page[match.end():]
    page = page.replace('<h1>Claude Haiku 5.5 in GitHub Copilot</h1>',
        '<h1>'+escape(H1)+'</h1>',1)
    page, n = re.subn(r'<section class="signal-layout shell">.*?</section>',
                       lambda _:BRIEF,page,count=1,flags=re.S)
    if n != 1:
        raise ValueError("Missing source summary")
    page = page.replace('<section class="signal-taxonomy shell">',
        BODY+'\n<section class="signal-taxonomy shell">',1)
    if page.count(marker) != 1:
        raise ValueError("Editorial marker lost or duplicate")
    for src in SOURCES:
        if src not in page:
            raise ValueError("Unlinked official source "+src)
    return page
