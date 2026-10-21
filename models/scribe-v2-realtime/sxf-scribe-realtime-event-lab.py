"""SXF / AI: deterministic streaming-event consumer lab.
24 fictional sessions transported over REAL localhost HTTP as NDJSON.
Event names mirror published Scribe API; no WebSocket or ElevenLabs calls.
No audio, paid provider use, actual model latency or accuracy measurement.
Python 3 standard library. Run: python sxf-scribe-realtime-event-lab.py
"""
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from threading import Thread
import json

TOTAL = 24
def scenario(i):
    if i < 12:
        return [
            {"message_type":"session_started","session_id":str(i)},
            {"message_type":"partial_transcript","text":"I"},
            {"message_type":"partial_transcript","text":"I need"},
            {"message_type":"partial_transcript","text":"I need support"},
            {"message_type":"committed_transcript","text":"I need support"}]
    if i < 18:
        return [
            {"message_type":"session_started","session_id":str(i)},
            {"message_type":"partial_transcript","text":"Please send"},
            {"message_type":"partial_transcript","text":"Please send"},
            {"message_type":"partial_transcript","text":""},
            {"message_type":"committed_transcript","text":"Please send the report"}]
    if i < 22:
        return [
            {"message_type":"session_started","session_id":str(i)},
            {"message_type":"partial_transcript","text":"Call"},
            {"message_type":"committed_transcript","text":"Call me"},
            {"message_type":"partial_transcript","text":"tom"},
            {"message_type":"committed_transcript","text":"tomorrow"}]
    return [
        {"message_type":"session_started","session_id":str(i)},
        {"message_type":"partial_transcript","text":"Unverified interim"},
        {"message_type":"rate_limited","error":"synthetic rate limit"}]

class TraceServer(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        i=int(self.path.strip("/"))
        raw="".join(json.dumps(event)+"\n" for event in scenario(i)).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/x-ndjson")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

def reduce_events(events):
    naive=[]; stable=[]; preview=""; error=None
    for event in events:
        t=event["message_type"]; value=event.get("text","")
        if t=="partial_transcript":
            naive.append(value)
            preview=value  # always replace previous preview
        elif t=="committed_transcript":
            naive.append(value);stable.append(value);preview=""
        elif t in {"rate_limited","quota_exceeded","transcriber_error","input_error"}:
            error=t
    return {"naive":" ".join(x for x in naive if x),
            "stable":" ".join(stable),"preview":preview,"error":error}

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),TraceServer)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    stats=Counter()
    try:
        for i in range(TOTAL):
            with urlopen(f"http://127.0.0.1:{server.server_port}/{i}",timeout=3) as response:
                events=[json.loads(line) for line in response if line.strip()]
            result=reduce_events(events)
            stats["http_sessions"]+=1
            stats["events"]+=len(events)
            if result["error"]:
                stats["error_sessions"]+=1
                assert not result["stable"]
            else:
                stats["committed_sessions"]+=1
                assert result["stable"]
            if result["naive"]!=result["stable"]:
                stats["naive_incorrect_or_unverified"]+=1
            if result["stable"] and not result["error"]:
                stats["event_aware_correct"]+=1
        actual=tuple(stats[k] for k in ("http_sessions","committed_sessions","error_sessions","naive_incorrect_or_unverified","event_aware_correct"))
        assert actual==(24,22,2,24,22),actual
        print(json.dumps({"scope":"local HTTP with synthetic Scribe-shaped events; NOT a provider or WebSocket test","results":dict(stats)},indent=2))
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)

if __name__=="__main__":main()
