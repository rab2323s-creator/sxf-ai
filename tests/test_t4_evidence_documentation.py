#!/usr/bin/env python3
"""Audit publicly documented, review-required records without fabricating GPU evidence."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / "data/local-llm-evidence/tesla-t4-2026-10-24"
files = sorted(folder.glob("*.redacted.json"))
assert len(files) == 2, "Exactly two supplied model captures"
expected = {
    "ollama:qwen3:8b": (39.421166666666664, 0, 5467, None),
    "ollama:qwen3-vl:4b": (64.53993333333334, 5467, 9943, "a01767e2afbfe9cab25d613c7d391e6057ff018960f9d07a961b064615b0fe7b"),
}
for path in files:
    artifact = json.loads(path.read_text())
    assert artifact["recordType"] == "sanitized-user-supplied-ollama-capture"
    assert artifact["reviewStatus"] == "review-required-not-published"
    assert artifact["redactions"] == ["measurement.gpu.uuid"]
    assert len(artifact["sourceCaptureSha256"]) == 64
    m = artifact["measurement"]
    assert m["publicationStatus"] == "review-required"
    assert m["gpu"]["name"] == "Tesla T4" and m["gpu"]["totalMiB"] == 15360
    assert "uuid" not in m["gpu"]
    assert m["runtime"] == "Ollama" and m["runtimeVersion"] == "0.40.10"
    assert m["contextTokens"] == 4096 and m["repetitions"] == 3 and m["warmupCount"] == 1
    assert m["modelId"] in expected
    mean, baseline, peak, image_sha = expected[m["modelId"]]
    assert m["gpu"]["usedMiB"] == baseline
    assert m["inputImageSha256"] == image_sha
    trials = m["runRecords"]
    assert len(trials) == 4 and trials[0]["warmup"] is True
    measured = trials[1:]
    assert all(r["warmup"] is False for r in measured)
    assert all(r["observedPeakGpuUsedMiB"] == peak for r in trials)
    assert all(r["observedGpuUsedDeltaMiB"] == peak - baseline for r in trials)
    for t in measured:
        real = t["completionTokens"] * 1e9 / t["generationDurationNs"]
        assert math.isclose(real, t["tokensPerSecond"], abs_tol=0.0001)
    actual_mean = sum(t["tokensPerSecond"] for t in measured) / len(measured)
    assert math.isclose(actual_mean, mean, abs_tol=0.00001)

registry = json.loads((ROOT / "data/local-llm-benchmarks.json").read_text())
assert registry["measurements"] == [], "Unapproved results must not appear in website registry"
report = (ROOT / "docs/benchmarks/tesla-t4-ollama-2026-10-24.md").read_text()
assert "39.42" in report and "64.54" in report
assert "review-required-not-published" in report
assert "not" in report.lower()
print("PASS: both source-linked sanitized Tesla T4 records pass measured arithmetic and remain unpublished")
