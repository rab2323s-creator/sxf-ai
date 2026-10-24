#!/usr/bin/env python3
"""Offline validation only. Never claims live NVIDIA GPU measurement."""
import ast,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/"scripts/measure_isolated_gpu_evidence.py").read_text()
ast.parse(s)
assert 'unload_all()' in s
assert 'model_ps.get("size_vram")' in s
assert '"answer": response["response"]' in s
assert '"gpuWideObservedPeakUsedMiB"' in s
assert 'review-required-not-published' in s
assert "local-llm-benchmarks.json" not in s
nb=json.loads((root/"notebooks/sxf_isolated_gpu_benchmark_v2.ipynb").read_text())
assert nb["nbformat"]==4
cells=["".join(x["source"]) for x in nb["cells"] if x["cell_type"]=="code"]
assert len(cells)==3
for c in cells:ast.parse(c)
body="\n".join(cells)
assert body.index('shutil.which("nvidia-smi")') < body.index("ensure_ollama_ready(OUTPUT)")
assert "scripts/measure_isolated_gpu_evidence.py" in body
assert 'files.download(str(archive))' in body
print("PASS: isolated GPU V2 source parses and enforces review-only evidence.")
