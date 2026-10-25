"""
AuthentiRx - openFDA drug label client (week 6).
Pulls layperson-useful label sections from openFDA /drug/label.json by generic
name or RxCUI. Reuses the rate-limited _get() from openfda.client.
Data is US public domain (CC0). Label text is FDA's, not AuthentiRx's.
"""
from __future__ import annotations
import time
import urllib.error
from . import client as fda

SECTIONS = {
    "indications": "indications_and_usage",
    "dosage": "dosage_and_administration",
    "boxed_warning": "boxed_warning",
    "contraindications": "contraindications",
    "warnings": "warnings",
    "adverse_reactions": "adverse_reactions",
    "drug_interactions": "drug_interactions",
}
MAX_CHARS = 1200
CACHE_TTL = 20 * 3600
_CACHE: dict[str, tuple[float, dict]] = {}


def _clip(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS].rsplit(" ", 1)[0] + " ..."


def _fetch(search: str, limit: int = 1) -> dict:
    """Return {'ok': True, 'record': dict|None} or {'ok': False, 'error': str}."""
    try:
        data = fda._get("label.json", search, limit)
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Could not reach openFDA (network error: {e.reason}). Try again shortly."}
    except TimeoutError:
        return {"ok": False, "error": "openFDA did not answer in time. Try again shortly."}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"openFDA returned HTTP {e.code}. Try again later."}
    except ValueError:
        return {"ok": False, "error": "openFDA returned a response that could not be read."}
    if not data or not data.get("results"):
        return {"ok": True, "record": None}
    return {"ok": True, "record": _pick(data["results"], search)}


def _pick(results: list, search: str) -> dict:
    """Prefer a single-ingredient label whose generic name starts with the query,
    so 'metformin' gets metformin alone rather than a sitagliptin combination."""
    want = search.split(":", 1)[-1].strip('"').lower()
    def score(r):
        gens = [g.lower() for g in r.get("openfda", {}).get("generic_name", [])]
        single = all(" and " not in g for g in gens)
        exact = any(g == want for g in gens)
        starts = any(g.startswith(want) for g in gens)
        return (exact, starts and single, single)
    return max(results, key=score)


ALIASES = {"paracetamol": "acetaminophen", "salbutamol": "albuterol",
           "glibenclamide": "glyburide", "adrenaline": "epinephrine"}


def label_by_name(generic_name: str) -> dict:
    name = generic_name.strip().lower()
    name = ALIASES.get(name, name)
    key = "name:" + name
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    res = _fetch(f'openfda.generic_name:"{name}"', limit=10)
    if res["ok"] and res["record"] is None:
        res = _fetch(f'openfda.substance_name:"{name}"', limit=10)
    out = _shape(name, res)
    _CACHE[key] = (time.time(), out)
    return out


def label_by_rxcui(rxcui: str) -> dict:
    rxcui = str(rxcui).strip()
    key = "rxcui:" + rxcui
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    out = _shape(rxcui, _fetch(f'openfda.rxcui:"{rxcui}"', limit=10))
    _CACHE[key] = (time.time(), out)
    return out


def _shape(query: str, res: dict) -> dict:
    base = {"query": query, "source": "openFDA drug label (FDA label text)"}
    if not res["ok"]:
        return {**base, "found": False, "error": res["error"], "sections": {}, "_full_sections": {}}
    rec = res["record"]
    if rec is None:
        return {**base, "found": False,
                "error": f"No FDA label found for '{query}'. Try the generic name printed on the pack.",
                "sections": {}, "_full_sections": {}}
    of = rec.get("openfda", {})
    sections, missing, raw = {}, [], {}
    for label, field in SECTIONS.items():
        vals = rec.get(field)
        if vals and any(str(v).strip() for v in vals):
            full = " ".join(" ".join(str(v).split()) for v in vals)
            raw[label] = full  # full text, used for matching
            sections[label] = _clip(full)
        else:
            missing.append(label)
    return {
        **base,
        "found": True,
        "brand": (of.get("brand_name") or [""])[0],
        "generic": (of.get("generic_name") or [""])[0],
        "ingredients": of.get("substance_name") or [],
        "rxcui": (of.get("rxcui") or [""])[0],
        "sections": sections,
        "_full_sections": raw,
        "missing_sections": missing,
        "note": "Label text from FDA. The label may be for a different strength or form. Read the leaflet or ask a pharmacist.",
    }
