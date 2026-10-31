"""Conservative, independently testable editorial importance gate.

A source may be AI-relevant without publishing a material AI development.
Ambiguous cases go to review, never to automatic publication. The original
relevance policy and individually reviewed decisions remain authoritative.
"""
from __future__ import annotations

import re

from editorial_review import REVIEWED_NEWS
from news_relevance import NewsDecision, assess_news


NAMED_MODEL = re.compile(
    r"\b(?:gpt[- ]?\d+(?:\.\d+)?|claude\s+(?:opus|sonnet|haiku|\w+)\s+\d+"
    r"|gemini\s+\d+(?:\.\d+)?|grok[- ]?\d+|llama[- ]?\d+"
    r"|lfm\d+|nemotron(?:\s+\d+(?:\.\d+)?)?|granite(?:\s+\w+)?\s+\d+"
    r"|apertus\s+\d+|falcon\s+asr|flux[- ]?\d+|qwen\s*\d+"
    r"|deepseek[- ]?v?\d+)\b", re.I,
)
AI_TECH = re.compile(
    r"\b(?:ai|llms?|language models?|foundation(?:al)? models?|"
    r"machine learning|neural|agents?|agentic|copilot|inference|"
    r"pretraining|multimodal|model(?:s)?|chatgpt|codex|mcp|"
    r"gpu|robotics|speech recognition|asr|computer use)\b", re.I,
)
RELEASE = re.compile(
    r"\b(?:introduc(?:e|es|ed|ing)|launch(?:es|ed|ing)?|"
    r"releas(?:e|es|ed|ing)|debut(?:s|ed)?|announc(?:e|es|ed|ing)|"
    r"open[- ]sourc(?:e|es|ed|ing)|new generation|generally available|"
    r"now available|rolling out|coming to)\b", re.I,
)
CAPABILITY = re.compile(
    r"\b(?:new|adds?|supports?|enabl(?:e|es|ed|ing)|"
    r"generat(?:e|es|ed|ing)|build|deploy|orchestrat(?:e|es|ion)|"
    r"route|realtime|real[- ]time|reasoning|multimodal|"
    r"vision|voice|speech|context window|function calling|"
    r"tool calling|batch api|api|inference|open weights?|"
    r"open[- ]source|checkpoint|quantiz(?:ation|ed))\b", re.I,
)
TECHNICAL_CHANGE = re.compile(
    r"\b(?:pricing|price cut|cost reduction|latency|throughput|"
    r"benchmark|evaluation|performance|training|pretraining|"
    r"post[- ]training|fine[- ]tuning|quantiz(?:ation|ed)|"
    r"inference|context window|open weights?|open[- ]source|"
    r"architecture|algorithm|framework|method(?:ology)?|"
    r"research|reasoning|accuracy|retrieval|security|safety)\b", re.I,
)
MEASURABLE = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*(?:x|×|times|tokens?|"
    r"hours?|ms|million|billion)|outperform(?:s|ed)?|"
    r"cut(?:s|ting)?|reduc(?:e|es|ed|ing)|improv(?:e|es|ed|ing)|"
    r"accelerat(?:e|es|ed|ing)|more accurat(?:e|ely)|"
    r"new (?:way|method|framework|algorithm)|first[- ]of[- ]its[- ]kind)\b", re.I,
)
SAFETY = re.compile(
    r"\b(?:misalignment|alignment|vulnerabilit(?:y|ies)|"
    r"prompt injection|frontier model safety|security|"
    r"cyber(?:security)?|safety|jailbreak|model abuse)\b", re.I,
)
SAFETY_CHANGE = re.compile(
    r"\b(?:detect(?:s|ion)?|mitigat(?:e|es|ion)|prevent(?:s|ion)?|"
    r"secur(?:e|es|ing)|protect(?:s|ions?)?|discover(?:s|ed)?|"
    r"fix(?:es|ed)?|patch(?:es|ed)?|evaluat(?:e|es|ion)|"
    r"assess(?:es|ment)?|research|report|investigat(?:e|ion)|"
    r"autofix|scan|red[- ]team)\b", re.I,
)
RESEARCH_IMPACT = re.compile(
    r"\b(?:screening|diagnos(?:is|tic)|healthcare|medical|"
    r"climate|earth|scientific discovery|continual learning|"
    r"memory|robustness|reliability|geospatial|drug discovery|"
    r"forecasting|research ideas?|scientific understanding)\b", re.I,
)
LIFECYCLE = re.compile(
    r"\b(?:deprecat(?:e|es|ed|ion|ing)|sunset|retir(?:e|es|ed|ement)|"
    r"breaking changes?|end of support|discontinu(?:e|ed))\b", re.I,
)
ROUTINE = re.compile(
    r"\b(?:permissions?|dashboard|notifications?|"
    r"weekly (?:release|roundup)|roundup|saved views?|"
    r"new (?:fields?|settings?)|usage metrics?|"
    r"admin(?:istration)?|license usage|workflow lockfiles?|"
    r"runner image|repository plugin defaults?)\b", re.I,
)
PROMOTIONAL = re.compile(
    r"\b(?:partnership|partner(?:s|ed)? with|"
    r"how .+ (?:uses?|used|is using)|customer story|"
    r"case study|enterprise pilot|\d+% roi|"
    r"our newest ai quest|future of the firm|"
    r"joins? .+ (?:community|team)|expands? (?:its |our )?partnership)\b", re.I,
)


def assess_importance(title: str, summary: str = "", source: str = "") -> NewsDecision:
    """Evaluate whether the headline establishes a consequential AI event.

    High confidence publishes; vague, promotional and routine updates are
    held for human review. Never infer a breakthrough from publisher identity.
    """
    title = (title or "").strip()
    summary = (summary or "").strip()
    if not title:
        return NewsDecision("review", "importance_missing_headline")

    model = bool(NAMED_MODEL.search(title))
    technical = bool(TECHNICAL_CHANGE.search(title))
    ai = bool(AI_TECH.search(title + " " + summary))
    # Promotions with only indirect AI mentions must not inherit the weight of
    # a trusted publisher. Explicit model releases below take precedence.
    if PROMOTIONAL.search(title) and not (model and RELEASE.search(title)):
        return NewsDecision("review", "importance_promotional_or_case_study")

    if model and re.search(r"\bin (?:github )?copilot\b", title, re.I):
        return NewsDecision("accept", "importance_named_model_platform_availability")
    if model and (RELEASE.search(title) or CAPABILITY.search(title) or TECHNICAL_CHANGE.search(title) or MEASURABLE.search(title)):
        return NewsDecision("accept", "importance_named_model_event")
    if ai and RELEASE.search(title) and TECHNICAL_CHANGE.search(title):
        return NewsDecision("accept", "importance_technical_release")
    if ai and LIFECYCLE.search(title) and (model or "copilot" in title.lower() or "api" in title.lower()):
        return NewsDecision("accept", "importance_model_lifecycle_change")
    if ai and SAFETY.search(title) and SAFETY_CHANGE.search(title):
        return NewsDecision("accept", "importance_specific_safety_development")
    if ai and technical and MEASURABLE.search(title):
        return NewsDecision("accept", "importance_measurable_technical_advance")
    if ai and source in {"Google Research", "Hugging Face", "Microsoft"} and (
        (RESEARCH_IMPACT.search(title) and (CAPABILITY.search(title) or technical or re.search(r"\b(?:screening|diagnos(?:is|tic)|learning)\b", title, re.I)))
        or (re.search(r"\b(?:new|novel|proposed)\b", title, re.I) and technical)
    ):
        return NewsDecision("accept", "importance_specific_research")
    if ai and CAPABILITY.search(title) and (
        re.search(r"\b(?:api|copilot|agentic|agents?|mcp|models?)\b", title, re.I)
        and re.search(r"\b(?:generat(?:e|es)|orchestrat(?:e|es)|route|"
                      r"build|deploy|autofix|scan|supports?|available)\b", title, re.I)
    ):
        if not ROUTINE.search(title):
            return NewsDecision("accept", "importance_product_capability")
    if ROUTINE.search(title):
        return NewsDecision("review", "importance_routine_product_update")
    return NewsDecision("review", "importance_impact_unconfirmed")


def assess_editorial_news(title: str, summary: str, source: str, url: str = "") -> NewsDecision:
    """A news item must clear *both* the unchanged relevance and importance gates."""
    relevance = assess_news(title, summary, source, url)
    if relevance.status != "accept":
        return relevance
    reviewed = REVIEWED_NEWS.get((url or "").strip())
    if reviewed and reviewed["title"] == title.strip() and reviewed["source"] == source.strip():
        # Source-specific, human-reviewed exceptions remain intentional.
        return relevance
    return assess_importance(title, summary, source)
