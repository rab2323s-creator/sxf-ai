# AI Agent Comparison: ChatGPT Work vs. Claude Cowork vs. Manus

**Prepared for:** SXF AI Agent Lab
**Research date:** November 3, 2026
**Method:** Web research only (search + page fetches). **No hands-on testing or benchmarking was performed.** Every "who is better" statement below is an inference from documented capabilities, not a measured result.

---

## 1. Executive summary

| Scenario | Best fit (on documented evidence) | Confidence |
|---|---|---|
| Researching information online | **Manus** (documented parallel "Wide Research"), with **ChatGPT Work** a close second | Low–medium (no tests; all three vendors warn about errors) |
| Analyzing business documents | **ChatGPT Work** if documents live in M365/Google/Slack/CRM; **Claude Cowork** if they are local files or folders | Medium |
| Executing multi-step workflows | **ChatGPT Work** for governed, cross-app work; **Manus 2.0** for individuals wanting event-triggered automation | Medium |

Three things to know before reading further:

1. **All three products changed substantially in the last 90 days** (ChatGPT Work launched July 9; Claude chat and Cowork are merging; Manus 2.0 shipped Sept 28 and Manus separated from Meta). Older articles are often wrong. See Section 6.
2. **Pricing models differ in kind.** ChatGPT Work and Claude Cowork are bundled into general subscriptions with usage limits. Manus sells credits, and its own help center says it cannot yet predict a task's credit cost.
3. **Manus has the weakest official-source coverage** in this report: the live pricing page could not be read, so its $200 tier rests on third-party sources.

---

## 2. Product profiles

Status tags: **[V]** verified on an official page I read in full; **[S]** official page seen only as a search snippet; **[3P]** third-party reporting; **[M]** vendor marketing claim; **[U]** unverified.

### 2.1 ChatGPT Work (OpenAI)

**What it is.** An agent mode inside ChatGPT, designed for longer multi-step tasks that end in a finished deliverable, with Chat as the separate mode for quick answers. [V] ([launch post](https://openai.com/index/chatgpt-for-your-most-ambitious-work/), [Get started docs](https://learn.chatgpt.com/docs/get-started-with-work)). It launched July 9, 2026 with Codex technology built in. [V]

**Core capabilities**
- Pulls context from connected apps via plugins (Slack, Microsoft Teams, Google Drive, SharePoint, email, calendars, CRMs, trackers) and produces sheets, slides, docs and web apps. [V] ([launch post](https://openai.com/index/chatgpt-for-your-most-ambitious-work/))
- Scheduled Tasks: run once, repeat on a schedule, trigger on an event, or monitor for changes. [V] (same page)
- Desktop app: built-in browser, use of local files and apps, and "Computer Use" to click and type on the user's behalf. [V] (same page)
- Sites (public beta): turns work into a shareable interactive page or web app. [V] (same page; [pricing page](https://learn.chatgpt.com/docs/pricing.md) confirms Sites is included with eligible plans during beta)
- A Data agent for company-data questions and dashboards was announced September 10, 2026. [S] ([OpenAI post](https://openai.com/index/put-data-to-work/))
- Admin controls: Enterprise/Edu admins manage plugin access, network/browser access and sensitive actions; a Compliance API gives visibility into Work activity; "auto-review" checks important connected-tool actions. [V] that these features are offered; how well they work is [M].

**Availability (current).** The product page says Work is available on all plans on macOS and Windows desktop, and on Plus, Pro, Business, Enterprise and Edu on web and mobile. [V] ([product page](https://openai.com/chatgpt-work/)). The Help Center adds that desktop availability depends on the plan and workspace. [S] ([Help Center](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex); the page itself blocked automated fetching.)

**Subscription requirements and cost.** There is no separate Work subscription. Work shares usage, credits and limits with Codex. [V] ([pricing page](https://learn.chatgpt.com/docs/pricing.md))

| Plan | Price listed by OpenAI [V] |
|---|---|
| Free | $0 |
| Go | $8/month |
| Plus | $20/month |
| Pro | from $100/month (plans at $100, $200 or $500) |
| Business | $20/user/month billed annually; $25 billed monthly (2+ users) |
| Enterprise / Edu | contact sales |

**Limits and limitations**
- Usage is metered, and long tasks consume more. Plus has a rolling five-hour window; the page gives *estimates* of local messages per window that vary widely by model (for example 5–45 for GPT-6 Astra versus 350–3,000 for GPT-6 Luna). Pro currently has no five-hour limit; weekly limits may apply to all plans. [V] ([pricing page](https://learn.chatgpt.com/docs/pricing.md))
- Computer Use and some browser-control features are marked "limited" in the plan matrix, with region restrictions noted. [V] (same page)
- Sites is in beta. [V]
- Enterprise/Edu plans without flexible pricing get Plus-level per-seat limits for most features. [V]
- A TechCrunch report (Nov 2, 2026) says OpenAI is preparing to merge the Chat and Work tabs and to pool ChatGPT and Codex usage. [3P] ([TechCrunch](https://techcrunch.com/2026/11/02/openai-is-finally-merging-chatgpts-chat-and-work-tabs/)). I found no official OpenAI page confirming this.

**Marketing claims I could not verify:** that nearly all OpenAI teams use Work, the Zapier and finance case-study outcomes, and the "state of the art" claim for GPT-5.6. [M]

---

### 2.2 Claude Cowork (Anthropic)

**What it is.** An agent that applies Claude Code's agentic architecture to non-coding knowledge work, so a user can describe an outcome and return to finished work. [V] ([Get started with Claude Cowork](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork))

**Core capabilities** (all [V] from the same page unless noted)
- Sessions run in the cloud on Anthropic's servers, keep running if the laptop closes, and can be followed across desktop, web and mobile. Local files, the built-in browser and computer use are reached through the Claude Desktop app, which must stay open for those steps.
- Sub-agent coordination for parallel work; long-running tasks.
- Outputs: Excel files with working formulas, PowerPoint decks and formatted documents.
- Scheduled tasks that run in the cloud with no device online.
- Projects (persistent workspaces with files, instructions and memory), plugins, connectors, and memory shared with chat.
- Browser use via a built-in browser or the Claude in Chrome extension.
- Three approval modes: Manual, Auto (Claude reviews each action and blocks unsafe ones), and Skip (no checks).

**Availability.** Paid plans only. Desktop (macOS, Windows, Linux in beta) on all paid plans; web and mobile on Pro, Max, Ultra and Team (beta on Team), and on Enterprise when an owner enables it. [V] ([Get started](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork), [Team and Enterprise article](https://support.claude.com/en/articles/13455879-use-claude-cowork-on-team-and-enterprise-plans)). A new unified chat-plus-Cowork experience is rolling out to individual plans; Team and Enterprise get it where an admin enables "Chat and Cowork unified." [V]

**Subscription requirements and cost.** No separate Cowork fee is listed anywhere I found; it is included with paid plans. (That "no separate fee" statement is my inference from the pricing and support pages, not an explicit sentence.) Plan prices from [claude.com/pricing](https://claude.com/pricing) [V]:

| Plan | Price |
|---|---|
| Free | $0 (Cowork not offered) |
| Pro | $20/month, or $17/month billed annually |
| Max | $100/month (5x Pro usage) |
| Ultra | $200/month (10x Pro weekly usage; no 5-hour limit for verified accounts) |
| Team | Standard $20/seat annual or $25 monthly; Premium $100 annual or $125 monthly (5x Standard usage); teams of 2–150 |
| Enterprise | $20/seat/month billed annually (20-seat minimum) **plus usage billed at API rates** |

**Limits and limitations**
- Multi-step tasks consume more usage than quick chats. [V]
- Sessions cannot be shared (individual artifacts can). Some features, including plugins with local MCP servers, work only on desktop. [V]
- Prompt-injection risk is described by Anthropic as non-zero. [V] ([Team and Enterprise article](https://support.claude.com/en/articles/13455879-use-claude-cowork-on-team-and-enterprise-plans))
- Network-egress settings do not apply to web fetch, web search or MCPs, including Claude in Chrome. [V]
- On Enterprise, Cowork in the cloud is off by default, and it is unavailable under the HIPAA configuration, which covers only local-mode sessions. [V]
- Local-session conversation history is stored on the user's computer, outside Anthropic's standard retention controls, and admins cannot centrally delete it. [V]
- The Get started page lists Linux as a beta desktop platform but its requirements section names only macOS or Windows for local file, browser and computer use. [V] (internal inconsistency; see Section 6)

**Marketing claims I could not verify:** quality of the generated spreadsheets and decks; the safety effectiveness of Auto mode ("no defense is perfect," per Anthropic itself). [M]

---

### 2.3 Manus (Butterfly Effect / Manus AI)

**What it is.** A general-purpose autonomous agent. On September 28, 2026 the company released **Manus 2.0**: a new in-house agent harness ("Cascade"), a purchasable Cloud Computer, event-triggered Automations, a desktop workspace called Manus Studio (documents, spreadsheets, slides, websites, code, video, games), Computer Use with remote control from a phone, and a separate app, **Cue**, for personal agents. [V] ([Introducing Manus 2.0](https://manus.im/blog/introducing-manus-2-0))

**Core capabilities**
- **Wide Research:** paid-only, triggers automatically for tasks that split into parallel parts, runs up to 20 sub-tasks at once, and caps each sub-task at 50 credits. [V] ([Help Center](https://help.manus.im/en/articles/11960169-what-is-wide-research))
- Automations can start from a new email, calendar event, Slack message, Notion update or change in ad performance, in addition to schedules. [V] ([blog](https://manus.im/blog/introducing-manus-2-0))
- Computer Use works in a visible workspace on the user's computer with approved files, browser and apps. [V] (same blog)
- Pro plans include advanced research, website deployment, slide generation, 20 concurrent tasks and 20 scheduled automations. [V] ([Help Center pricing article](https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus))

**Availability.** Web, desktop and mobile. Cue is invite-code early access and not part of the core Manus subscription. [V] (blog)

**Subscription requirements and cost** (credit-based). [V] ([Help Center](https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus); [plans docs](https://manus.im/docs/introduction/plans.md))

| Plan | Price | Credits / limits |
|---|---|---|
| Free | $0 | 300 daily refresh credits, 1 concurrent task, 2 scheduled automations |
| Pro | from $20/month | from 4,000 credits/month |
| Pro (higher) | from $40/month, 7-day trial | from 8,000 credits/month |
| Team | from $20/seat/month | shared credit pool; adds SSO, training opt-out, usage analytics, access control, shared slide templates |
| Annual billing | 17% discount | |

Not verified from an official page I could read: a **$200/month, 40,000-credit** tier. Several third-party price guides report it, and the Help Center article shows its price tables only as images. [3P/U]
Also [3P/U]: that the Free plan is limited to the "Manus 1.6 Lite" model with a 1,500 credit/month cap. Third parties attribute this to the Help Center, but the article I read does not say it.

**Limits and limitations**
- **Cost unpredictability.** A Help Center article (dated Dec 18, 2025) says Manus cannot yet estimate a task's credit use in advance and that any credit promises the agent makes should be treated as hallucinations. [V] ([Help Center](https://help.manus.im/en/articles/13185575-is-there-a-way-to-check-how-many-credits-a-task-will-cost-before-i-begin)). The plans documentation, by contrast, says the dashboard provides estimates before a task starts. [V] ([plans docs](https://manus.im/docs/introduction/plans.md)). This is an unresolved conflict between two official pages.
- **Accuracy warning.** The same Help Center article lists fabricated content, including invented academic papers and citations, among known AI behaviors. [V]
- Plan credits reset monthly; only purchased add-on credits never expire. [V] (plans docs)
- Wide Research is not available on the Free plan. [V]
- Cloud Computer is a separate purchase. Its price was not found. [V] that it is separate; price [U]
- **Corporate situation.** Meta announced a roughly $2B acquisition in December 2025; China's planning agency ordered it unwound on April 27, 2026; Manus resumed independent operations in September 2026 and raised more than $500M in October. [3P] ([CNBC, Apr 27](https://www.cnbc.com/2026/04/27/meta-manus-china-blocks-acquisition-ai-startup.html), [CNBC, Oct 8](https://www.cnbc.com/2026/10/08/manus-fund-raise-meta-muse-tencent.html); both read as search snippets only). This is a due-diligence factor for enterprises; I found no official Manus page describing its current ownership or data-handling commitments after the split.
- Team and Enterprise data claims (SOC 2, no training by model providers) appear in third-party summaries; I did not read Manus's [trust center](https://trust.manus.im/). [U]

**Marketing claims I could not verify:** Cascade's efficiency gains (23.2% fewer tokens, 28.2% faster, 32% cheaper) are from one tested configuration chosen by Manus. [M]

---

## 3. Side-by-side comparison

| Dimension | ChatGPT Work | Claude Cowork | Manus |
|---|---|---|---|
| Vendor status | OpenAI | Anthropic | Butterfly Effect; independent again after Meta deal unwound [3P] |
| Launched / GA | July 9, 2026 [V] | Desktop GA on macOS/Windows per Anthropic release notes [S]; the Apr 9, 2026 date and Jan 2026 preview dates come from third-party reporting [3P]; web/mobile beta applies to Team [V] | Manus 2.0 on Sept 28, 2026 [V] |
| Entry paid price | Plus $20/mo [V] | Pro $20/mo ($17 annual) [V] | Pro from $20/mo [V] |
| Free access | Desktop app only; no web/mobile Work on Free [V] | No (paid only) [V] | Yes, limited (daily credits) [V] |
| Pricing model | Subscription with usage limits and optional credits; shared with Codex [V] | Subscription with usage limits and optional usage credits; Enterprise adds API-rate usage [V] | Credits per task; plan credits reset monthly [V] |
| Pre-task cost estimate | Not documented; usage estimates per model [V] | Not documented [U] | Conflicting official statements [V] |
| Web research | Built-in browser (desktop) and web search [V] | Web search, built-in browser, Claude in Chrome [V] | Advanced research; Wide Research (paid) [V] |
| File / document work | Creates sheets, slides, docs; local files on desktop; Drive/SharePoint plugins [V] | Excel with formulas, decks, docs; direct local file access on desktop; projects [V] | Docs, sheets, PDFs, slides, sites, code, video, games in Studio [V] |
| Workflow automation | Scheduled Tasks incl. event triggers; plugins; Computer Use [V] | Cloud scheduled tasks; plugins; connectors; sub-agents [V] | Event-triggered Automations; 20 concurrent tasks (Pro); Cloud Computer (extra) [V] |
| Runs when your computer is off | Yes for cloud Work and scheduled tasks; steps needing local files need the computer [V] | Yes in the cloud; local-file steps need Desktop app open [V] | Cloud Computer available for always-on projects (purchase) [V] |
| Admin / compliance | Compliance API, admin controls, EKM requirement noted for some Enterprise workspaces [V] | Compliance API, OpenTelemetry, role-based controls, HIPAA local-mode config [V] | Team plan: SSO, opt-out of training, analytics, access control [V]; enterprise assurances [U] |
| Third-party app connections | Plugins directory [V] | Connectors, plugins, MCP [V] | Slack, Notion, email, calendar triggers [V] |
| Key limitations | Metered usage; Computer Use limited/region-restricted; Sites in beta [V] | No session sharing; some desktop-only features; prompt-injection risk; paid plans only [V] | Cost unpredictability; documented hallucination risk; ownership turbulence [V]/[3P] |
| Independent test results | None collected | None collected | None collected |

---

## 4. Recommendations

I did not run comparative tasks, so these are conditional recommendations grounded in documented design and constraints.

### 4.1 Researching information online → **Manus** (conditional), then **ChatGPT Work**

- **Why Manus:** Wide Research is the only feature among the three that is documented specifically for splitting a research job into up to 20 parallel sub-tasks. Pro-level pricing starts at $20/month.
- **Why not unconditionally:** Manus's own Help Center warns the agent may invent sources, and credit cost cannot be predicted ahead of time. A breadth job can drain credits unexpectedly.
- **ChatGPT Work** is a strong alternative when research must end in a polished artifact, and its desktop built-in browser is documented for comparing sources and pulling from websites.
- **Claude Cowork** is a sensible choice when you already use Claude and want research combined with local files, but it has no documented parallel-research feature of Manus's kind.
- **For all three:** verify every citation before use.

### 4.2 Analyzing business documents → **ChatGPT Work** or **Claude Cowork**, depending on where the documents live

- **Choose ChatGPT Work** if the material sits in Microsoft 365, Google Drive, Slack or a CRM (documented plugins), or you need company-data analysis. The Data agent is relevant here, though I only saw it as a snippet. Governance features (Compliance API, admin controls) are documented for Enterprise and Edu.
- **Choose Claude Cowork** if the material is local files or folders (documented direct local file access), you want persistent project workspaces, or you need Excel output with working formulas. Enterprise controls (role-based access, OpenTelemetry, Compliance API) are documented.
- **Manus is the weakest choice for sensitive documents on current evidence.** Its Team plan offers a data-training opt-out, which implies (my inference) that lower tiers may not, and I could not verify post-Meta data-handling commitments.

### 4.3 Executing multi-step workflows → **ChatGPT Work** (organizations), **Manus 2.0** (individuals/small teams)

- **ChatGPT Work:** combines scheduled and event-triggered tasks, cross-app plugins, Computer Use, and admin approval controls in one governed product.
- **Manus 2.0:** event-triggered Automations (email, Slack, Notion, calendar) with 20 concurrent tasks on Pro are documented, and the entry price is low. Trade-offs are cost unpredictability and Cloud Computer being an extra purchase at an unknown price.
- **Claude Cowork** is close behind: cloud-run scheduled tasks, sub-agents, plugins, and an explicit permission model. Its documented triggers are scheduled and on-demand; I found no documented event-triggered automation for Cowork.

---

## 5. Verified facts vs. assumptions vs. unavailable information

**Verified (official page read in full):** plan prices for all three (except Manus's $200 tier); availability statements; core capability lists; Cowork and Manus limitations quoted above; ChatGPT Work usage mechanics.

**Reported but not officially confirmed:** the planned ChatGPT Chat/Work merge (TechCrunch); Manus–Meta acquisition, unwind and funding (CNBC, snippets only); Cowork's GA dates beyond Anthropic's release-notes snippet.

**Marketing claims, not independently verified:** all customer outcomes, efficiency percentages, "state of the art" statements, and productivity claims.

**Assumptions I made (flagged):** Cowork has no separate fee; Manus lower tiers may lack a training opt-out; recommendations in Section 4.

**Unavailable or unverified:** Manus $200/40,000-credit tier from an official page; Manus Free-plan model and 1,500-credit cap from an official page; Manus Cloud Computer price; Manus trust-center claims; Cowork pre-task cost estimates; any head-to-head performance data.

---

## 6. Conflicting or outdated information found

| # | Topic | Conflict | Resolution |
|---|---|---|---|
| 1 | ChatGPT Work model | Launch post (Jul 9) says GPT-5.6; current product page says GPT-6; current docs list GPT-6 Astra, GPT-6.1 Sol/Terra and GPT-6 Luna. | Launch post is historical; the newer pages reflect current models. OpenAI's pricing page also notes GPT-5.5 retires Oct 14, 2026. |
| 2 | ChatGPT Work on Free | Launch post and Fox Business say Chat/Work/Codex are on every plan including Free (desktop). Current product page confines Free to the desktop app and lists Plus and above for web/mobile. | Free = desktop only. Fox Business wording is easy to misread as all surfaces. |
| 3 | ChatGPT Work rollout order | Launch post: Pro/Enterprise/Edu first, Plus/Business "over the next few days." | Rollout sequencing, resolved by the current product page. |
| 4 | ChatGPT Pro tiers | Third-party blog says the $200 tier stopped taking new sign-ups on Sept 10. OpenAI's pricing page lists $100, $200 and $500 Pro plans with no such note. | Unverified; treat as possibly true but not confirmed. |
| 5 | Claude plan names/prices | Third-party sites still list "Max 20x at $200"; official pricing now calls the $200 tier **Ultra** and Max is $100. Older snippets show Team at $25/$30 and "teams of 5 to 75"; current page shows $20/$25 and 2–150 seats. | Official page wins; many third-party pricing guides are outdated. |
| 6 | Cowork plan list | The Get started article names Ultra; the Team and Enterprise article, as I fetched it, lists Pro, Max, Team, Enterprise without Ultra (a search snippet of the same article included Ultra). | Likely documentation lag between pages; Ultra is on the pricing page. |
| 7 | Cowork "GA" | Third-party reports call it GA on all paid plans; one outlet says Anthropic's pages still describe web/mobile as beta. | Official pages: desktop GA per release notes, web/mobile beta applies to Team; Linux desktop beta. |
| 8 | Cowork platforms | Get started lists Linux (beta); its requirements section names only macOS or Windows. | Internal inconsistency; confirm before deploying on Linux. |
| 9 | Manus plan names | Older sources use Standard/Customizable/Extended or $39/$199 tiers; the Help Center now uses Free/Pro/Team and says Basic/Plus were renamed Pro. | Use Help Center naming; older figures are obsolete. |
| 10 | Manus credit estimates | Plans docs say the dashboard gives pre-task estimates; Help Center (Dec 2025) says it cannot. | Unresolved; the Help Center page is older, so the docs may reflect a newer feature, but I could not confirm. |
| 11 | Manus ownership | Early-2026 articles describe Manus as Meta-owned; later sources say the deal was unwound. | Latest reporting says independent; official confirmation not found. |

---

## 7. Limitations of this research

- **No hands-on testing.** Nothing here measures accuracy, speed or output quality.
- **Verification method.** My sandbox had no outbound network, so I could not run HTTP status checks. "Verified" means the page was returned by the fetch tool or a search result and its content supports the claim. Each URL's status is in Section 8.
- **Blocked or unread pages:** OpenAI Help Center (bot detection), manus.im/pricing, trust.manus.im, claude.com/product/cowork, chatgpt.com/pricing, Claude release notes and OpenAI's Data agent post (snippets only).
- **Prices change, vary by region, and exclude tax.** Re-check before purchase.
- **The three products are not like-for-like.** ChatGPT Work and Cowork are modes inside larger assistant subscriptions; Manus is a standalone credit-priced agent platform. Price comparisons are indicative only.
- **Evidence ledger:** see `evidence.csv` for the per-claim record.

---

## 8. URL verification log

Status key: **Read** = page content fetched and relevant claims confirmed. **Snippet** = relevant text seen in a search result only. **Blocked** = fetch refused.

| URL | Status | Used for |
|---|---|---|
| https://openai.com/index/chatgpt-for-your-most-ambitious-work/ | Read | ChatGPT Work launch, capabilities, rollout |
| https://openai.com/chatgpt-work/ | Read | Current availability, GPT-6 |
| https://learn.chatgpt.com/docs/get-started-with-work | Read | What Work is, models, best uses |
| https://learn.chatgpt.com/docs/pricing.md | Read | Plans, prices, usage limits, feature matrix |
| https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex | Snippet (fetch blocked) | Availability wording |
| https://openai.com/index/put-data-to-work/ | Snippet | Data agent |
| https://techcrunch.com/2026/11/02/openai-is-finally-merging-chatgpts-chat-and-work-tabs/ | Snippet | Planned Chat/Work merge |
| https://www.foxbusiness.com/technology/openai-unveils-chatgpt-work-automate-workplace-tasks-ai-race-intensifies | Snippet | "Every plan incl. Free" wording |
| https://www.developersdigest.tech/blog/codex-usage-limits-pricing-2026 | Snippet | Unverified Pro $200 pause claim |
| https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork | Read | Cowork capabilities, availability, limitations |
| https://support.claude.com/en/articles/13455879-use-claude-cowork-on-team-and-enterprise-plans | Read | Team/Enterprise controls, security |
| https://claude.com/pricing | Read | Plan prices and usage |
| https://support.claude.com/en/articles/13364135-use-claude-cowork-safely | Snippet | Availability, safety |
| https://support.claude.com/en/articles/14479288-claude-cowork-architecture-overview | Snippet | Where Cowork runs |
| https://support.claude.com/en/articles/12138966-release-notes | Snippet | GA timeline |
| https://www.unite.ai/anthropic-folds-cowork-into-a-single-claude-experience-across-plans/ | Snippet | Third-party timeline |
| https://runtimewire.com/article/anthropic-claude-cowork-all-paid-plans-web-mobile | Snippet | GA vs beta discrepancy |
| https://www.anthropic.com/pricing?q=umwelt | Snippet | Outdated Team price evidence |
| https://help.manus.im/en/articles/11711111-what-is-the-current-membership-pricing-for-manus | Read | Manus plans and prices |
| https://manus.im/docs/introduction/plans.md | Read | Credit mechanics |
| https://manus.im/blog/introducing-manus-2-0 | Read | Manus 2.0 features and availability |
| https://help.manus.im/en/articles/11960169-what-is-wide-research | Read | Wide Research |
| https://help.manus.im/en/articles/13185575-is-there-a-way-to-check-how-many-credits-a-task-will-cost-before-i-begin | Read | Credit estimates, hallucination warning |
| https://www.cnbc.com/2026/04/27/meta-manus-china-blocks-acquisition-ai-startup.html | Snippet | Acquisition blocked |
| https://www.cnbc.com/2026/10/08/manus-fund-raise-meta-muse-tencent.html | Snippet | Post-Meta funding |
| https://www.usecarly.com/blog/manus-pricing/ | Snippet | $200 tier (third party) |
| https://emergent.sh/learn/manus-ai-pricing | Snippet | $200 tier, Free-plan model (third party) |
| https://pasqualepillitteri.it/en/news/12697/openai-5-hour-codex-chatgpt-work-limit-plus | Snippet | Plus 5-hour limit reinstated (third party) |
| https://pulse2.com/manus-raises-more-than-500-million-after-unwinding-meta-acquisition/ | Snippet | Manus data-deletion claim (unverified) |
| https://aitoolsatlas.ai/tools/manus-ai | Snippet | Manus Team SOC 2 / training claims (unverified) |
| https://spectrumailab.com/blog/manus-ai-pricing-plans-cost-guide-2026 | Snippet | Free-plan model/cap attributed to Help Center |

---

*End of report.*