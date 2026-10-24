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
