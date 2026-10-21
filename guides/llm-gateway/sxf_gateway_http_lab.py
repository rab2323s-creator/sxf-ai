"""SXF / AI original loopback HTTP gateway experiment.
80 tasks across three fault-policy scenarios. Standard library only.
Run: python sxf_gateway_http_lab.py
No real LLMs, vendors, provider pricing or production infrastructure.
"""
from __future__ import annotations
import json, threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request, error

TOTAL = 80
COST = {"primary": 0.002, "backup": 0.003}

class MockBackend(BaseHTTPRequestHandler):
    attempts = Counter()
    def log_message(self, *args):
        pass
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        policy, task, provider = data["policy"], data["task"], data["provider"]
        key = (policy, task, provider)
        self.attempts[key] += 1
        count = self.attempts[key]
        if provider == "primary":
            if task < 50 or (50 <= task < 60 and count > 1):
                status, payload = 200, {"kind": "chat_completion", "message": "accepted"}
            elif task < 60 or task >= 70:
                status, payload = 429, {"error": "injected_rate_limit"}
            else:
                status, payload = 500, {"error": "injected_server_error"}
        elif task >= 75:
            status, payload = 200, {"kind": "invalid_schema", "message": "not accepted"}
        else:
            status, payload = 200, {"kind": "chat_completion", "message": "accepted"}
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        if status == 429: self.send_header("Retry-After", "0")
        self.end_headers()
        self.wfile.write(raw)

def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), MockBackend)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = "http://127.0.0.1:%s/mock" % server.server_port
    def invoke(policy, task, provider):
        data = json.dumps({"policy": policy, "task": task, "provider": provider}).encode()
        req = request.Request(endpoint, data, {"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read())
        except error.HTTPError as exc:
            return exc.code, json.loads(exc.read())
    def accepted(status, body):
        return status == 200 and body.get("kind") == "chat_completion" and body.get("message") == "accepted"
    results = []
    try:
        for policy in ("no_retry", "retry_once", "retry_then_fallback"):
            calls, ok, schema_rejections = Counter(), 0, 0
            for task in range(TOTAL):
                status, body = invoke(policy, task, "primary")
                calls["primary"] += 1
                if status in (429, 500) and policy != "no_retry":
                    status, body = invoke(policy, task, "primary")
                    calls["primary"] += 1
                if status in (429, 500) and policy == "retry_then_fallback":
                    status, body = invoke(policy, task, "backup")
                    calls["backup"] += 1
                if accepted(status, body): ok += 1
                elif status == 200: schema_rejections += 1
            total = sum(calls[p] * COST[p] for p in COST)
            results.append({"policy":policy,"tasks":TOTAL,"valid_completions":ok,
                            "success_pct":round(100 * ok / TOTAL,2),
                            "primary_http_calls":calls["primary"],"backup_http_calls":calls["backup"],
                            "schema_rejections":schema_rejections,
                            "modeled_total_usd":round(total,3),
                            "modeled_cost_per_valid_usd":round(total / ok,6)})
        expected = [(50,80,0,0),(60,110,0,0),(75,110,20,5)]
        actual = [(r["valid_completions"],r["primary_http_calls"],r["backup_http_calls"],r["schema_rejections"]) for r in results]
        assert actual == expected, (actual,expected)
        print(json.dumps({"scope":"actual loopback HTTP, synthetic provider behavior; no LLM models",
                          "assumed_cost_usd_per_http_call":COST,"results":results},indent=2))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

if __name__ == "__main__":
    main()
