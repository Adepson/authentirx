# AuthentiRx

AuthentiRx is a mobile-first prescription verification and drug safety web app. A user types a medicine name and sees the officially identified drug name, public safety alerts, FDA recall records, and official label warnings, each with its source.

AuthentiRx is an information tool. It does not decide whether a medicine is genuine, safe, or approved, and it does not give medical advice. Always confirm with a pharmacist or doctor.

## What it uses

All data sources are free and open:

- RxNorm (NIH RxNav) to resolve medicine names, including common misspellings and brand names, to a standard drug identity.
- openFDA drug labels to show official FDA label warnings for a medicine.
- openFDA enforcement data to show FDA recall records with classification and reason.
- openFDA FAERS adverse event data to show reported adverse event counts for a medicine. These are reports, not proof of cause.
- NAFDAC Nigeria public recalls and safety alerts, stored as a local table (alerts/nafdac_alerts.json) and matched by name, with links to the official notices.

Interaction checks are label-text-based only. The app looks for other medicines named in a medicine's FDA label text. It is not a clinical drug interaction checker and must not be used as one.

No API keys, accounts, or paid services are required. No personal data or location is collected by the app.

## Files

- server.py: the web server and JSON API (standard library only, no dependencies).
- app.html: the mobile-first single-page interface.
- rxnorm/client.py: RxNorm name resolution.
- openfda/client.py, label.py, faers.py, interactions.py: openFDA recalls, label warnings, adverse event counts, and label-text interaction checks.
- alerts/lookup.py: matches typed names to the local NAFDAC alert table.
- alerts/build.py: rebuilds the NAFDAC alert table from the NAFDAC public alerts listing.
- alerts/nafdac_alerts.json: the local NAFDAC alert table.
- week2_test.py: runs the openFDA pipeline over 50 common medicines.
- week5_safety_audit.py: checks the safety rules (disclaimer present, no verdict language, safe failure on unknown names).

## How to run

Requires Python 3.9 or newer. No installation of packages is needed.

    python server.py

Then open http://127.0.0.1:8734 in a browser. The server listens on localhost only.

API endpoints:

- /api/check?name=<medicine>: RxNorm match, NAFDAC alerts, FDA recalls, FDA label warning.
- /api/label?name=<medicine> or ?rxcui=<id>: FDA label sections.
- /api/events?name=<medicine>: FAERS adverse event counts.
- /api/interactions?names=<a,b,c>: label-text mentions between up to 6 medicines.

To run the checks:

    python week5_safety_audit.py
    python week2_test.py

## Status

This is an MVP. Known open items: WHO alerts are not yet ingested (no free API), plain-language alert summaries need human review, and interaction checking is limited to label text. Hosting is not set up yet.
