"""SXF Agent Opportunity Atlas: executable deterministic workflow fault-injection.
No LLM calls, providers or real company outcomes. Python 3 stdlib.
Run: python sxf-agent-workflow-lab.py
"""
import json
from collections import Counter

def run(policy, jobs=120):
    actions=set()
    metrics=Counter()
    for i in range(jobs):
        key=f"job-{i}"
        approved=i % 12 != 0
        fault=i % 5 == 0
        replay=fault
        valid=i % 7 != 0
        attempts=2 if replay else 1
        for attempt in range(attempts):
            metrics["attempts"]+=1
            if not valid:
                metrics["invalid_input_attempts"]+=1
                if policy!="naive": continue
            if not approved:
                metrics["approval_block_attempts"]+=1
                if policy!="naive":continue
            if fault and attempt==0:
                # Response lost AFTER side-effect: retry can duplicate it.
                metrics["lost_reply_attempts"]+=1
            if key in actions:
                metrics["duplicates_attempted"]+=1
                if policy=="guarded":continue
                metrics["duplicate_actions"]+=1
            else: actions.add(key)
            metrics["side_effect_calls"]+=1
    metrics["unique_actions"]=len(actions)
    return dict(metrics)

def main():
    naive=run("naive")
    guarded=run("guarded")
    assert naive["duplicate_actions"]>0
    assert guarded["duplicate_actions"]==0
    assert guarded["side_effect_calls"]<=naive["side_effect_calls"]
    assert guarded["unique_actions"]<=naive["unique_actions"]
    output={"study":"Synthetic fault injection; not an LLM benchmark",
            "scenarios":120,"naive":naive,"guarded":guarded,
            "caveat":"Deterministic rules, simulated response loss; no real model or company"}
    print(json.dumps(output,indent=2))
if __name__=="__main__":main()
