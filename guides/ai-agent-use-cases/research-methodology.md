# SXF Agent Opportunity Atlas — methodological disclosure
Version 1.0, October 22, 2026

Fifty use cases are original SXF editorial design scenarios. They are NOT verified examples of fifty companies using AI agents. Four mutually exclusive suggested workflow classifications: agent candidate, deterministic workflow, AI-assisted drafting and human decision required. The classification is a provisional starting point for a concrete business pilot, not a general ban or universal engineering solution.

The Opportunity Index is a transparent **heuristic**, not a validated probability, objective measure of AI readiness, certification, safety score or guarantee of ROI. Users select 0–5 planning variables; the score must not be used to authorize high-stakes actions or to rank people.

ROI calculator assumptions: baseline human cost = monthly task volume × time per task / 60 × fully loaded hourly cost. New cost = task volume × model cost per attempt + monthly platform costs + manual handling of failed tasks + review labor for accepted tasks. Accepted tasks are assumed to require only the specified review fraction of baseline task time. One-time setup is deducted from illustrative first-year savings. Not included: uncertainty, rework, error loss, management, audit, integration, support or migration. This is arithmetic, not observed company ROI.

The offline Python lab uses 120 **fictional** tasks, with predetermined input-invalid, human-approval and response-loss-after-side-effect faults. It contrasts a naive at-least-once side-effect handler with explicit guard checks and idempotency. No cloud AI, model calls or provider reliability testing. Reproduce: `python sxf-agent-workflow-lab.py`.

Source methodology:
- NIST AI RMF / AI 600-1 guidance on risks, governance, human oversight: https://www.nist.gov/itl/ai-risk-management-framework
- Anthropic guidance on workflows versus agents: https://www.anthropic.com/engineering/building-effective-agents
- Google Cloud architecture on agents and orchestration: https://cloud.google.com/architecture/choose-design-pattern-agentic-ai-system
- OpenAI practical agent-building guide: https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- OWASP LLM and Agentic application security overview: https://genai.owasp.org/

A credible external industry benchmark would require pre-registered tasks, authorized real user data, independently checked acceptance criteria, run traces, actual bills, error rates, and repeat trials. None of those measurements is asserted for the 50 editorial scenarios.
