"""Preserve the generated local-inference reference page during scheduled rebuilds."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "guides/run-ai-models-locally/index.html"
def render_local_inference_guide():
    content = PAGE.read_text(encoding="utf-8")
    required = ("https://sxf.si/guides/run-ai-models-locally/", "local-vram-calculator", "FAQPage", "gpu-vram-memory-budget.svg")
    if any(part not in content for part in required):
        raise RuntimeError("Local inference guide is missing a required section")
    return content
