"""AuthentiRx week 3: build the curated NAFDAC alert table.
Scrapes ONLY the public listing pages of NAFDAC's own Recalls and Safety
Alerts section (official public notices), storing: title, year, url.
Plain-English summaries are added by human curation later; until then the
app shows the official title and link, never its own verdict.
"""
from __future__ import annotations
import re, html, json, urllib.request

LISTING = "https://nafdac.gov.ng/category/recalls-and-alerts/"
UA = {"User-Agent": "AuthentiRx/0.1 (research)"}


def fetch_page(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def parse_alerts(page_html):
    out, seen = [], set()
    for u, t in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page_html, re.S):
        t = re.sub(r"<[^>]+>", "", t)
        t = html.unescape(t).strip()
        if len(t) < 20 or "nafdac.gov.ng" not in u:
            continue
        low = t.lower()
        if not any(w in low for w in ("alert", "recall", "counterfeit", "falsified", "substandard", "unregistered", "ban")):
            continue
        m = re.search(r"(20\d\d)", u) or re.search(r"(20\d\d)", t)
        year = int(m.group(1)) if m else None
        if u not in seen:
            seen.add(u)
            out.append({"title": t[:220], "year": year, "url": u,
                        "source": "NAFDAC Recalls and Safety Alerts"})
    return out


def build(pages=1):
    entries = []
    for p in range(1, pages + 1):
        url = LISTING if p == 1 else f"{LISTING}page/{p}/"
        entries += parse_alerts(fetch_page(url))
    json.dump(entries, open("alerts/nafdac_alerts.json", "w"), indent=1)
    return entries


if __name__ == "__main__":
    e = build(1)
    print(f"{len(e)} NAFDAC alert entries saved; years "
          f"{min((x["year"] or 0) for x in e)}-{max((x["year"] or 0) for x in e)}")
