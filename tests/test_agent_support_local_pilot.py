"""Offline unit tests for the free local inference evaluator; no model download."""
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_support_local_pilot as pilot


class LocalSupportPilotTests(unittest.TestCase):
    def test_refuses_remote_paid_or_untrusted_urls(self):
        self.assertEqual(pilot.check_local_url("http://127.0.0.1:8087"),"http://127.0.0.1:8087")
        for url in ["https://api.openai.com", "http://remote.example/v1", "http://127.0.0.2:8087"]:
            with self.assertRaises(ValueError):
                pilot.check_local_url(url)

    def test_mocked_model_api_is_measured_not_confused_with_dry_run(self):
        data, _ = pilot.load()
        answers = iter([c["expected_decision"] for c in data["cases"]])
        def fake_call(*args):
            return json.dumps({"decision": next(answers), "reason": "Policy rule"}), {
                "prompt_tokens": 42, "completion_tokens": 9
            }
        with mock.patch.object(pilot, "request_local", side_effect=fake_call):
            result = pilot.evaluate("http://127.0.0.1:8087", "mock", repeats=1)
        self.assertEqual(result["overall"]["correct"],24)
        self.assertEqual(result["overall"]["attempts"],24)
        self.assertEqual(result["overall"]["prompt_tokens"],24*42)
        self.assertEqual(result["overall"]["provider_api_fees_usd"],0)
        self.assertTrue(result["not_a_production_agent_benchmark"])
        self.assertNotIn("SYNTHETIC_FIXTURE_ONLY_NO_MODEL_RUN",result["evidence_type"])

    def test_errors_count_as_failures(self):
        with mock.patch.object(pilot,"request_local",side_effect=ValueError("model unavailable")):
            result = pilot.evaluate("http://localhost:8087","mock", repeats=1)
        self.assertEqual(result["overall"]["correct"],0)
        self.assertEqual(result["overall"]["invalid_or_request_failures"],24)
        self.assertEqual(result["overall"]["attempts"],24)


if __name__ == "__main__":
    unittest.main()
