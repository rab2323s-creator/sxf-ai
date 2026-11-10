#!/usr/bin/env python3
"""Keep authored HTML stable while automated feed/catalog pages are rebuilt.

Editorial HTML already in the checkout is authoritative. The news builder may
create new editorial routes but cannot rewrite existing authored content.
Routes explicitly owned by live generators remain mutable.
"""
from __future__ import annotations

import argparse
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Feed/catalog/navigation surfaces intentionally regenerated from data.
GENERATED_ROUTE_ROOTS = frozenset({
    "signals", "topics", "models", "providers", "evaluations", "compare", "brief",
})
GENERATED_ENTRYPOINTS = frozenset({
    "index.html", "guides/index.html", "research/index.html",
    "open-source/index.html", "tools/index.html",
})


def is_authored_html(relative_path: Path) -> bool:
    """Default to editorial ownership; explicit generated routes opt out."""
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Expected a repository-relative route: {relative_path}")
    if relative_path.suffix.lower() != ".html" or not relative_path.parts:
        return False
    if any(part.startswith(".") for part in relative_path.parts):
        return False
    return (relative_path.parts[0] not in GENERATED_ROUTE_ROOTS
            and relative_path.as_posix() not in GENERATED_ENTRYPOINTS)


def authored_snapshots(root: Path) -> dict[Path, bytes]:
    """Snapshot existing editorial pages, never newly generated routes."""
    root = Path(root).resolve()
    return {
        path: path.read_bytes()
        for path in root.rglob("*.html")
        if path.is_file() and not path.is_symlink()
        and is_authored_html(path.relative_to(root))
    }


@contextmanager
def preserve_authored_pages(root: Path) -> Iterator[None]:
    """Restore authored pages even if a generator or post-processor raises."""
    before = authored_snapshots(root)
    try:
        yield
    finally:
        for path, original in before.items():
            if not path.is_file() or path.read_bytes() != original:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)


def assert_authored_pages_clean(root: Path) -> None:
    """Fail before bot commit if *any* later step changed tracked authored HTML."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    changed = [p for p in result.stdout.splitlines() if is_authored_html(Path(p))]
    if changed:
        raise RuntimeError(
            "Automated build modified editorial HTML; refusing to publish: "
            + ", ".join(changed[:25])
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assert-clean", action="store_true")
    args = parser.parse_args()
    if args.assert_clean:
        assert_authored_pages_clean(Path(__file__).resolve().parents[1])
        print("PASS: no authored editorial HTML changed by automated build")
    else:
        parser.error("Use --assert-clean (the builder calls preserve_authored_pages directly)")


if __name__ == "__main__":
    main()
