#!/usr/bin/env python3
"""Static/runtime contract checks for the Model Explorer filters."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "models" / "explorer.js").read_text(encoding="utf-8")

assert "const syncProviderUi = () => {\n    syncProviderUi();" not in source, (
    "syncProviderUi must never recurse into itself"
)
assert 'providerButtons.forEach(button => {' in source, (
    "Provider UI sync must update quick provider buttons"
)
assert 'button.setAttribute("aria-pressed", String(active));' in source, (
    "Provider quick buttons must expose pressed state"
)
assert 'providerOptions?.querySelectorAll("[data-provider-option]")' in source, (
    "Provider picker options must stay synchronized"
)
assert 'syncProviderUi();\n\n    capabilityButtons.forEach' in source, (
    "URL hydration must synchronize provider picker state"
)

print("Model Explorer filter runtime contract passed")
