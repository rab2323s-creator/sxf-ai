"""SXF / AI news relevance policy, independent from SEO quality."""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NewsDecision:
    status: str   # accept | review | reject
    reason: str


AI_FIRST_SOURCES = {"OpenAI", "Google AI", "Anthropic", "Meta", "xAI"}
AI_RESEARCH_SOURCES = {"Google Research", "Microsoft"}
AI_COMMUNITY_SOURCES = {"Hugging Face"}
AI_TITLE = re.compile(
    r"\b(?:ai|artificial intelligence|generative ai|genai|"
    r"agentic|agents?|llms?|large language models?|machine learning|"
    r"deep learning|pretrain(?:ing|ed)|neural|multimodal|"
    r"foundation models?|vision.language|inference|gpt[- .]?\d|"
    r"chatgpt|codex|claude|gemini|grok|copilot|mcp|model context protocol|"
    r"diffusers?|llama|qwen|nemotron|granite|apertus|flux[.-]?\d|"
    r"falcon asr|asr|text.to.speech|open.weights?|model weights?|"
    r"quantiz(?:ation|ed)|benchmark(?:s|ing)?|reasoning models?|"
    r"prompt injection|tool calling|computer use)\b", re.I
)
GITHUB_DIRECT = re.compile(
    r"\b(?:github copilot|copilot|ai scan|ai[- ]powered|agentic|"
    r"ai agents?|artificial intelligence|generative ai|"
    r"large language models?|llms?|gpt[- .]?\d|chatgpt|codex|"
    r"claude (?:opus|sonnet|haiku)|gemini(?: \d| in copilot)|"
    r"mcp servers?|model context protocol|local ai models?|"
    r"model for leaked secret detection)\b", re.I
)
GITHUB_AI_SUMMARY = re.compile(
    r"\b(?:github copilot|copilot cli|ai scan for pull requests|"
    r"agentic autofix|agentic coding|ai coding agents?|"
    r"ai[- ]powered (?:code|coding|security|development)|"
    r"large language models?|llm[- ]powered|model context protocol|"
    r"mcp servers?|local (?:ai )?models? (?:in|for|with) copilot)\b", re.I
)
GITHUB_MODEL_WITH_AI = re.compile(
    r"\b(?:purpose.built model|model for leaked secret detection|"
    r"model[- ]powered)\b", re.I
)
GITHUB_SECONDARY_CONTEXT = re.compile(
    r"\b(?:anthropic|openai|ai[- ]enabled|ai agent|"
    r"machine learning|neural model)\b", re.I
)
BOILERPLATE = re.compile(
    r"^\s*(?:we.re on a journey to advance and democratize artificial "
    r"intelligence through open source and open science\.?|"
    r"a blog post by .+ on hugging face|blog post|read more|learn more)\s*$",
    re.I
)


def substantive_summary(value: str) -> str:
    """Remove known publisher slogans, not informative short descriptions."""
    summary = (value or "").strip()
    return "" if BOILERPLATE.fullmatch(summary) else summary


def assess_news(title: str, summary: str, source: str) -> NewsDecision:
    """Source-specific, auditable classification. Review is not auto-accepted."""
    title = (title or "").strip()
    summary = substantive_summary(summary)
    source = (source or "").strip()
    if not title or not source:
        return NewsDecision("review", "missing_title_or_source")
    if source == "GitHub":
        if GITHUB_DIRECT.search(title):
            return NewsDecision("accept", "github_explicit_ai_topic")
        if GITHUB_AI_SUMMARY.search(summary):
            return NewsDecision("accept", "github_ai_product_in_summary")
        if GITHUB_MODEL_WITH_AI.search(title) and re.search(
            r"\b(?:ai agent|machine learning|ai[- ]powered)\b", summary, re.I
        ):
            return NewsDecision("accept", "github_verified_model_context")
        if GITHUB_SECONDARY_CONTEXT.search(title + " " + summary):
            return NewsDecision("review", "github_indirect_ai_mention")
        return NewsDecision("reject", "github_general_platform_update")
    if source in AI_FIRST_SOURCES:
        return NewsDecision("accept", "ai_primary_source")
    if source in AI_COMMUNITY_SOURCES:
        if AI_TITLE.search(title + " " + summary):
            return NewsDecision("accept", "ai_community_topic")
        return NewsDecision("review", "ai_community_insufficient_context")
    if source in AI_RESEARCH_SOURCES:
        if AI_TITLE.search(title + " " + summary):
            return NewsDecision("accept", "ai_research_topic")
        return NewsDecision("review", "research_topic_unconfirmed")
    return NewsDecision("review", "unrecognized_source")


def primary_category(title: str, source: str, summary: str = "",
                     default: str = "Tools") -> str:
    """Prefer explicit model/research evidence over the generic source fallback."""
    t = (title or "").lower().replace("–", "-").replace("—", "-")
    s = (summary or "").lower()
    if source == "GitHub" and re.search(
        r"\b(?:copilot|ai scan|agentic autofix)\b", t + " " + s
    ):
        return "Tools"
    if re.search(
        r"\b(?:open[- ]source|open[- ]weights?|model weights?|"
        r"open[- ]weight|checkpoint|llama\.cpp|mlx|quantiz(?:ation|ed))\b", t
    ):
        return "Open Source"
    if re.search(
        r"\b(?:research paper|research study|study|benchmark|evaluation|"
        r"scientific paper|safety research|assessment|misalignment)\b", t
    ) or (re.search(r"\b(?:research|paper|science)\b", t) and not re.search(
        r"\b(?:research runs|research uses|research builds)\b", t
    )):
        return "Research"
    if re.search(
        r"\b(?:gpt[- ]\d+(?:\.\d+)?|claude(?:\s+\w+)?\s+\d+(?:\.\d+)?|"
        r"gemini(?:\s+\d+(?:\.\d+)?)?|lfm\d|apertus\s+\d|falcon asr|"
        r"vision.language model|reasoning model|foundation model|"
        r"multimodal model|language model|llm)\b", t
    ):
        return "Models"
    return default if default in {"Tools", "Models", "Research", "Open Source"} else "Tools"


def partition_news_rows(rows):
    """Split ingestion into approved, human-review, and rejected candidates.

    Neither review nor rejected rows may enter the public archive as new pages.
    Legacy archive records are deliberately not modified by this helper.
    """
    approved, review, rejected = [], [], []
    for item in rows:
        decision = assess_news(item.get("title", ""), item.get("summary", ""), item.get("source", ""))
        if decision.status == "accept":
            approved.append(item)
        elif decision.status == "review":
            review.append(item)
        else:
            rejected.append(item)
    return approved, review, rejected
