#!/usr/bin/env python3
"""Guard the feed generator against accidental multiple entrypoints."""
from __future__ import annotations

import ast
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_news.py"


def main() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SCRIPT))
    guards = [
        (index, node)
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    ]
    assert len(guards) == 1, (
        f"Expected one __main__ guard, found {len(guards)} in {SCRIPT}"
    )
    index, guard = guards[0]
    assert index == len(tree.body) - 1, (
        "__main__ entrypoint must be the last top-level statement"
    )
    assert len(guard.body) == 1, "Entrypoint must contain one statement"
    call = guard.body[0]
    assert (
        isinstance(call, ast.Expr)
        and isinstance(call.value, ast.Call)
        and isinstance(call.value.func, ast.Name)
        and call.value.func.id == "main"
        and not call.value.args
        and not call.value.keywords
    ), "Entrypoint must call main() exactly once"
    print("PASS: one final main() entrypoint")


if __name__ == "__main__":
    main()
