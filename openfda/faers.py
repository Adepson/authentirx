"""
AuthentiRx - FAERS adverse event client (week 6).
Pulls counts from openFDA /drug/event.json (FDA Adverse Event Reporting System)
for a generic name or substance. FAERS reports are unverified reports sent to
FDA. They are NOT proof that a drug caused an event. Reporting depends on how
widely a drug is used and on how much people report, so counts cannot be
compared across drugs as a rate of harm.
Reuses the rate-limited _get() from openfda.client. Data is US public domain (CC0).
"""
from __future__ import annotations
import time
import urllib.error
from . import client as fda

CACHE_TTL = 20 * 3600
_CACHE: dict[str, tuple[float, dict]] = {}

SERIOUS_FLAGS = {
    "death": "seriousnessdeath",
    "hospitalization": "seriousnesshospitalization",
    "life_threatening": "seriousnesslifethreatening",
    "disability": "seriousnessdisabling",
}
ALIASES = {"paracetamol": "acetaminophen", "salbutamol": "albuterol",
           "glibenclamide": "glyburide", "adrenaline": "epinephrine"}
DISCLAIMER = ("FAERS reports are unverified reports sent to FDA. A report does not prove that the drug caused the event. "
              "Reporting depends on how widely a drug is used, so higher counts do not mean a drug is more dangerous. "
              "Ask a pharmacist or doctor.")


def _drug_clause(name: str) -> str:
    return (f'(patient.drug.openfda.generic_name:"{name}" '
            f'OR patient.drug.openfda.substance_name:"{name}")')


def _total(search: str) -> int:
    """Count of matching reports, from meta.results.total (limit=1 keeps it cheap)."""
    data = fda._get("event.json", search, 1)
    if not data:
        return 0
    return int(data.get("meta", {}).get("results", {}).get("total", 0))


def _count(search: str, field: str, limit: int = 5) -> list[dict]:
    """openFDA count endpoint: top terms for a field among matching reports."""
    import json, urllib.parse, urllib.request
    url = (f"{fda.BASE}/event.json?search={urllib.parse.quote(search)}"
           f"&count={urllib.parse.quote(field)}&limit={limit}")
    wait = fda.MIN_INTERVAL - (time.monotonic() - fda._last)
    if wait > 0:
        time.sleep(wait)
    fda._last = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": fda.UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read()).get("results", [])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise


def events_by_name(name: str) -> dict:
    name = name.strip().lower()
    name = ALIASES.get(name, name)
    key = "faers:" + name
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    try:
        out = _build(name)
    except urllib.error.URLError as e:
        out = {"query": name, "found": False, "error": f"Could not reach openFDA (network error: {e.reason}). Try again shortly."}
    except TimeoutError:
        out = {"query": name, "found": False, "error": "openFDA did not answer in time. Try again shortly."}
    except urllib.error.HTTPError as e:
        out = {"query": name, "found": False, "error": f"openFDA returned HTTP {e.code}. Try again later."}
    except ValueError:
        out = {"query": name, "found": False, "error": "openFDA returned a response that could not be read."}
    _CACHE[key] = (time.time(), out)
    return out


def _build(name: str) -> dict:
    drug = _drug_clause(name)
    total = _total(drug)
    base = {"query": name, "source": "openFDA FAERS (adverse event reports)",
            "disclaimer": DISCLAIMER, "total_reports": total}
    if total == 0:
        return {**base, "found": False,
                "error": f"No FAERS reports found for '{name}'. Try the generic name printed on the pack."}
    serious_search = f"{drug} AND serious:1"
    serious_total = _total(serious_search)
    outcomes = {k: _total(f"{drug} AND {flag}:1") for k, flag in SERIOUS_FLAGS.items()}
    # Medically confirmed: reports from physicians (1), pharmacists (2) or other health professionals (3).
    confirmed = f"{drug} AND (primarysource.qualification:1 OR primarysource.qualification:2 OR primarysource.qualification:3)"
    confirmed_total = _total(confirmed)
    terms = _count(confirmed, "patient.reaction.reactionmeddrapt.exact", 5)
    basis = "medically confirmed reports"
    if not terms:
        terms = _count(drug, "patient.reaction.reactionmeddrapt.exact", 5)
        basis = "all reports (no medically confirmed reports matched)"
    return {
        **base,
        "found": True,
        "serious_reports": serious_total,
        "serious_share_pct": round(100 * serious_total / total, 1) if total else 0,
        "serious_outcomes": outcomes,
        "medically_confirmed_reports": confirmed_total,
        "top_reactions": [{"term": t["term"], "count": t["count"]} for t in terms],
        "top_reactions_basis": basis,
        "note": "Counts are for all reports in FAERS that name this drug. Top reaction terms are reported events, not confirmed side effects.",
        "source_note": "openFDA FAERS, drug event endpoint, CC0 public domain data.",
    }


if __name__ == "__main__":
    import json, sys
    for n in sys.argv[1:] or ["paracetamol", "amoxicillin", "warfarin"]:
        print(json.dumps(events_by_name(n), indent=1))
