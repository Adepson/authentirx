"""
AuthentiRx - RxNorm (NIH RxNav) client, week 1 stage 1.
Purpose: match any user-typed medicine name (including misspellings and
brand names) to the official RxNorm drug record (RxCUI), the backbone ID
every later check (interactions, recalls, alerts) will use.

Terms of use: free, no key required at 20 req/s per IP. Attribution to
NLM/RxNav required. Cache results for 12-24h. See:
https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html
"""
from __future__ import annotations
import time, json, pathlib
import urllib.parse, urllib.request

BASE = "https://rxnav.nlm.nih.gov/REST"
CACHE = pathlib.Path(__file__).with_suffix(".cache")  # naive; swap for Redis later
_CACHE: dict[str, tuple[float, object]] = {}
CACHE_TTL = 20 * 3600  # 20h, inside NLM's 12-24h guidance
_last_call = 0.0
MIN_INTERVAL = 1 / 15  # stay safely under 20 req/s


def _get(path: str, **params) -> dict:
    global _last_call
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    now = time.monotonic()
    if now - _last_call < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - (now - _last_call))
    _last_call = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": "AuthentiRx/0.1 (research)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def resolve_drug(name: str) -> dict | None:
    """Best-effort match of a typed name to an official RxCUI.
    Returns {'rxcui', 'name'} or None if nothing matched."""
    key = f"approx:{name.lower()}"
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        cached = hit[1]
    else:
        try:
            data = _get("approximateTerm.json", term=name, maxEntries=3)
        except Exception:
            return None  # fail safe: bad/empty input matches nothing
        cands = data.get("approximateGroup", {}).get("candidate", [])
        # prefer a candidate that has a readable name
        best = next((c for c in cands if c.get("name")), cands[0] if cands else None)
        cached = (
            {"rxcui": best["rxcui"], "name": best.get("name", ""), "typed": name}
            if best
            else None
        )
        _CACHE[key] = (time.time(), cached)
    return cached


def drug_names(rxcui: str) -> list[str]:
    """All names/terms NIH attaches to this drug ID (for display + search)."""
    data = _get(f"rxcui/{rxcui}/properties.json")
    props = data.get("properties", {})
    return [props[k] for k in ("name", "synonym") if props.get(k)]


if __name__ == "__main__":
    for probe in ["paracetmol", "Amoxcillin", "ibuprofen 400"]:
        r = resolve_drug(probe)
        print(probe, "->", r)
        if r:
            print("   official names:", drug_names(r["rxcui"])[:6])
