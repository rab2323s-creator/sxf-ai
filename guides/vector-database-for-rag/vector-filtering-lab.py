"""SXF / AI — original synthetic filtered retrieval experiment.
Runs with Python 3 standard library only.
This demonstrates candidate filtering, NOT database speed or vendor ranking.
"""
import math
import json

K=5
docs=[]
for tenant,n in (("red",120),("blue",120)):
    for i in range(n):
        angle=(-0.06+i*0.001) if tenant=="red" else (0.25+i*0.001)
        docs.append((tenant+"-"+str(i).zfill(3),tenant,(math.cos(angle),math.sin(angle))))

def similarity(a,b):
    return sum(x*y for x,y in zip(a,b))

def search(query,records):
    return [r[0] for r in sorted(records,key=lambda r:(-similarity(query,r[2]),r[0]))[:K]]

def test():
    outcomes={}
    for tenant in ("red","blue"):
        vals=[]
        for j in range(20):
            a=(j-9.5)*0.001
            query=(math.cos(a),math.sin(a))
            eligible=[d for d in docs if d[1]==tenant]
            expected=search(query,eligible)
            before=search(query,eligible)
            after=[key for key in search(query,docs) if key.startswith(tenant+"-")]
            vals.append((
                len(set(before)&set(expected))/K,
                len(set(after)&set(expected))/K,
                len(after)
            ))
        outcomes[tenant]={
            "queries":20,
            "prefilter_recall_at_5":round(sum(v[0] for v in vals)/20,3),
            "postfilter_recall_at_5":round(sum(v[1] for v in vals)/20,3),
            "mean_postfilter_count":round(sum(v[2] for v in vals)/20,3)
        }
    assert outcomes["red"]=={"queries":20,"prefilter_recall_at_5":1.0,"postfilter_recall_at_5":1.0,"mean_postfilter_count":5.0}
    assert outcomes["blue"]=={"queries":20,"prefilter_recall_at_5":1.0,"postfilter_recall_at_5":0.0,"mean_postfilter_count":0.0}
    print(json.dumps({"records":len(docs),"total_queries":40,"k":K,"outcomes":outcomes},indent=2))

if __name__=="__main__":
    test()
