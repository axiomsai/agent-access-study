#!/usr/bin/env python3
"""Local receiver for control reads: the page script in Chrome POSTs one JSON line per product page; appended to control.jsonl."""
import datetime as dt, http.server, json, sys
from pathlib import Path
OUT = Path(sys.argv[1]) / "control.jsonl"
class H(http.server.BaseHTTPRequestHandler):
    def _h(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
    def do_OPTIONS(self):
        self.send_response(204); self._h(); self.end_headers()
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8", "replace")
        try:
            rec = json.loads(body); rec["saved_at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
            with OUT.open("a") as fh: fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as e:
            print("bad body", e, body[:200], flush=True)
        self.send_response(200); self._h(); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", 8765), H).serve_forever()
