"""
AuthentiRx - openFDA client, week 2.
Checks a drug name against FDA recall/enforcement records and official
label warnings. Data is US public domain (CC0); present results as dated
FDA records with sources, never as AuthentiRx's own verdicts.
Docs: https://open.fda.gov/apis/  Limits: 240/min, 1000/day keyless.
"""
from __future__ import annotations
import time, json, urllib.parse, urllib.request

BASE = "https://api.fda.gov/drug"
_last = 0.0
MIN_INTERVAL = 0.3
UA = "AuthentiRx/0.1 (research)"


def _get(path: str, search: str, limit: int = 5):
    global _last
    url = f"{BASE}/{path}?search={urllib.parse.quote(search)}&limit={limit}"
    wait = MIN_INTERVAL - (time.monotonic() - _last)
    if wait > 0: time.sleep(wait)
    _last = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise


def recalls(generic_name: str, limit: int = 5) -> list:
    data = _get("enforcement.json", f'openfda.generic_name:"{generic_name.lower()}"', limit)
    if not data: return []
    out = []
    for r in data.get("results", []):
        out.append({
            "status": r.get("status"),
            "classification": r.get("classification"),
            "product": (r.get("product_description") or "")[:200],
            "reason": (r.get("reason_for_recall") or "")[:200],
            "date": r.get("recall_initiation_date"),
            "source": "openFDA drug enforcement, record " + str(r.get("recall_number", "")),
        })
    return out


def label_warnings(generic_name: str):
    data = _get("label.json", f'openfda.generic_name:"{generic_name.lower()}"', 1)
    if not data: return None
    r = data["results"][0]
    of = r.get("openfda", {})
    return {
        "brand": (of.get("brand_name") or [""])[0],
        "generic": (of.get("generic_name") or [""])[0],
        "warnings": (r.get("warnings") or [""])[0][:400],
        "do_not_use": (r.get("do_not_use") or [""])[0][:200],
        "source": "openFDA drug label",
    }


def check(generic_name: str) -> dict:
    return {"drug": generic_name, "recalls": recalls(generic_name), "label": label_warnings(generic_name)}
