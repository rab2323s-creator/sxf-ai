#!/usr/bin/env python3
"""Offline pricing audit regression tests; no external network required."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pricing_source_audit import compare_catalog, active_price, money


def model(model_id="sample-model", provider="OpenAI", rate_in="2", rate_out="10"):
    return {
        "provider": provider, "model_id": model_id, "model": model_id,
        "pricing_status": "official-paid",
        "pricing_basis": {"meter": "tokens"},
        "pricing": {"standard": [{"start": "2026-01-01", "end": None,
                                   "input": float(rate_in), "output": float(rate_out)}]},
        "provenance": {"verified_at": "2026-09-27", "evidence": {
            "pricing": "https://example.com/provider-pricing"}},
    }


class PricingAuditTests(unittest.TestCase):
    def test_matching_router_price_never_replaces_official(self):
        data = {"models": [model()], "source_verified": "2026-10-09"}
        router = {"data": [{"id": "openai/sample-model",
                            "pricing": {"prompt": "0.000002",
                                        "completion": "0.000010"}}]}
        result = compare_catalog(data, router, None, "2026-10-09")
        item = result["models"][0]
        self.assertEqual(item["audit_status"], "cross_checked_third_party")
        self.assertEqual(item["official_usd_per_million_tokens"],
                         {"input": "2.0", "output": "10.0"})
        self.assertEqual(item["observations"][0]["comparison"], "matches")

    def test_detects_difference_without_modifying_official(self):
        data = {"models": [model()]}
        router = {"data": [{"id": "openai/sample-model",
                            "pricing": {"prompt": "0.000003",
                                        "completion": "0.000010"}}]}
        item = compare_catalog(data, router, None, "2026-10-09")["models"][0]
        self.assertEqual(item["audit_status"], "review_difference")
        self.assertEqual(item["official_usd_per_million_tokens"]["input"], "2.0")

    def test_litellm_exact_vendor(self):
        data = {"models": [model()]}
        lite = {"sample-model": {"litellm_provider": "anthropic",
                                 "input_cost_per_token": 0.000002,
                                 "output_cost_per_token": 0.00001}}
        item = compare_catalog(data, None, lite, "2026-10-09")["models"][0]
        self.assertEqual(item["audit_status"], "not_found_in_third_party_feeds")

    def test_no_guesses_for_unpublished_or_tiered_prices(self):
        m = model()
        m["pricing_status"] = "not-published"
        self.assertIsNone(active_price(m, "2026-10-09"))
        m["pricing_status"] = "official-paid"
        m["pricing"]["tiered"] = {"basis": "something"}
        self.assertIsNone(active_price(m, "2026-10-09"))

    def test_invalid_amounts_rejected(self):
        self.assertIsNone(money("-1"))
        self.assertIsNone(money("NaN"))
        self.assertIsNone(money("Infinity"))

    def test_price_effective_dates(self):
        self.assertIsNone(active_price(model(), "2025-12-31"))


if __name__ == "__main__":
    unittest.main()
