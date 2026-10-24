#!/usr/bin/env python3
"""Ensure hosted GPU notebook only captures genuine review-required measurements."""
import json
import ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]
book=json.loads((root/"notebooks/sxf_cloud_gpu_benchmark.ipynb").read_text())
assert book["nbformat"]==4
cells=book["cells"]
codes=["".join(x["source"]) for x in cells if x["cell_type"]=="code"]
assert len(codes)>=6
for i,src in enumerate(codes):
    ast.parse(src,filename=f"notebook-cell-{i}")
full="\n".join(codes)
assert full.index('shutil.which("nvidia-smi")')<full.index('"ollama","pull"')
assert "measure_local_ollama.py" in full
assert '"--image",str(image_file)' in full
assert '"--repeats","3"' in full
assert 'kind")!="local-measurement-candidate"' in full
assert 'files.download(str(archive))' in full
assert "local-llm-benchmarks.json" not in full
assert "reviewStatus" not in full and "approved" not in full
assert 'http://127.0.0.1:11434/api/version' in full
print("PASS: cloud notebook parses, gates GPUs before downloads, invokes local real-inference tools, never writes public benchmark registry")
