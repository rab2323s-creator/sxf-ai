#!/usr/bin/env python3
"""Check the Compare extension is deterministic, non-destructive and fail-closed."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ensure_compare_v2 import restore, validate
page = (Path(__file__).resolve().parents[1] / "compare" / "index.html").read_text(encoding="utf-8")
validate(page)
assert restore(page) == page, "Restore must not duplicate existing components"
baseline = page
blocks = (
    ('<div class="compare-builder-presets"', '<div class="compare-builder-workload">'),
    ('<div class="compare-builder-volume"', '<section class="compare-decision-shell"'),
    ('<section class="compare-decision-shell"', '<div id="compareBuilderError"'),
    ('<div id="compareBuilderError"', '<div id="compareBuilderResults"'),
    ('<section id="compareEvidence"', '<div id="compareCuratedLink"'),
)
for start, end in blocks:
    i = baseline.index(start)
    j = baseline.index(end, i)
    baseline = baseline[:i] + baseline[j:]
for asset in (
    '<link rel="stylesheet" href="/compare/compare-enhancements.css">',
    '<script src="/compare/decision-engine.js" defer></script>',
    '<script src="/compare/decision-cockpit.js" defer></script>',
):
    assert asset in baseline
    baseline = baseline.replace(asset, "", 1)
rebuilt = restore(baseline)
validate(rebuilt)
assert restore(rebuilt) == rebuilt
assert 'data-compare-builder' in rebuilt
assert 'id="compareBuilderResults"' in rebuilt
assert 'id="compareEvidence"' in rebuilt
assert 'id="compareDecisionCockpit"' in rebuilt
try:
    restore("<html><main>wrong generator output</main></html>")
except ValueError:
    pass
else:
    raise AssertionError("Generator contract drift must fail loudly")
print("PASS: Compare V2 post-generation restoration, idempotence and guard")
