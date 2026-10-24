# SXF — Tesla T4 user-captured Ollama benchmarks (24 October 2026)

**Status: documented for public audit, NOT approved for benchmark display.** These are real *user-supplied inference measurement records*, with arithmetic and archive integrity checked; the physical GPU environment has not been independently reproduced or audited. They must not be represented as guaranteed VRAM requirements, end-to-end latency, vision correctness, or universally reproducible speeds.

## Source and scope

- Original evidence: `sxf-cloud-gpu-evidence.zip` uploaded privately by the tester on 2026-10-24. Full archive SHA-256: `1105529c06a979f7426b4321827a5042ba4b779eb52a59cf9619554116f7baf4`. The original ZIP is **not publicly hosted** in this repository; its hash is only an integrity reference, not independent public verification.
- Original manifest SHA-256: `6ffbb20a0695be2b2af0490a057cb601762c3f4e1f82df5414e532b396d93f57`.
- Original `qwen3-8b-4096.json` SHA-256: `62c86471bd7db192909ff3fc03bd8e8356c097374eeeb9595eba9e7089dbae6d`.
- Original `qwen3-vl-4b-4096.json` SHA-256: `7ee38a2718bf6b3df58b232c709e7dabcce63de6287206f1cdc1a94c2ec0e30a`.
- Original `vision-square.png` SHA-256: `a01767e2afbfe9cab25d613c7d391e6057ff018960f9d07a961b064615b0fe7b`, 329 bytes. The image is a red square centered on a blue background.
- GitHub retains only [redacted **text** trial data](../../data/local-llm-evidence/tesla-t4-2026-10-24/qwen3-8b-4096.redacted.json) and [redacted **vision** trial data](../../data/local-llm-evidence/tesla-t4-2026-10-24/qwen3-vl-4b-4096.redacted.json). These are derived from the original JSON; GPU UUID is omitted, therefore their own file hashes **do not equal** original hashes. Do not describe them as raw captures.

## Recorded measurement setup

| Property | Recorded value |
| --- | --- |
| GPU | NVIDIA Tesla T4, 15,360 MiB |
| Software | Ollama 0.40.10 |
| Context | Requested 4,096 tokens |
| Requested output | Up to 192 tokens; `think=false` requested |
| Concurrency | One |
| Repetitions | One warmup + three recorded generations per model |
| Calculation | `eval_count × 10⁹ / eval_duration`, generation-only tokens/sec from Ollama API |
| GPU memory | `nvidia-smi` **whole-GPU** memory used, polled every 200 ms; not model-exclusive allocation |
| Quantization | Publisher Ollama tag; exact quantization **not verified** in captured report |
| Device/software isolation | No independent check of driver version, background GPU processes, offload fraction or full residency |

## Actual three measured runs (warmups excluded)

| Model | Workload | Recorded tok/s for each run | Mean tok/s¹ | Baseline GPU used | Highest observed whole-GPU used |
| --- | --- | --- | ---: | ---: | ---: |
| `ollama:qwen3:8b` | Chat | 39.1627, 39.6329, 39.4679 | **39.42** | 0 MiB | 5,467 MiB |
| `ollama:qwen3-vl:4b` | Vision request with PNG | 64.6301, 64.5992, 64.3905 | **64.54** | 5,467 MiB | 9,943 MiB |

¹ Arithmetic mean of the three **measured** generation-only speeds; presented as a summary for this report, **not** as a selectable benchmark or a prediction for other devices.

For Vision, observed additional whole-GPU use over its existing baseline was **4,476 MiB** (9,943 − 5,467), **not** a clean VRAM measurement of Qwen3-VL alone. The previous chat model could still be resident. The 9,943 MiB reading must not be attributed to Vision alone. An isolated GPU baseline and Ollama `/api/ps` record are still required to investigate residency.

The Vision measurement submitted an actual PNG and received non-empty generation tokens, but **the response text was not preserved**. Therefore image recognition correctness is **not verified**. Workload prompts differ and token/sec across models **cannot be interpreted as a model-quality comparison**. Prefill, model loading, first-token latency and wall-clock response time are not included in generation-only token/sec.

## Quality and provenance gates

**Passed on supplied artifacts:** exact expected four trial records for each model (including warmup); 3 independent measured trial records each; per-trial throughput arithmetic consistency; matching manifest SHA-256 entries; Vision fixture SHA-256; positive token counts/durations; nonempty runtime, model tag, context and NVIDIA GPU fields.

**Not yet confirmed:** independent origin of GPU readings, clean-model VRAM footprint, complete on-GPU residency, exact publisher quantization/digest, detailed driver/hardware isolation, and Vision answer correctness. Original raw evidence is private and not yet available as an immutable public artifact. The above checks do not turn user-provided evidence into independent hardware certification.

**Decision:** keep `data/local-llm-benchmarks.json` unchanged (`measurements: []`). Document trial records only, marked `review-required-not-published`. The browser finder will not render these as approved performance data. To approve in future, preserve an accessible immutable original capture; review licenses/model identity/offload and isolated GPU state; manually verify the actual image answer. Do not upgrade results to `reviewStatus: "approved"` merely because this report exists.

## Reproduction

Scripts: `scripts/measure_local_ollama.py` and `scripts/review_local_gpu_measurement.py`. Original collection notebook: `notebooks/sxf_cloud_gpu_benchmark.ipynb`. Follow-up isolated Vision notebook: `notebooks/sxf_isolated_vision_verification.ipynb` (not yet successfully captured). Rerunning these may produce different results due to runtime, model, hardware and background load.
