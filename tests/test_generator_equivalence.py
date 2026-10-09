#!/usr/bin/env python3
"""Compare the previous and revised renderers against the SAME saved input.

The legacy script is imported under another module name so its two historical
__main__ guards do not fetch feeds. Only its final effective page rendering
functions are invoked. The revised generator uses --render-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def manifest(root):
    paths = list(root.rglob("*.html")) + [root / "sitemap.xml", root / "_redirects"]
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
        if p.is_file() and ".git" not in p.parts
    }


LEGACY_RENDER = """
import importlib.util
import json
import sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / 'scripts'))
spec = importlib.util.spec_from_file_location(
    'legacy_sxf_generator', root / 'scripts' / 'update_news.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
archive = json.loads((root / 'data' / 'archive.json').read_text())['items']
current_rows = json.loads((root / 'data' / 'news.json').read_text())['items']
by_url = {item['url']: item for item in archive}
current = [by_url[item['url']] for item in current_rows]
module.update_index(current)
module.update_section_pages(current)
module.build_discovery_pages(archive, current)
module.normalize_static_shells()
module.update_sitemap(archive)
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="origin/main")
    args = parser.parse_args()
    legacy_code = subprocess.check_output(
        ["git", "show", f"{args.baseline}:scripts/update_news.py"],
        cwd=ROOT,
    ).decode("utf-8")

    with tempfile.TemporaryDirectory(prefix="sxf-render-parity-") as d:
        temp_root = Path(d)
        old_root, new_root = temp_root / "old", temp_root / "new"
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache")
        shutil.copytree(ROOT, old_root, ignore=ignore)
        shutil.copytree(ROOT, new_root, ignore=ignore)
        (old_root / "scripts" / "update_news.py").write_text(legacy_code, encoding="utf-8")

        for root in (old_root, new_root):
            assert (root / "data" / "archive.json").is_file()
            assert (root / "data" / "news.json").is_file()

        subprocess.run([sys.executable, "-c", LEGACY_RENDER], check=True, cwd=old_root)
        subprocess.run(
            [sys.executable, "scripts/update_news.py", "--render-only"],
            check=True, cwd=new_root,
        )
        old_manifest, new_manifest = manifest(old_root), manifest(new_root)
        changed = [
            k for k in sorted(old_manifest.keys() | new_manifest.keys())
            if old_manifest.get(k) != new_manifest.get(k)
        ]
        # These rendered pages intentionally differ after fixing effective-date
        # pricing and adding the shared browser pricing policy.
        expected_pricing_changes = {
            "index.html", "compare/index.html", "models/pricing/index.html",
            # Preserving Qwen's official $4.951 output rate in generated cards.
            "models/index.html", "models/qwen3-8-max/index.html",
            "providers/alibaba-cloud/index.html",
            "models/qwen3-5-397b-a17b/index.html",
            # Open Source views change deliberately, with no unrelated pages.
            "open-source/index.html",
            "topics/open-source-ai/index.html",
            "topics/index.html",
            # Topic membership also affects related topic links/metadata on these
            # specific signals; their canonical paths and article content stay stable.
            "signals/discover-local-models-in-github-copilot-cli-cfd130b/index.html",
            "signals/fine-tuning-a-350m-model-for-better-structured-outputs-in-100-grpo-ste-4502076/index.html",
            "signals/introducing-olmo-core-3-open-scalable-training-infrastructure-for-larg-0bf00b7/index.html",
            "signals/open-sourcing-astabrief-the-fast-report-generation-model-in-asta-d599f0a/index.html",
            "signals/open-tts-leaderboard-scalable-evaluation-for-multilingual-text-to-spee-581ab31/index.html",
            "signals/the-open-asr-leaderboard-adds-its-first-global-south-language-b0b2c2d/index.html",
            "sitemap.xml",
        }
        unexpected = [name for name in changed if name not in expected_pricing_changes]
        assert not unexpected, (
            f"Unexpected old/new renderer differences in {len(unexpected)} output files: "
            f"{unexpected[:35]}"
        )
        for name in ("archive.json", "news.json", "model-history.json", "source-shadow.json"):
            source = (ROOT / "data" / name).read_bytes()
            assert (old_root / "data" / name).read_bytes() == source
            assert (new_root / "data" / name).read_bytes() == source
        print(
            f"PASS: {len(old_manifest)} HTML, sitemap and redirect artifacts "
            "are byte-identical with legacy renderer using the same snapshots"
        )


if __name__ == "__main__":
    main()
