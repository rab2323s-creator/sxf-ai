"""SXF / AI: reproducible ML release-manifest evidence gap audit.
The 12 release scenarios are synthetic, not real vendor audits or legal decisions.
Python 3 standard library only; no network or third-party libraries.
Run: python sxf-license-evidence-lab.py
"""
import json

SCENARIOS = [
    # id, license, deployment, origin, sha, full license, model card, policy,
    # packaged license, notice, custom-terms-reviewed, modified
    ("A01", "MIT", "internal", True, True, True, True, False, False, False, False, False),
    ("A02", "Apache-2.0", "saas", True, True, True, True, False, False, False, False, False),
    ("A03", "MIT", "redistribute", True, True, True, True, False, True, True, False, False),
    ("A04", "Apache-2.0", "redistribute", True, True, True, True, False, True, True, False, True),
    ("A05", "MIT", "redistribute", True, True, True, True, False, False, False, False, False),
    ("A06", "Apache-2.0", "redistribute", True, True, True, True, False, True, False, False, True),
    ("A07", "custom", "saas", True, True, True, True, False, False, False, False, False),
    ("A08", "custom", "saas", True, True, True, True, True, False, False, True, False),
    ("A09", "custom", "redistribute", True, True, True, True, True, True, True, True, False),
    ("A10", "MIT", "internal", True, False, True, True, False, False, False, False, False),
    ("A11", "Apache-2.0", "saas", True, True, False, True, False, False, False, False, False),
    ("A12", "custom", "internal", True, True, True, True, True, False, False, False, False),
]

def inspect(row):
    (ident, license_id, deployment, origin, sha, license_text, card,
     policy, packaged, notice, counsel, modified) = row
    gaps = []
    if not origin: gaps.append("origin URL missing")
    if not sha: gaps.append("weight revision/hash missing")
    if not license_text: gaps.append("complete governing license missing")
    if not card: gaps.append("model card missing")
    if license_id == "custom":
        if not policy: gaps.append("incorporated use policy unavailable")
        if not counsel: gaps.append("custom terms not reviewed")
    if deployment == "redistribute":
        if not packaged: gaps.append("redistribution license copy missing")
        if not notice: gaps.append("notice/attribution evidence missing")
        if license_id == "Apache-2.0" and modified and not notice:
            gaps.append("modification notice not documented")
    return {"fixture_id":ident,"license_label":license_id,"deployment":deployment,
            "evidence_ready_for_human_review":not gaps,"evidence_gaps":gaps}

def main():
    results = [inspect(r) for r in SCENARIOS]
    label_only = sum(bool(r[1]) for r in SCENARIOS)
    ready = sum(r["evidence_ready_for_human_review"] for r in results)
    assert (len(results),label_only,ready) == (12,12,6)
    assert all(r["evidence_gaps"] for r in results if not r["evidence_ready_for_human_review"])
    print(json.dumps({"method":"synthetic release-manifest evidence audit",
                      "fixtures":len(results),"license_labels_present":label_only,
                      "evidence_ready_for_human_review":ready,
                      "unresolved_evidence_packets":len(results)-ready,
                      "not_a_legal_clearance":True,"results":results},indent=2))

if __name__ == "__main__":
    main()
