#!/usr/bin/env python3
"""Reject automated model-page regressions without freezing prices or specifications.

Before a build, remember existing editorial SEO, sections, substantial authored
prose, FAQ questions, linked calculators and model-page assets. Compare after
the build. Numeric price/context/spec changes and new content remain allowed;
deletion or generic-template fallback fails closed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Iterator
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MODEL_FILE = re.compile(r"^models/[^/]+/index\.html$")
SCHEMA_TYPES = frozenset({"FAQPage", "TechArticle", "Article"})
VOID_TAGS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})
VOLATILE = re.compile(
    r"(?:model-history|what-changed|change-watch|model-evaluations|"
    r"model-comparisons|signal-(?:card|row|list)|news-(?:card|row|list)|"
    r"related-signals|live-feed|latest-(?:news|signal|update))", re.I
)
VARIABLE_NUMBER = re.compile(
    r"(?<![A-Za-z])(?:[$€£]\s*)?-?\d[\d,.]*(?:\s?(?:%|[KMBT]|ms|s|hours?|minutes?|tokens?|MTok|/\w+))?", re.I
)
SPACES = re.compile(r"\s+")


def normalized(text: str) -> str:
    text = SPACES.sub(" ", unescape(text)).strip().casefold()
    return VARIABLE_NUMBER.sub("{number}", text)


def is_model_page(path: Path) -> bool:
    return bool(MODEL_FILE.fullmatch(path.as_posix()))


def schema_entries(data: object) -> Iterator[dict]:
    if isinstance(data, list):
        for item in data:
            yield from schema_entries(item)
    elif isinstance(data, dict):
        if isinstance(data.get("@graph"), list):
            yield from schema_entries(data["@graph"])
        else:
            yield data


class ModelHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool, bool]] = []
        self.data_capture: list[tuple[str, bool, list[str]]] = []
        self.contract: dict = {
            "title": "", "description": "", "canonical": "",
            "og_image": "", "robots": "", "h1": [], "sections": [],
            "headings": [], "prose": [], "faq": [], "sources": [],
            "assets": [], "editorial_markers": [], "schema_types": [],
            "schema_faq": [], "tables": 0, "controls": 0,
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        parent_volatile = any(entry[1] for entry in self.stack)
        local_volatile = bool(VOLATILE.search(" ".join(
            (a.get("class") or "", a.get("id") or "",
             " ".join(k for k in a if k.startswith("data-")))
        )))
        volatile = parent_volatile or local_volatile
        in_main = tag == "main" or any(entry[2] for entry in self.stack)
        editorial_start = (tag in {"section", "article"} and bool(a.get("id"))) or any(
            k.endswith(("-guide", "-lab", "-dossier", "-planner"))
            for k in a if k.startswith("data-")
        )
        editorial = (not volatile and editorial_start) or any(entry[3] for entry in self.stack)
        if tag not in VOID_TAGS:
            self.stack.append((tag, volatile, in_main, editorial))

        if tag == "meta":
            if (a.get("name") or "").lower() == "description":
                self.contract["description"] = normalized(a.get("content") or "")
            if (a.get("name") or "").lower() == "robots":
                self.contract["robots"] = a.get("content") or ""
            if (a.get("property") or "").lower() == "og:image":
                self.contract["og_image"] = a.get("content") or ""
        if tag == "link":
            if (a.get("rel") or "").lower() == "canonical":
                self.contract["canonical"] = a.get("href") or ""
            if (a.get("rel") or "").lower() == "stylesheet" and a.get("href"):
                self.contract["assets"].append(urlsplit(a["href"]).path)
        if tag == "script" and a.get("src"):
            self.contract["assets"].append(urlsplit(a["src"]).path)
        if tag == "section" and in_main and not volatile and a.get("id"):
            self.contract["sections"].append(a["id"])

        if in_main and not volatile:
            if tag == "table" and editorial:
                self.contract["tables"] += 1
            if tag in {"input", "select", "textarea", "button"} and editorial:
                self.contract["controls"] += 1
            for name in a:
                if name.startswith("data-") and (
                    name.endswith(("-guide", "-lab", "-calculator", "-explorer", "-planner", "-dossier"))
                    or name.startswith("data-sxf-")
                ):
                    self.contract["editorial_markers"].append(name)
            if tag == "a" and editorial and (a.get("href") or "").startswith("/"):
                self.contract["sources"].append(urlsplit(a["href"]).path)

        if tag in {"title", "h1", "h2", "p", "summary", "script"}:
            capture = tag != "script" or a.get("type") == "application/ld+json"
            if capture:
                relevant = in_main and (editorial if tag in {"p", "h2"} else True)
                self.data_capture.append((
                    tag,
                    (volatile or not relevant) if tag not in {"title", "script"} else False,
                    [],
                ))

    def handle_data(self, text: str) -> None:
        for _tag, _skip, chunks in self.data_capture:
            chunks.append(text)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.data_capture) - 1, -1, -1):
            if self.data_capture[i][0] != tag:
                continue
            name, skip, chunks = self.data_capture.pop(i)
            content = " ".join(chunks).strip()
            if name == "title":
                self.contract["title"] = normalized(content)
            elif name == "script" and content:
                try:
                    for entry in schema_entries(json.loads(content)):
                        kinds = entry.get("@type")
                        kinds = kinds if isinstance(kinds, list) else [kinds]
                        self.contract["schema_types"].extend(
                            kind for kind in kinds if kind in SCHEMA_TYPES
                        )
                        if "FAQPage" in kinds:
                            for item in entry.get("mainEntity", []):
                                if isinstance(item, dict) and item.get("name"):
                                    self.contract["schema_faq"].append(
                                        normalized(str(item["name"]))
                                    )
                except (ValueError, TypeError):
                    pass
            elif not skip:
                if name == "h1" and content:
                    self.contract["h1"].append(normalized(content))
                elif name == "h2" and content:
                    self.contract["headings"].append(normalized(content))
                elif name == "summary" and content:
                    self.contract["faq"].append(normalized(content))
                elif name == "p" and len(SPACES.sub(" ", unescape(content)).strip()) >= 85:
                    self.contract["prose"].append(normalized(content))
            break
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def fingerprint(source: str) -> dict:
    parser = ModelHTML()
    parser.feed(source)
    parser.close()
    return parser.contract


def snapshot(root: Path) -> dict[str, dict]:
    root = root.resolve()
    return {
        path.relative_to(root).as_posix(): fingerprint(path.read_text(encoding="utf-8"))
        for path in sorted((root / "models").glob("*/index.html"))
        if path.is_file() and is_model_page(path.relative_to(root))
        and path.parent.name != "pricing"
    }


def regressions(before: dict, after: dict) -> list[str]:
    bad = []
    for singular in ("title", "description", "canonical", "og_image"):
        old = before.get(singular)
        if old and old != after.get(singular):
            bad.append(singular)
    if "index" in (before.get("robots") or "").split(",") and "noindex" in (after.get("robots") or "").split(","):
        bad.append("robots: unexpectedly changed to noindex")
    for key in ("tables", "controls"):
        if after.get(key, 0) < before.get(key, 0):
            bad.append(f"{key}: lost {before[key] - after.get(key, 0)}")
    for key in (
        "h1", "sections", "headings", "prose", "faq", "schema_faq",
        "schema_types", "assets", "editorial_markers", "sources"
    ):
        missing = Counter(before.get(key, [])) - Counter(after.get(key, []))
        if missing:
            first = next(iter(missing))
            bad.append(f"{key}: missing {sum(missing.values())} (example: {str(first)[:100]})")
    return bad


def verify(root: Path, baseline: dict[str, dict]) -> None:
    root = root.resolve()
    failures = []
    for path, prior in baseline.items():
        rel = Path(path)
        if not is_model_page(rel):
            raise ValueError(f"Invalid model page in snapshot: {path}")
        target = root / rel
        if not target.is_file():
            failures.append(f"{path}: page disappeared")
            continue
        differences = regressions(
            prior, fingerprint(target.read_text(encoding="utf-8"))
        )
        failures.extend(f"{path}: {item}" for item in differences)
    if failures:
        raise RuntimeError(
            "Model editorial regression detected; refusing to publish:\n"
            + "\n".join(failures[:30])
        )


@contextmanager
def protect_model_pages(root: Path) -> Iterator[None]:
    root = root.resolve()
    originals = {
        path: path.read_bytes()
        for path in sorted((root / "models").glob("*/index.html"))
        if path.is_file() and is_model_page(path.relative_to(root))
        and path.parent.name != "pricing"
    }
    baseline = {
        path.relative_to(root).as_posix(): fingerprint(raw.decode("utf-8"))
        for path, raw in originals.items()
    }
    try:
        yield
        verify(root, baseline)
    except BaseException:
        # A failed local regeneration must never leave erased model pages behind.
        for path, raw in originals.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != raw:
                path.write_bytes(raw)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("snapshot", "verify"))
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.mode == "snapshot":
        args.file.parent.mkdir(parents=True, exist_ok=True)
        data = snapshot(args.root)
        if not data:
            raise RuntimeError("No model pages found; refusing empty protection baseline")
        args.file.write_text(
            json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        print(f"PASS: captured {len(data)} model editorial baselines")
    else:
        data = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise ValueError("Missing model baseline")
        verify(args.root, data)
        print(f"PASS: {len(data)} model pages retained editorial content and metadata")


if __name__ == "__main__":
    main()
