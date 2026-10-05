# Catalog coverage quality review

Verified against the canonical SXF model catalog on 2026-10-06.

## Executive conclusion

The catalog has moved past the point where raw provider count is the main bottleneck.

Current state:
- 23 models
- 10 providers
- 21 reasoning-capable models
- 23 image-input models
- 4 video-input models
- 2 audio-input models
- 17 models with >=1M context
- 20 official-paid models
- 19 calculator-eligible models
- 4 open-weight models

The next highest-value investment is **structured model taxonomy + Explorer UX**, not immediate bulk catalog expansion.

Why: SXF now covers the major provider ecosystems well enough for a credible general-purpose comparison surface, but several important distinctions are still encoded indirectly in prose rather than explicit fields.

## Coverage strengths

### Provider diversity

The catalog now covers 10 ecosystems:
- OpenAI
- Anthropic
- Google
- xAI
- Meta
- DeepSeek
- Mistral AI
- Alibaba Cloud / Qwen
- Cohere
- Amazon

Provider concentration is materially healthier than at the 17-model stage. The largest three provider groups account for 13 of 23 models (~56.5%), while seven additional ecosystems are represented.

### General frontier coverage

Reasoning, image input and long-context capability are already well represented:
- 21 / 23 reasoning
- 23 / 23 image input
- 17 / 23 at >=1M context

Adding more general-purpose frontier models now has diminishing marginal value unless a model adds a new access mode, modality, specialist task, or materially different economics.

### Pricing comparability

19 / 23 models are directly calculator-eligible.

The exceptions are intentional:
- Meta open-weight models have no canonical provider Standard API token rate.
- DeepSeek has time-variable peak/off-peak pricing.
- Command A+ is free within API rate limits and has instance-priced private deployment.

This is healthy: SXF is preserving pricing semantics instead of forcing everything into one calculator contract.

## Weakest areas

### 1. Model taxonomy is not first-class

Important product dimensions are not explicit fields in the canonical schema.

Examples:
- open-weight status
- lifecycle: current / preview / legacy / deprecated
- coding specialization
- agentic/tool-use specialization
- speech / transcription / TTS
- OCR / document extraction
- embeddings
- reranking
- moderation / safety
- deployment class

Today, some of these are inferred from `positioning`, `notes`, provider name, or page copy.

That is acceptable for 20 models, but not for 50–100.

### 2. Open-weight filtering is heuristic

The current Explorer considers a model open-weight when the phrase appears in `positioning` or when the provider is Meta.

This is brittle. A factual access property should never depend on editorial copy.

Recommended canonical field:

```json
"access": {
  "official_api": true,
  "open_weight": true,
  "self_hostable": true
}
```

Optional factual license:

```json
"license": {
  "name": "Apache 2.0",
  "url": "https://..."
}
```

### 3. Specialist coverage is shallow

The catalog is intentionally focused on general-purpose generation models.

Current measurable modality gaps:
- audio input: 2 / 23
- video input: 4 / 23

Specialist model classes such as OCR, speech-to-speech, transcription, rerank and embeddings are effectively absent.

That is not yet a defect. It becomes a defect only after the product can represent their different units and capabilities cleanly.

For example:
- OCR may price per page
- transcription may price per minute
- TTS may price per character
- rerank may price per search unit / token bundle
- embeddings may have input-only token pricing

Do not add these to the current input/output-token contract until pricing units are generalized.

### 4. Explorer provider controls are approaching scale limits

Ten provider buttons are manageable, but this pattern does not scale cleanly to 15–20 providers, especially on mobile.

Recommended direction:
- keep quick chips for top/high-frequency providers
- move the complete provider list into a searchable select/popover
- preserve URL state
- show active-filter count
- support structured task/capability facets

### 5. Use-case discovery is weaker than raw-spec discovery

The Explorer can currently filter by:
- provider
- reasoning
- image
- audio/video
- context
- access
- verification
- pricing sort

It cannot directly answer:
- Which models are coding-specialized?
- Which are best suited to agents/tool use?
- Which are open-weight and multimodal?
- Which support video?
- Which are speech-native?
- Which are specialist retrieval models?

Before adding many specialist models, SXF should make these dimensions explicit and filterable.

## Recommended next architecture

### Phase 1 — factual taxonomy

Add structured fields to every model:

```json
"access": {
  "official_api": true,
  "open_weight": false,
  "self_hostable": false
},
"lifecycle": {
  "status": "current"
},
"capabilities": [
  "reasoning",
  "coding",
  "agents",
  "vision",
  "video"
]
```

Capability values must be backed by official documentation. Avoid subjective labels such as "best" or "recommended" in canonical data.

Suggested controlled vocabulary:
- reasoning
- coding
- agents
- tool-use
- vision
- video
- audio
- speech-to-speech
- transcription
- tts
- ocr
- embeddings
- rerank
- moderation
- long-context

### Phase 2 — Explorer upgrade

Use the structured taxonomy to add:
- Task filter: General / Coding / Agents / Retrieval / Speech / OCR
- modality split: Image / Video / Audio instead of combined Audio/Video
- Access: Paid API / Free API / Open weights / Self-hostable
- Lifecycle: Current / Preview / Legacy
- scalable provider picker
- URL persistence for all new filters

### Phase 3 — specialist expansion

Once the data contract supports specialist classes, add a small specialist batch.

Strong current examples from official documentation include:
- Codestral for coding
- qwen3-coder-next for repository-level coding
- Cohere Rerank v4.0 Pro / Fast for retrieval
- Mistral OCR 4.1 for document extraction
- Voxtral Mini Transcribe 2 for speech transcription
- Amazon Nova 2 Sonic for speech-to-speech

Each should use its native pricing unit rather than being forced into `input/output per MTok`.

## Priority decision

| Next action | Value | Reason |
| --- | ---: | --- |
| Structured taxonomy + Explorer upgrade | 10/10 | Unlocks reliable scale and makes the existing 23-model catalog more useful immediately |
| Specialist model batch | 8.5/10 | High differentiation, but needs taxonomy and generalized pricing units first |
| More open-weight generalists | 7.5/10 | Useful, but current open-weight representation is already non-zero and the filtering contract is the bigger issue |
| More general frontier models | 5.5/10 | Lowest marginal value after reaching 10 providers |

## Recommended next implementation

Do **structured taxonomy first**, then wire it into the Explorer.

This is the last major data-model step needed before SXF can scale the catalog aggressively without accumulating brittle heuristics.
