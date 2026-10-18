# We Tested an AI Agent: From Goal to Completed Task
**SXF / AI — source-backed field test · October 18, 2026**

## Task given to the agent

"Using current, first-party documentation only, compare OpenAI Agents SDK, Google ADK and LangGraph. Produce an actionable, cited brief that explains what each framework emphasizes, when a developer might select it, and where the evidence stops. Verify the source pages before finalizing. Save a machine-readable record of research steps."

## Actual setup

- **Agent:** GPT-6 in a tool-enabled ChatGPT research session.
- **Execution model:** One agent that chose web searches, inspected documentation, synthesized findings and invoked a GitHub integration for output. No multi-agent delegation and no locally installed copies of the compared frameworks.
- **Tools:** Web search, web document retrieval, GitHub repository connector and validation logic.
- **Completion criteria:** Three first-party documentation sources inspected, three source-backed summaries, a usable decision brief, a readable research log, and machine-readable evidence.

## Findings

| Framework | Documented emphasis | Practical selection signal | First-party evidence |
| --- | --- | --- | --- |
| OpenAI Agents SDK | Code-first agent integration; tool use, control of your application runtime, handoffs, guardrails and tracing | Start here when an application needs model-driven tool use with a managed SDK agent loop and application-owned integrations | [OpenAI Agents SDK documentation](https://developers.openai.com/api/docs/guides/agents/sdk) |
| Google ADK | Composing multi-agent and multi-node workflows using graph, dynamic, collaborative and templated structures | Consider it when a design needs explicit workflow composition or organized collaboration between agents | [Google ADK workflow documentation](https://adk.dev/workflows/) |
| LangGraph | Persistent graph state: checkpointers for individual threads and stores for information shared across threads | Consider it when recovery, continuity, or durable state are central requirements | [LangGraph persistence documentation](https://docs.langchain.com/oss/python/langgraph/persistence) |

These are **documented capabilities and selection signals**, not measured reliability, price, latency or performance comparisons. Choosing a production stack still requires application-specific implementation and evaluation.

## What happened during the run

1. **Goal and source plan.** The agent chose three project-maintained documentation sites rather than secondary articles, and defined a common comparison: orchestration, state, and production visibility.
2. **Search and retrieval.** It searched for SDK documentation and retrieved pages on OpenAI Agents SDK, Google ADK workflows, and LangGraph persistence.
3. **Observation and correction.** Two documentation URLs redirected: Google ADK's `google.github.io/adk-docs/workflows/` led to `adk.dev/workflows/`; LangGraph's `/durable-execution` led to `/persistence`. The agent used the resolved pages for final evidence.
4. **Analysis.** It avoided a fabricated universal "winner" and mapped each documented strength to a concrete engineering requirement.
5. **Report and verification.** It prepared this report, a JSON research trace, and an on-page summary. Claim-to-source mappings and output structure were checked before publication.

## Result and limits

**Result: the research and reporting goal was completed.** Three official documentation sources were inspected, and the agent produced a cited selection memo plus an evidence file. The need to resolve two changed documentation URLs is an observable example of the retrieve–observe–correct loop.

**What was not measured:** API-token usage, billed model cost, end-to-end wall-clock duration, or runtime execution of the three SDKs. These measures are intentionally omitted rather than inferred from vendor pricing pages. The comparison is a documentation-based decision brief, not an SDK benchmark.

## Verified source list

1. [OpenAI Agents SDK — developer documentation](https://developers.openai.com/api/docs/guides/agents/sdk)
2. [Google ADK — multi-agent workflow documentation](https://adk.dev/workflows/)
3. [LangGraph — persistence documentation](https://docs.langchain.com/oss/python/langgraph/persistence)

**Machine-readable evidence:** [Research trace](./research-agent-trace-2026-10-18.json)

**Reproducibility:** Open each source and check the capabilities listed in the findings table. Source documentation is maintained by its publisher and may change after the date of this run.
