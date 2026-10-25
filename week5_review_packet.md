# AuthentiRx review packet (week 5)
Prepared for: (1) a licensed pharmacist, (2) a privacy/legal reviewer.

## What the app does (one line)
A user types a medicine name; the app shows the officially identified drug
(NIH RxNorm), any NAFDAC public safety alerts with links to the official
notices, FDA recall records with classification and reason, and the official
FDA label warning. The app never states its own verdict.

## For the pharmacist (about 1 hour)
1. Use the app with these test cases and mark PASS/FAIL:
   - "paracetmol" (misspelled) -> must show paracetamol
   - "augmentin" -> must show the 2026 counterfeit alert
   - "insulin" -> recalls and alerts, correctly attributed
   - a nonsense name -> must fail safely with a clear message
2. Judge: is showing official notices without interpretation safe for lay users?
3. Flag any output that could mislead (wrong match, misleading name display).
4. Recommend what a warning banner must say, if anything more.

## For the privacy reviewer (about 1 hour)
Data flow: the user's typed medicine name goes to NIH RxNav (USA) and
openFDA (USA). The NAFDAC table is stored locally, so those lookups do not
leave our server. No account, no personal data, no location is collected in
this MVP. Logs may contain the searched medicine name only.

Checklist to verify:
- Nigeria Data Protection Act 2023: health-related query data is sensitive;
  decide whether searching counts (we collect no identifiers, but logs do).
- Retention: propose deleting query logs after X days.
- Cross-border transfer disclosure (queries processed in the USA).
- Required privacy policy statements for a health-adjacent app.

## Already audited automatically (2026-10-23)
- Disclaimer present on every response.
- No verdict language ('safe', 'genuine', 'fake') in any output.
- Unknown/empty input fails safely.
- Audit script: week5_safety_audit.py (rerunnable).

## Known open items for reviewers
- WHO alerts not yet ingested (no API; curation needed).
- Plain-language summaries per alert need human review before pilot.
- Interaction checking still out of scope (no free licensed dataset).
