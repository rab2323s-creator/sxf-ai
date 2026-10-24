#!/usr/bin/env python3
"""Structural validation for isolated user-owned cloud GPU evidence notebook.

This is NOT an actual GPU benchmark. It verifies executable notebook syntax and
fail-closed evidence controls; measured data can only come from a Colab GPU run.
"""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"notebooks/sxf_isolated_vision_verification.ipynb"
book=json.loads(path.read_text())
assert book["nbformat"]==4
cells=book["cells"]
codes=["".join(c["source"]) for c in cells if c["cell_type"]=="code"]
assert len(codes)==5
for i,src in enumerate(codes):
    ast.parse(src,filename=f"isolated-vision-cell-{i}")
body="\n".join(codes)
assert body.index('shutil.which("nvidia-smi")') < body.index('ensure_ollama_ready(OUTPUT)')
assert body.index('Unloading resident model:') < body.index('subprocess.run([OLLAMA,"pull"')
assert body.index('gpuBaselineAfterModelUnload') < body.index('scripts/measure_local_ollama.py')
assert '"/api/ps"' in body
assert '"size_vram"' in body
assert '"visionAnswer":answer' in body
assert '"answerAccuracy":"not-independently-reviewed"' in body
assert '"modelDigest":identity.get("digest")' in body
assert '"--repeats","3"' in body
assert '"--image",str(fixture)' in body
assert 'candidate' not in path.name
assert 'local-llm-benchmarks.json' not in body
assert 'reviewStatus":"manual-review-required"' in body
assert 'files.download(str(archive))' in body
assert 'github.com/rab2323s-creator/sxf-ai' in body
print("PASS: isolated Vision notebook syntax, GPU gate, unload gate, provenance, measured repeats and no auto-publication")
