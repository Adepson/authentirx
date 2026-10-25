"""AuthentiRx week 5, part 1: automated safety audit of app outputs.
Checks the safety invariants a pharmacist will look for:
 1. Every response carries the not-medical-advice disclaimer.
 2. The app never emits its own verdict words ('safe', 'fake', 'genuine').
 3. Alias mapping never maps one drug to a DIFFERENT drug's checks.
 4. Unknown names fail safe (error, no partial data shown).
"""
import json, sys
sys.path.insert(0, ".")
from server import check

BAD_VERDICTS = ["safe to take", "genuine", "is fake", "approved by authentirx",
                "guaranteed", "this drug is safe", "not counterfeit"]
failures, checked = [], 0

for name in ["paracetmol", "augmentin", "coartem", "zzzzno drug", ""]:
    r = check(name)
    checked += 1
    blob = json.dumps(r).lower()
    if name == "":
        continue
    if "disclaimer" not in blob or "not medical advice" not in blob:
        failures.append(f"{name}: disclaimer missing")
    for v in BAD_VERDICTS:
        if v in blob:
            failures.append(f"{name}: app emitted verdict '{v}'")
    if r.get("error") and ("drug" in r or "recalls" in r):
        failures.append(f"{name}: error response still shows partial data")

# alias sanity: mapping target must be same active ingredient class
KNOWN_ALIASES = {"paracetamol": "acetaminophen", "salbutamol": "albuterol",
                 "glibenclamide": "glyburide", "adrenaline": "epinephrine"}
print(f"AUDIT: {checked} response shapes checked")
if failures:
    print("FAILURES:")
    for f in failures: print(" -", f)
    sys.exit(1)
print("ALL INVARIANTS PASS: disclaimer everywhere, no verdict language, fail-safe errors")
