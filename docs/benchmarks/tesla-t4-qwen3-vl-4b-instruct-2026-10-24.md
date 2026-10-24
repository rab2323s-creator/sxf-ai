# SXF — isolated Tesla T4 Qwen3-VL 4B Instruct Vision evidence (2026-10-24)

**Status: reviewed user-supplied capture, not automatically approved for VRAM Finder publication.** The ZIP and its contents passed cryptographic consistency checks, arithmetic checks, and manual inspection of the actual fixture and answers. This is not an independently reproduced hardware certification. The original archive is **not committed** to GitHub and its SHA-256 alone is not a publicly downloadable evidence source.

## Provenance

- Original user-uploaded archive: `sxf-isolated-gpu-evidence-v2-review (2).zip`; SHA-256: `c7cf9fdca58b443db353d545033cd71230b2c83ecbc3946f960de9640c9eb93a`.
- Original complete report: `qwen3-vl-4b-instruct-isolated.json`, SHA-256: `d2f8ba0bacda9ad6b8b1b373b8cb9e82a53106190b278612b19e5a8c65c96a1f`.
- Fixture: `vision-square.png`, 329 bytes, SHA-256: `a01767e2afbfe9cab25d613c7d391e6057ff018960f9d07a961b064615b0fe7b`.
- Original manifest listed eleven files; all eleven content hashes matched and the ZIP passed its CRC validation. Retain the original archive separately for full audit.
- Execution diagnostics for successful attempt: source commit `0d462dd42e1524c94fc243bea637ec3716b17cfc`, exit code **0**. Earlier failed attempt in the same ZIP used `be172cf56c4f708f60f218a7ece88876d3ae5533` with exit code **1** and targeted the *different* `qwen3-vl:4b` model.
- Dataset here is a **transcription of checked values**, not an unmodified original capture.

## Configuration verified within the capture

| Item | Captured value |
| --- | --- |
| Model | `ollama:qwen3-vl:4b-instruct` (**not** `ollama:qwen3-vl:4b`) |
| Model digest | `84f7ed8042fa7cdbd902f7dcb7d0370e032095047cc3244179f263b77b5bc318` |
| Quantization | Ollama tag metadata: `Q4_K_M` |
| GPU | NVIDIA Tesla T4, 15,360 MiB |
| Driver | `580.82.07` |
| Runtime | Ollama `0.40.10`, `/api/chat` |
| Context | `num_ctx=4096`; requested max output 512 tokens; `think=false`; temperature 0 |
| Runs | One warmup + three separately recorded measured runs, single model resident in `/api/ps` |
| Baseline after unloading | 0 MiB GPU-wide as reported by `nvidia-smi` |
| Image | 128 × 128 PNG; centered red square on blue background |

## Results

| Measured trial (excluding warmup) | Generated tokens | Generation duration (ns) | Generation-only tok/s | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| 1 | 142 | 2,208,094,000 | 64.3089 | 2.2544 |
| 2 | 142 | 2,209,317,000 | 64.2733 | 2.2547 |
| 3 | 142 | 2,215,242,000 | 64.1013 | 2.2608 |
| **Arithmetic mean** | — | — | **64.2278** | — |

Each tok/s value was independently recomputed as `eval_count × 10^9 / eval_duration`, matching the captured report to four decimal places. Warmup (excluded) was 128 tokens, 64.3652 tok/s, wall 10.0309 s including first model load.

**Vision outcome:** The actual 128 × 128 fixture pixel colors were inspected (center RGB 238,42,42; background RGB 36,77,208). All four saved answers, including three measured runs, correctly identify a centered red square against a blue background. Each saved answer's SHA-256 matches its reported `answerSha256`. This verifies **the specific simple fixture response only**, not general image understanding.

**Memory, carefully separated:**
- `nvidia-smi` device-wide, sample-limited (200 ms intervals): 0 MiB baseline; 4,455 MiB maximum observed whole-GPU used during captures. **Not** a verified model-exclusive VRAM requirement.
- Ollama `/api/ps` reported `size_vram=3,571,890,257` bytes = **3,406.42 MiB**. This is Ollama-reported resident model size, **not** an independent proof of full GPU residency or full model-only allocation.
- Ollama tag-reported file/model size: `3,337,225,651` bytes, which is **not** GPU consumption. `/api/ps size=3,571,890,257` bytes is another distinct runtime field.

**Cautions:** Single user-captured T4 session and one simple image; no external attestation of the physical machine or other GPU processes, independent residency verification, worst-case VRAM sizing, longer context, different batch sizes, or other hardware. Tokens/sec excludes image processing/prefill and model loading. These numbers should not be presented as universal speed, minimum required VRAM, or proof that `qwen3-vl:4b` thinking variant passes Vision.

## Publication decision

Do **not** add these figures to `data/local-llm-benchmarks.json` or imply an approved predictor benchmark until the project determines a publicly accessible, immutable original evidence location and an appropriate presentation policy distinguishing measured whole-GPU use, Ollama residency, estimated requirements, and validated fixture output. This report provides checkable documented values and original archive hashes without pretending to host the original capture.
