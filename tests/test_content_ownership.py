#!/usr/bin/env python3
"""Regression tests for site-wide editorial HTML ownership."""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from content_ownership import (is_authored_html, preserve_authored_pages,
                               assert_authored_pages_clean)


def write(root: Path, path: str, text: str) -> Path:
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def main() -> None:
    protected = (
        "superintelligence/index.html", "research/ai-agent-reliability/index.html",
        "guides/ai-agent-evaluation-checklist/index.html",
        "guides/best-ai-agents/index.html", "about/index.html",
        "tools/my-authored-guide/index.html",
    )
    generated = (
        "signals/latest/index.html", "topics/ai-agents/index.html",
        "models/some-new-model/index.html", "research/index.html", "guides/index.html",
        "index.html", "tools/index.html",
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path in protected + generated:
            write(root, path, "old content")
        assert all(is_authored_html(Path(p)) for p in protected)
        assert all(not is_authored_html(Path(p)) for p in generated)
        assert not is_authored_html(Path("styles.css"))
        with preserve_authored_pages(root):
            for path in protected + generated:
                write(root, path, "builder changed it")
            write(root, "guides/new-guide/index.html", "brand new guide")
        assert all((root / p).read_text() == "old content" for p in protected)
        assert all((root / p).read_text() == "builder changed it" for p in generated)
        assert (root / "guides/new-guide/index.html").read_text() == "brand new guide"
        try:
            with preserve_authored_pages(root):
                write(root, protected[0], "bad state")
                raise LookupError("simulate generator failure")
        except LookupError:
            pass
        assert (root / protected[0]).read_text() == "old content"

        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        write(root, generated[0], "new feed")
        assert_authored_pages_clean(root)
        write(root, protected[1], "regressed SEO")
        try:
            assert_authored_pages_clean(root)
        except RuntimeError as exc:
            assert "research/ai-agent-reliability/index.html" in str(exc)
        else:
            raise AssertionError("Drift should block a bot commit")
    print("PASS: authored pages survive automated regeneration and pre-commit drift is blocked")


if __name__ == "__main__":
    main()
