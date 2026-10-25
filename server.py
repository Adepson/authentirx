"""AuthentiRx MVP API (stdlib only, no dependencies).
Endpoints:
  /api/check?name=<medicine>  -> RxNorm resolve + openFDA recalls/label + NAFDAC alerts
  /                           -> mobile-first single page UI
"""
import json, urllib.parse, html
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rxnorm import client as rx
from openfda import client as fda
from alerts import lookup as naf
from openfda import label as flabel
from openfda import interactions as finter
from openfda import faers

ALIASES = {"paracetamol": "acetaminophen", "salbutamol": "albuterol",
           "glibenclamide": "glyburide", "adrenaline": "epinephrine"}


def check(name: str) -> dict:
    out = {"typed": name, "disclaimer": "Informational only. Not medical advice. Always confirm with a pharmacist."}
    r = rx.resolve_drug(name)
    if not r:
        out["error"] = "We could not match that medicine name. Try the name printed on the pack."
        return out
    out["drug"] = r
    out["nafdac_alerts"] = naf.lookup(r["rxcui"] if False else name)[:5] or naf.lookup(r["name"])[:5]
    generic = r["name"].lower()
    generic = ALIASES.get(name.lower(), generic)
    out["fda_recalls"] = fda.recalls(generic)[:3]
    out["fda_label"] = fda.label_warnings(generic)
    return out


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/check"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = (q.get("name") or [""])[0].strip()
            if not name:
                return self._send(400, json.dumps({"error": "missing name"}).encode())
            try:
                self._send(200, json.dumps(check(name)).encode())
            except Exception as e:
                self._send(502, json.dumps({"error": f"upstream error: {e}"}).encode())
        elif self.path.startswith("/api/label"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = (q.get("name") or [""])[0].strip()
            rxcui = (q.get("rxcui") or [""])[0].strip()
            if not name and not rxcui:
                return self._send(400, json.dumps({"error": "missing name or rxcui"}).encode())
            try:
                res = flabel.label_by_rxcui(rxcui) if rxcui else flabel.label_by_name(name)
                res.pop("_full_sections", None)
                self._send(200, json.dumps(res).encode())
            except Exception as e:
                self._send(502, json.dumps({"error": f"upstream error: {e}"}).encode())
        elif self.path.startswith("/api/events"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = (q.get("name") or [""])[0].strip()
            if not name:
                return self._send(400, json.dumps({"error": "missing name"}).encode())
            try:
                self._send(200, json.dumps(faers.events_by_name(name)).encode())
            except Exception as e:
                self._send(502, json.dumps({"error": f"upstream error: {e}"}).encode())
        elif self.path.startswith("/api/interactions"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            names = [n for part in q.get("names", []) for n in part.split(",") if n.strip()]
            if len(names) > 6:
                return self._send(400, json.dumps({"error": "enter at most 6 medicines"}).encode())
            try:
                self._send(200, json.dumps(finter.check_pairs(names)).encode())
            except Exception as e:
                self._send(502, json.dumps({"error": f"upstream error: {e}"}).encode())
        elif self.path.startswith("/logo.svg"):
            try:
                self._send(200, pathlib.Path("logo.svg").read_bytes(), "image/svg+xml")
            except Exception:
                self._send(404, b"not found")
        else:
            page = pathlib.Path("app.html").read_bytes()
            self._send(200, page, "text/html; charset=utf-8")

    def log_message(self, *a): pass


if __name__ == "__main__":
    import os
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8734))), H).serve_forever()
