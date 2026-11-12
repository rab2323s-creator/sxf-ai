#!/usr/bin/env python3
"""SXF opt-in NON-STREAMING endpoint probe. Makes no API calls without explicit CLI + env key."""
import argparse, csv, json, os, statistics, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
PROMPTS=[
 "In one sentence, explain the difference between an API and an SDK.",
 'Return exactly this JSON object without extra text: {"ok":true}',
 "List three non-sensitive ways to reduce GPU idle costs."
]
COLUMNS=["timestamp_utc","endpoint_host","model","trial","status","elapsed_ms","prompt_tokens","completion_tokens","total_tokens","error_type"]
def main():
 p=argparse.ArgumentParser(description="Explicit opt-in non-streaming LLM HTTP smoke test.")
 p.add_argument("--endpoint",required=True,help="Trusted HTTPS chat completions URL")
 p.add_argument("--model",required=True)
 p.add_argument("--key-env",default="INFERENCE_TEST_KEY")
 p.add_argument("--trials",type=int,default=3)
 p.add_argument("--timeout",type=int,default=40)
 p.add_argument("--output",default="hosting-probe-results.csv")
 p.add_argument("--max-tokens",type=int,default=128)
 a=p.parse_args()
 u=urllib.parse.urlparse(a.endpoint)
 if u.scheme!="https" or not u.netloc or u.username or u.password:
  p.error("Only explicit trusted HTTPS endpoint URLs are accepted")
 if not 1<=a.trials<=30 or not 8<=a.max_tokens<=512 or not 5<=a.timeout<=120:
  p.error("trials 1..30, max-tokens 8..512, timeout 5..120")
 key=os.getenv(a.key_env,"")
 if not key:p.error("No API key found in the specified environment variable; no requests sent")
 if len(a.model)>300:p.error("Model ID too long")
 rows=[]
 for trial in range(a.trials):
  body=json.dumps({"model":a.model,"messages":[{"role":"user","content":PROMPTS[trial%len(PROMPTS)]}],"temperature":0,"max_tokens":a.max_tokens,"stream":False}).encode("utf-8")
  req=urllib.request.Request(a.endpoint,data=body,method="POST",headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":"SXF-Hosting-Protocol/1"})
  started=time.monotonic()
  try:
   with urllib.request.urlopen(req,timeout=a.timeout) as res:
    status=res.status; data=json.loads(res.read(2*1024*1024))
   usage=data.get("usage",{}) if isinstance(data,dict) else {}
   row=[datetime.now(timezone.utc).isoformat(),u.hostname,a.model,trial+1,status,round((time.monotonic()-started)*1000,2),usage.get("prompt_tokens"),usage.get("completion_tokens"),usage.get("total_tokens"),""]
  except (urllib.error.HTTPError,urllib.error.URLError,ValueError,TimeoutError) as exc:
   row=[datetime.now(timezone.utc).isoformat(),u.hostname,a.model,trial+1,getattr(exc,"code","ERROR"),round((time.monotonic()-started)*1000,2),"","","",type(exc).__name__]
  rows.append(row);print("trial",trial+1,"HTTP",row[4],"elapsed_ms",row[5])
 with open(a.output,"w",newline="",encoding="utf-8") as f:
  wr=csv.writer(f);wr.writerow(COLUMNS);wr.writerows(rows)
 latencies=[row[5] for row in rows if row[4]==200]
 if latencies:print("Observed successful-response p50 end-to-end ms:",round(statistics.median(latencies),2))
 print("Saved",len(rows),"rows. No raw prompts or credentials recorded. Not a TTFT or provider-comparison benchmark.")
if __name__=="__main__":main()
