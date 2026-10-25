"""
AuthentiRx - label-based interaction flags (week 6).
Rule set: if drug A's openFDA label drug_interactions text mentions drug B
(by name, brand, or ingredient, whole word, case-insensitive), flag A -> B.
This is LABEL TEXT MATCHING ONLY. It is not a clinical interaction checker
and it can miss interactions or flag mentions that are not relevant.
"""
from __future__ import annotations
import re
from .label import label_by_name


def _terms(d: dict, typed: str) -> set[str]:
    t = {typed.strip().lower()}
    for k in ("generic", "brand"):
        if d.get(k): t.add(d[k].lower())
    for i in d.get("ingredients", []): t.add(i.lower())
    return {x for x in t if x}


def _mentions(text: str, term: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text, re.I) is not None


def check_pairs(names: list[str]) -> dict:
    names = [n.strip() for n in names if n and n.strip()]
    names = list(dict.fromkeys(names))  # dedupe, keep order
    out = {
        "disclaimer": "Label-text based check, not a clinical interaction checker. Absence of a flag does NOT mean no interaction. Ask a pharmacist or doctor.",
        "drugs": [], "flags": [], "errors": [],
    }
    if len(names) < 2:
        out["errors"].append("Enter at least two medicine names.")
        return out
    labels = {}
    for n in names:
        lab = label_by_name(n)
        labels[n] = lab
        if not lab["found"]:
            out["errors"].append(f"{n}: {lab['error']}")
        out["drugs"].append({"typed": n, "found": lab["found"], "generic": lab.get("generic", ""),
                             "has_interaction_section": "drug_interactions" in lab.get("sections", {})})
    for a in names:
        la = labels[a]
        if not la["found"]:
            continue
        text = la["_full_sections"].get("drug_interactions")
        if not text:
            continue
        for b in names:
            if a == b: continue
            lb = labels[b]
            if not lb["found"]: continue
            hit = next((t for t in sorted(_terms(lb, b), key=len, reverse=True) if _mentions(text, t)), None)
            if hit:
                out["flags"].append({
                    "drug_a": a, "drug_b": b, "matched_term": hit,
                    "message": f"The {a} label's drug interactions section mentions '{hit}' (drug {b}). Read the label or ask a pharmacist.",
                    "source": "openFDA drug label, drug_interactions section",
                })
    return out
