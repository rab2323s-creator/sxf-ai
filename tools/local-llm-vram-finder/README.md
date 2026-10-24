# SXF Local LLM VRAM Finder — Data and Evidence Policy

## Architecture
- `data/model-index.json`: SXF's general AI model index. It includes API-only models and must **not** be treated as the local-running catalog.
- `data/local-llm-catalog.json`: publishable artifacts. One entry per exact Ollama tag or GGUF file. **Not** one entry per model family.
- `data/local-llm-sources.json`: an allowlist of candidate Hugging Face GGUF repositories; membership does not imply a repository currently resolves or is safe to execute.
- `scripts/update_local_llm_catalog.py`: fetches Hugging Face file trees, accepts only a single unsharded GGUF file with a positive integer file size, excludes auxiliary mmproj files from being treated as self-contained models, and preserves last known variants for unavailable repositories.
- `data/local-llm-benchmarks.json`: intentionally empty measured-throughput evidence registry. A result is shown only when a separate record provides the exact variant ID, GPU, runtime, quantization, context size, concurrency, measured date and evidence URL.
- `tools/local-llm-vram-finder/selector.js`: browser-side, source-aware filtering and inverse GPU capacity estimator; never phones home to third parties.
- `.github/workflows/refresh-local-llms.yml`: refreshes once weekly and on initial main integration, proposes review changes via PR rather than silently publishing.

## Evidence levels
1. Ollama original 13 tags: rounded registry-published **download sizes** carried from the earlier source check; sizeBytes is null. Historical snapshots must not be called exact-byte verified.
2. Hugging Face GGUF: bytes sourced from a resolved Hub tree **on the successful refresh date**; this is one GGUF file size, not total runtime assets or complete multimodal downloads.
3. Fit: published size in decimal gigabytes plus heuristic buffers of 2 / 3 / 4.5 / 7 GB at 4K / 8K / 16K / 32K context. Adds 1 GB for vision tasks plus an extra 1 GB conservative warning allowance for GGUF vision variants. These constants are not measured KV cache requirements; they vary materially by architecture, runtime, quantization, batch and backend.
4. Generation speed: no `tokens/sec` estimate or quality ranking is inferred from memory, weight count, or file size. No measurement is currently published. Add fully provenance-backed observations separately.

## Review
- Verify each source actually describes the expected model family and a file the target runtime can read.
- Review licensing and usage restrictions using the model card; the catalog's family-level license label is **not** legal confirmation of an individual repack.
- Check GGUF sharding and projector requirements, especially for vision models, before recommending any Ollama or llama.cpp commands.
- Do not describe the file sizes as measured peak VRAM or guaranteed compatibility. Apple unified memory is not a discrete VRAM tier.
- Approve the generated catalog PR only after tests and inspection of source provenance. If sources are offline the updater fails without overwriting the catalog.

## QA
```sh
python scripts/update_local_llm_catalog.py --check
python tests/test_local_llm_catalog.py
python tests/test_best_local_llms_by_vram.py
node --check tools/local-llm-vram-finder/selector.js
python tests/test_best_local_llms_browser.py  # Playwright Chromium required
```

The automatic candidate refresh is **not** evidence that 100–200 model families have been validated. Public count is the count of individually sourced artifact records; breadth is expanded only through reviewed data.

## Vision runtime-evidence pilot (source checking is NOT execution)
- `data/local-llm-runtime-audit.json` lists **three candidate model+projector pairs**: Gemma 3 4B, Qwen3-VL 4B, and Qwen3-VL 8B (Q4_K_M GGUF), plus Ollama text/vision control model IDs. Filename and listing status are source leads only; no compatibility is certified.
- `python scripts/audit_local_vision_sources.py` checks the shortlist against the current catalog entirely offline.
- `python scripts/audit_local_vision_sources.py --refresh` requests Hugging Face repository file trees and verifies exact projector filename and byte size. It writes the audit file only after **all** source queries complete; errors leave the prior reviewed snapshot unchanged. The result is `hub-byte-verified` (bytes only), `not-found`, or previously `listed-not-byte-verified`. **None** of these outcomes is a model-loading result.
- Runtime execution and projector matching must be independently tested with the pinned llama.cpp build and recorded command, GPU, backend, context, image input, model SHA256, projector SHA256 and observed GPU memory. No such vision execution evidence has been collected or published in this pilot.

## Reproducible local GPU measurement capture
A real NVIDIA GPU with `nvidia-smi`, a running **local** Ollama at `127.0.0.1:11434`, and the exact pre-installed Ollama tag is required. Example:
```sh
ollama pull qwen3:8b
python scripts/measure_local_ollama.py --model-id ollama:qwen3:8b --context 4096 --repeats 3 --output local-results/qwen3-8b-4096.json
```
The script makes **one warmup + at least three** deterministic `/api/generate` calls, preserving per-trial `eval_count`, `eval_duration`, generation tokens/sec, wall-clock time and a 200ms `nvidia-smi` sampling record. The sampling is **not** model-exclusive GPU allocation, is not guaranteed to catch a momentary true peak, and does **not** verify 100% GPU residency or image support. A stable GPU, pinned runtime version, and isolation from other processes are essential for any reproducible claim. **No remote inference calls or public benchmark writes occur.** The script does not pull models or install binaries.
```sh
python scripts/review_local_gpu_measurement.py local-results/qwen3-8b-4096.json --evidence-url https://YOUR-IMMUTABLE-REPORT-URL --output local-results/qwen3-8b-review.json
```
Replace the illustrative URL with an **actual immutable public measurement report** after uploading and reviewing the original artifact. The review tool independently verifies model IDs, runtime details, warmup count, numeric consistency and all repeats, and emits a **draft** result only. Publication requires human review for GPU/VRAM isolation, actual runtime residency, licenses, physical hardware provenance and test conditions. Upload artifacts outside the repo until approved; local output paths should never contain private prompts.
- `data/local-llm-benchmarks.json` stays empty until valid real runs and independent evidence exist; synthetic tests only assert rejection behavior. **Never** publish example measurements.
- A VRAM selection estimate remains based on file size plus an illustration buffer, not the sampling output.

## Recommended measurement matrix (not completed)
Review independently: RTX 3060 12GB, RTX 4060 Ti 16GB, RTX 4090 24GB (or equivalently documented hardware). Start with Ollama Qwen3 8B and Qwen2.5 Coder 7B for text controls, then image-capable Ollama Qwen3 VL 4B; for GGUF projector studies, audit Gemma3 4B, Qwen3-VL 4B and Qwen3-VL 8B in a pinned llama.cpp build. Treat untested models and unsupported GPU hardware as **not measured**. Do not extrapolate benchmark results from one device to another.

## Publication approval rule
Only registry entries with `evidenceType: "measured"` and `reviewStatus: "approved"` are rendered in the public selector. Generated trial candidates are `draft-not-published` and must never appear as public results. A reviewer must verify immutable evidence, trial artifacts, device/driver and runtime versions, model identity and offload conditions before approving. Nothing is auto-approved.\n