#!/usr/bin/env python3
"""Guard scheduled Standard prices and actual rendered SXF surfaces against drift."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news as generator  # noqa: E402

MODEL_ID = "gemini-3.7-flash"
CATALOG = json.loads((ROOT / "data/model-pricing.json").read_text(encoding="utf-8"))
MODEL = next(m for m in CATALOG["models"] if m["model_id"] == MODEL_ID)
EXPECTED_2026 = {"input": 0.75, "cached_input": 0.075, "output": 3.75}
EXPECTED_2027 = {"input": 1.5, "cached_input": 0.15, "output": 7.5}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def check_rate(actual, expected, label):
    check(actual is not None, f"{label}: unexpectedly missing price")
    for field, value in expected.items():
        check(actual.get(field) == value, f"{label}: {field} {actual.get(field)} != {value}")


def html_for(path):
    return (ROOT / path).read_text(encoding="utf-8")


def check_card():
    html = html_for("index.html")
    start = html.find('<h3><a href="/models/gemini-3-7-flash/">Gemini 3.7 Flash</a></h3>')
    if start == -1:
        return  # Dynamic homepage rotates models. Fixture checks generation separately.
    card = html[start:html.index("</article>", start)]
    active = generator.homepage_standard_price(MODEL_ID)
    check(active is not None, "Gemini has no current active rate")
    label = (f'{generator.catalog_price_label(active["input"])} in · '
             f'{generator.catalog_price_label(active["output"])} out / MTok')
    check(label in card, "Homepage Gemini card disagrees with active canonical Standard pricing")


def check_actual_views():
    active = generator.active_standard_price(MODEL_ID)
    check(CATALOG["currency"] == "USD", "Catalog currency drift")
    check(MODEL["pricing_basis"]["quantity"] == 1_000_000, "Gemini pricing units drift")
    check(MODEL["pricing_basis"]["meter"] == "tokens", "Gemini pricing meter drift")
    check_card()
    model_html = html_for("models/index.html")
    match = re.search(r'data-model-id="gemini-3.7-flash"([\s\S]*?)</tr>', model_html)
    check(match is not None, "Models table missing Gemini 3.7")
    check(f'data-input="{active["input"]}"' in match.group(0), "Models input rate mismatch")
    check(f'data-output="{active["output"]}"' in match.group(0), "Models output rate mismatch")
    pricing_html = html_for("models/pricing/index.html")
    row = re.search(r'data-pricing-row[^>]*data-search="gemini 3\.7 flash[\s\S]*?</tr>', pricing_html)
    check(row is not None, "Pricing page missing Gemini 3.7")
    check(f'<td class="price">{generator.catalog_price_label(active["input"])}</td>' in row.group(),
          "Pricing table input mismatch")
    check(f'<td class="price">{generator.catalog_price_label(active["output"])}</td>' in row.group(),
          "Pricing table output mismatch")
    compare_hub = html_for("compare/index.html")
    check(f'Gemini 3.7 Flash: {generator.catalog_price_label(active["input"])}/'
          f'{generator.catalog_price_label(active["output"])}' in compare_hub,
          "Compare hub card rate mismatch")
    compare_detail = html_for("compare/gemini-3-8-flash-vs-gemini-3-7-flash/index.html")
    detail_match = re.search(
        r'data-compare-model="gemini-3\.7-flash"([\s\S]*?)</article>',
        compare_detail,
    )
    check(detail_match is not None, "Compare detail Gemini 3.7 facts missing")
    check(f'<dt>Input / MTok</dt><dd>{generator.catalog_price_label(active["input"])}</dd>'
          in detail_match.group(0), "Compare detail input differs from active catalog")
    check(f'<dt>Output / MTok</dt><dd>{generator.catalog_price_label(active["output"])}</dd>'
          in detail_match.group(0), "Compare detail output differs from active catalog")
    expected_cost = (100_000 * active["input"] + 10_000 * active["output"]) / 1_000_000
    calculated_cost, rates = generator.estimate_standard_cost(MODEL_ID, 100_000, 10_000)
    check(abs(calculated_cost - expected_cost) < 1e-10, "Calculator rate differs from displayed Standard price")
    check_rate(rates, active, "Current cost calculator")


def check_fixture():
    fixture = {
        **MODEL,
        "model_id": "pricing-regression-fixture",
        "model": "Gemini Pricing Test Fixture",
        "sxf_url": "/models/pricing-regression-fixture/",
        "pricing": {"standard": [
            {"start": "2026-08-13", "end": "2026-12-31", **EXPECTED_2026},
            {"start": "2027-01-01", "end": None, **EXPECTED_2027},
        ]},
    }
    ident = fixture["model_id"]
    event = {
        "type": "model_added", "model_id": ident, "sequence": 1,
        "verified_at": "2026-10-09",
        "snapshot": {"provider": "Google", "model": fixture["model"],
                     "context_window": fixture["context_window"],
                     "pricing": fixture["pricing"]},
    }
    with patch.dict(generator.MODEL_PRICING_BY_ID, {ident: fixture}):
        for date in ("2026-08-13", "2026-10-09", "2026-12-31"):
            check_rate(generator.active_standard_price(ident, date), EXPECTED_2026, date)
        check_rate(generator.active_standard_price(ident, "2027-01-01"), EXPECTED_2027, "2027 start")
        try:
            generator.active_standard_price(ident, "2026-08-12")
        except RuntimeError as exc:
            check("No Standard pricing period" in str(exc), "Gap should report no active rate")
        else:
            raise AssertionError("Gap silently selected arbitrary pricing")

        with patch.object(generator, "load_model_history", return_value={"events": [event]}):
            for date, expected in [("2026-10-09", EXPECTED_2026), ("2026-12-31", EXPECTED_2026),
                                   ("2027-01-01", EXPECTED_2027)]:
                card = generator.homepage_change_cards(limit=1, on_date=date)
                label = (f'{generator.catalog_price_label(expected["input"])} in · '
                         f'{generator.catalog_price_label(expected["output"])} out / MTok')
                check(label in card, f"Homepage card picked wrong effective price for {date}")
            card = generator.homepage_change_cards(limit=1, on_date="2026-08-12")
            check("Pricing not published" in card, "Homepage must not fall back over a price gap")

        broken = {**fixture, "pricing": {"standard": [
            {"start": "2026-01-01", "end": "2026-12-31", **EXPECTED_2026},
            {"start": "2026-12-31", "end": None, **EXPECTED_2027},
        ]}}
        with patch.dict(generator.MODEL_PRICING_BY_ID, {ident: broken}):
            try:
                generator.active_standard_price(ident, "2026-10-09")
            except RuntimeError as exc:
                check("Overlapping" in str(exc), "Overlaps must raise an explicit error")
            else:
                raise AssertionError("Overlapping periods must fail")


def main():
    for date, expected in [("2026-10-09", EXPECTED_2026),
                           ("2026-12-31", EXPECTED_2026),
                           ("2027-01-01", EXPECTED_2027)]:
        check_rate(generator.active_standard_price(MODEL_ID, date), expected, "official Gemini " + date)
    check_fixture()
    check_actual_views()
    print("PASS: Gemini official pricing, homepage fixture, current rendered cross-page rates, and calculator costs")


if __name__ == "__main__":
    main()
