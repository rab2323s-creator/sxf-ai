"""Offline regression for the preregistered agent pilot. No API calls."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_support_pilot as pilot


class AgentSupportPilotTests(unittest.TestCase):
    def test_fixture_is_consistent(self):
        data, policies = pilot.load()
        self.assertEqual(len(data["cases"]), 24)
        self.assertEqual(len(policies), 6)
        for case in data["cases"]:
            self.assertEqual(pilot.decide_oracle(case), case["expected_decision"])
            self.assertTrue(pilot.question(case, policies).strip())

    def test_response_is_strict(self):
        self.assertEqual(pilot.extract('{"decision":"escalate","reason":"Identity check required"}'),"escalate")
        for bad in ["{}","not JSON",'{"decision":"refund","reason":"x"}',
                    '{"decision":"escalate","reason":"x","extra":5}']:
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                pilot.extract(bad)

    def test_dry_run_marks_itself_as_non_model(self):
        with tempfile.TemporaryDirectory() as d:
            dest = pathlib.Path(d) / "result.json"
            p = subprocess.run([sys.executable, str(ROOT/"scripts"/"agent_support_pilot.py"),
                                "--mode", "dry-run", "--output", str(dest)],
                               capture_output=True,text=True,check=True)
            result = json.loads(dest.read_text())
            self.assertEqual(result["run_type"],"SYNTHETIC_FIXTURE_ONLY_NO_MODEL_RUN")
            self.assertEqual(result["attempted"],24)
            self.assertEqual(result["correct"],24)
            self.assertEqual(result["estimated_api_cost_usd"],0)
            self.assertIn("Report:",p.stdout)

if __name__ == "__main__":
    unittest.main()
