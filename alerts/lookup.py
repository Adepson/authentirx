"""AuthentiRx week 3: lookup a drug name against the curated alert table.
Combines: (1) alias mapping so international names match official titles
(salbutamol -> albuterol, paracetamol -> acetaminophen), and
(2) keyword search over NAFDAC's public alert entries.
Returns official notice titles + links only. No verdicts of its own.
"""
from __future__ import annotations
import json, pathlib

ALIASES = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "glibenclamide": "glyburide",
    "adrenaline": "epinephrine",
    "ORS": "oral rehydration salts",
}

TABLE = pathlib.Path(__file__).parent / "nafdac_alerts.json"


def _load():
    return json.load(open(TABLE))


def lookup(drug_name: str) -> list:
    names = {drug_name.lower(), ALIASES.get(drug_name.lower(), "").lower()}
    names.discard("")
    hits = []
    for e in _load():
        t = e["title"].lower()
        if any(n in t for n in names):
            hits.append(e)
    return hits


if __name__ == "__main__":
    for probe in ["amoxicillin", "artemether", "folic acid", "chloroquine"]:
        hits = lookup(probe)
        print(f"\n{probe}: {len(hits)} NAFDAC alert(s)")
        for h in hits[:3]:
            print("  ", h["year"], h["title"][:100])
            print("   ", h["url"][:90])
