#!/usr/bin/env python3
"""Offline failure/reuse safeguards: no GPU benchmarks are performed here."""
import ast
import importlib.util
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("isolated", root / "scripts/measure_isolated_gpu_evidence.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixture_hash = module.hashlib.sha256(module.png_fixture()).hexdigest()
row = {"trial": 0, "warmup": True, "tokensPerSecond": 12.0, "answer": "red square"}
record = {
    "schemaVersion": 2, "publicationStatus": "review-required-not-published",
    "modelTag": "qwen3-vl:4b", "workload": "vision",
    "modelDigest": "a"*64, "contextTokens": 4096, "repetitions": 3,
    "warmupCount": 1, "imageSha256": fixture_hash,
    "runRecords": [{**row, "trial": i, "warmup": i == 0} for i in range(4)]
}
assert module.valid_completed_report(record, "qwen3-vl:4b", "vision", 4096, 3, fixture_hash)
assert not module.valid_completed_report(record, "qwen3:8b", "vision", 4096, 3, fixture_hash)
assert not module.valid_completed_report(record, "qwen3-vl:4b", "vision", 8192, 3, fixture_hash)
assert not module.valid_completed_report(record, "qwen3-vl:4b", "vision", 4096, 3, "bad")
assert not module.valid_completed_report({**record, "runRecords": record["runRecords"][:2]}, "qwen3-vl:4b", "vision", 4096, 3, fixture_hash)
assert not module.valid_completed_report({**record, "runRecords": [{**x, "answer": ""} for x in record["runRecords"]]}, "qwen3-vl:4b", "vision", 4096, 3, fixture_hash)
with tempfile.TemporaryDirectory() as directory:
    destination = Path(directory) / "partial.json"
    module.save_json_atomic(destination, {"publicationStatus": "incomplete-do-not-publish", "runRecords": [row]})
    assert json.loads(destination.read_text())["runRecords"] == [row]
    assert not destination.with_suffix(".json.tmp").exists()
nb = json.loads((root / "notebooks/sxf_isolated_gpu_benchmark_v2.ipynb").read_text())
cells = ["".join(cell["source"]) for cell in nb["cells"] if cell["cell_type"] == "code"]
for cell in cells:
    ast.parse(cell)
assert "supports_vision_resume()" in cells[0]
assert 'FALLBACK_REF="fix/isolated-vision-resumable-evidence-v3"' in cells[0]
assert "BENCHMARK_SHA=" in cells[0]
assert "WORKLOAD=\"vision\"" in cells[1]
assert "benchmark-stdout-" in cells[1]
assert "benchmark-stderr-" in cells[1]
assert "benchmark-run-" in cells[1]
assert '"exitCode":run.returncode' in cells[1]
assert 'benchmark-stderr-*.log' in cells[2]
assert '"--workload",WORKLOAD' in cells[1]
assert "if run.returncode:raise" not in cells[1]
assert '*-partial-*.json' in cells[2]
assert '"incomplete-do-not-publish"' in cells[2]
assert 'files.download(str(archive))' in cells[2]
print("PASS: offline resume validation, atomic partial evidence, and failure ZIP safeguards")
