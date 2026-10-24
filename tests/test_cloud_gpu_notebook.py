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
assert full.index('shutil.which("nvidia-smi")')<full.index('ensure_ollama_ready(OUTPUT)')
assert "measure_local_ollama.py" in full
assert '"--image",str(image_file)' in full
assert '"--repeats", "3"' in full or '"--repeats","3"' in full
assert 'kind")!="local-measurement-candidate"' in full
assert 'files.download(str(archive))' in full
assert "local-llm-benchmarks.json" not in full
assert "reviewStatus" not in full and "approved" not in full
assert 'ensure_ollama_ready(OUTPUT)' in full
assert 'OLLAMA, "pull", "qwen3:8b"' in full
assert (root/'scripts/ensure_colab_ollama.py').is_file()
assert '"pull", "--ff-only", "origin", "main"' in full
assert full.count('importlib.reload(ensure_colab_ollama)') == 3
print("PASS: cloud notebook parses, gates GPUs before downloads, invokes local real-inference tools, never writes public benchmark registry")

helper=(root/"scripts/ensure_colab_ollama.py").read_text()
ast.parse(helper)
assert "ollama-linux-amd64.tar.zst" in helper
assert "extractall(path=install_dir, filter=\"data\")" in helper
assert "https://ollama.com/install.sh" not in helper

assert full.count('"fetch", "origin", "main"') == 3

assert full.count('capture_output=True, text=True') >= 2
assert full.count('run.stderr[-12000:]') == 2
measure=(root/'scripts/measure_local_ollama.py').read_text()
ast.parse(measure)
assert '"think":False' in measure
