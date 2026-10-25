"""AuthentiRx week 2 test: run the openFDA pipeline on 50 common medicines."""
import json, sys, time
sys.path.insert(0, ".")
from openfda import client as fda

# 50 common medicines (INN names, globally relevant; openFDA is US data)
MEDS = ["acetaminophen", "ibuprofen", "amoxicillin", "azithromycin", "metronidazole",
    "ciprofloxacin", "doxycycline", "cephalexin", "gentamicin", "chloramphenicol",
    "paracetamol", "aspirin", "diclofenac", "naproxen", "tramadol",
    "morphine", "codeine", "prednisolone", "dexamethasone", "hydrocortisone",
    "metformin", "glibenclamide", "amlodipine", "lisinopril", "atenolol",
    "hydrochlorothiazide", "furosemide", "atorvastatin", "omeprazole", "ranitidine",
    "artemether", "lumefantrine", "artesunate", "sulfadoxine", "pyrimethamine",
    "chloroquine", "quinine", "praziquantel", "albendazole", "mebendazole",
    "ferrous sulfate", "folic acid", "vitamin a", "zinc sulfate", "oral rehydration salts",
    "insulin", "salbutamol", "epinephrine", "haloperidol", "diazepam"]

results, with_recalls, ok_labels = [], 0, 0
for m in MEDS:
    try:
        r = fda.check(m)
        results.append(r)
        if r["recalls"]: with_recalls += 1
        if r["label"]: ok_labels += 1
        print(f"{m:20s} recalls:{len(r['recalls'])} label:{'yes' if r['label'] else 'none'}")
    except Exception as e:
        results.append({"drug": m, "error": str(e)})
        print(f"{m:20s} ERROR {e}")
    time.sleep(0.35)

json.dump(results, open("week2_results.json", "w"), indent=1)
print(f"\nSUMMARY: {len(MEDS)} medicines | label data found for {ok_labels} | had FDA recall records: {with_recalls}")
