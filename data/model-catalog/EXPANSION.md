# Catalog coverage and expansion plan

Verified against the current SXF catalog and official provider documentation on 2026-10-06.

## Current coverage

| Provider | Models | Reasoning | Image input | Audio / video input | >=1M context | Official paid API | Open-weight |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI | 6 | 6 | 6 | 0 | 6 | 6 | 0 |
| Anthropic | 4 | 4 | 4 | 0 | 3 | 4 | 0 |
| Google | 2 | 2 | 2 | 2 | 2 | 2 | 0 |
| xAI | 3 | 3 | 3 | 0 | 1 | 3 | 0 |
| Meta | 2 | 0 | 2 | 0 | 2 | 0 | 2 |
| **Total** | **17** | **15** | **17** | **2** | **14** | **15** | **2** |

### What this means

The catalog is already strong on frontier reasoning, image input, long context, and directly comparable paid API pricing. The main structural gap is provider diversity: 13 of 17 tracked models come from OpenAI, Anthropic, and xAI, while major production ecosystems such as Mistral, DeepSeek, Alibaba/Qwen, Cohere, and Amazon Nova are absent.

Audio/video understanding is also concentrated entirely in Google. Open-weight representation currently comes only from Meta.

## Expansion rule

A model should enter the catalog only when it adds at least one of these:

1. A materially missing provider ecosystem.
2. A distinct cost/performance tier.
3. A capability not well represented in the current catalog.
4. Important open-weight deployment coverage.
5. A clearly current production model with official specification and provenance.

Do not add deprecated aliases, minor dated snapshots, or models that only duplicate an already-covered role unless the dated identifier is required to preserve a stable API contract.

## Batch A — highest priority

These models should be verified and added first.

| Priority | Candidate | Why it closes a real gap | Verification readiness |
| --- | --- | --- | --- |
| P0 | DeepSeek V4.1 Flash | Adds DeepSeek, 1M context, multimodal input, reasoning, unusually low official API pricing | Excellent |
| P0 | Mistral Small 4 | Adds Mistral, reasoning + coding + open weights, efficient paid API tier | Excellent |
| P0 | Mistral Medium 3.5 | Adds a stronger Mistral multimodal/agentic tier and open-weight option | Excellent |
| P0 | Qwen3.8 Max | Adds Alibaba/Qwen, 1M context, 131K max output, thinking mode, global paid API | Excellent |
| P1 | Mistral Large 3 | Adds Mistral's large general-purpose tier at a low published Standard token price | Strong |

### Official source anchors

- DeepSeek pricing/specs: https://api-docs.deepseek.com/quick_start/pricing/
- DeepSeek V4.1 release/status: https://api-docs.deepseek.com/updates/
- Mistral model catalog: https://docs.mistral.ai/models
- Mistral pricing: https://docs.mistral.ai/inference/pricing
- Qwen3.8 Max model page: https://docs.modelstudio.console.alibabacloud.com/en/model-studio/qwen3-8-max
- Alibaba Model Studio pricing: https://docs.modelstudio.console.alibabacloud.com/en/model-studio/model-pricing

## Batch B — add after pricing/access normalization review

| Priority | Candidate | Why | Gate before inclusion |
| --- | --- | --- | --- |
| P1 | Cohere Command A+ | Enterprise RAG/agent/reasoning ecosystem, vision input, distinct deployment story | Confirm current self-serve token price vs Model Vault pricing and choose one normalized access contract |
| P1 | Amazon Nova 2 Lite | Adds AWS-native multimodal/reasoning ecosystem with 1M context and 65,536 output | Normalize current Bedrock on-demand pricing and region semantics before calculator eligibility |
| P2 | Amazon Nova 2 Sonic | Adds native speech-to-speech coverage | Requires a separate non-token pricing representation; do not force into text-token calculator |
| P2 | NVIDIA NIM-selected model | Important deployment ecosystem | Keep outside Standard token-price comparison unless a directly comparable provider token rate exists |

## Explicit exclusions for the first expansion

- DeepSeek V4 Pro: official status has been in transition around V4.1 Flash; avoid adding a model whose routing/lifecycle is moving until its stable successor contract is clear.
- Old Qwen snapshots: prefer the current stable alias/version unless a historical page is specifically needed.
- Specialist OCR/TTS/embedding/rerank products: valuable later, but they need pricing units beyond input/output tokens and should not distort the first general-model expansion.
- Third-party hosted models: do not treat a host's price as the model developer's canonical Standard API price without an explicit partner-priced status.

## Target after Batch A

17 -> 22 models, 5 -> 8 providers.

This first increase is intentionally small. It tests the new provider-source architecture with three new ecosystems and multiple pricing shapes before scaling to 30+ models.
