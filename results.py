#!/usr/bin/env python3
"""Fill the five pre-registered lead numbers (PREREG, Lead numbers + Definitions) from the three counted days.
Access comes from final.json (coded class + Karen's rulings); price from grade.py via final.json; copy age from
summary.json; robots from the homepage read. Writes runs/RESULTS.json and prints the tables.

    python3 results.py
"""
import collections, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAYS = ["2026-11-05", "2026-11-07", "2026-11-09"]
LIVE = ["claude", "gemini", "openai"]
F = ["claude", "gemini", "openai", "perplexity"]
TA = {"refused_or_error", "shell_or_challenge", "turned_away"}
AI_TOKENS_EXCLUDE = {"*"}

final = {d: json.loads((HERE / f"runs/products-{d}/final.json").read_text()) for d in DAYS}
summ = {d: {(r["domain"], r["idx"]): r for r in json.loads((HERE / f"runs/products-{d}/summary.json").read_text())} for d in DAYS}
out = {}

# Lead 1. Turned away on a page: at least 2 of 3 days. By a store: at least 3 of its 5 pages. Lead: stores where
# at least two of the three live fetchers are turned away by the store.
page_days = collections.defaultdict(int)
pages = set()
for d in DAYS:
    for x in final[d]:
        pages.add((x["domain"], x["idx"]))
        if x["final_access"] in TA:
            page_days[(x["domain"], x["idx"], x["fetcher"])] += 1
stores = sorted({p[0] for p in pages})
by_store = {}
for s in stores:
    by_store[s] = {f: sum(1 for (dom, i) in pages if dom == s and page_days[(dom, i, f)] >= 2) for f in F}
turned_away_by = {s: [f for f in F if by_store[s][f] >= 3] for s in stores}
lead1 = [s for s in stores if sum(1 for f in LIVE if f in turned_away_by[s]) >= 2]
out["lead1"] = {"stores_with_product_pages": len(stores), "stores": lead1, "count": len(lead1),
                "turned_away_by_store": turned_away_by, "pages_turned_away_2of3": by_store}

# Lead 2. Blind to price: reached the page and gave no price, per fetcher, per day of 100 and pooled of 300.
out["lead2"] = {f: {d: sum(1 for x in final[d] if x["fetcher"] == f and x["final_access"] == "blind_to_price") for d in DAYS} for f in F}

# Lead 3. Price match among graded prices (match, wrong, other listed), per fetcher, per day and pooled.
lead3 = {}
for f in F:
    row = {}
    for d in DAYS:
        c = collections.Counter(x["final_outcome"] for x in final[d] if x["fetcher"] == f)
        row[d] = {"match": c["price_match"], "graded": c["price_match"] + c["price_wrong"] + c["matched_other_listed_price"],
                  "other_listed": c["matched_other_listed_price"], "conflict": c["price_conflict"], "price_while_blocked": c["price_while_blocked"]}
    m = sum(row[d]["match"] for d in DAYS); g = sum(row[d]["graded"] for d in DAYS)
    row["pooled"] = {"match": m, "graded": g, "per_100": round(100 * m / g, 1) if g >= 20 else None}
    lead3[f] = row
out["lead3"] = lead3

# Lead 4. Anthropic copies older than 7 days, of 100 pages per day, and how many of those answers said so.
lead4 = {}
for d in DAYS:
    said = {}
    for line in (HERE / f"runs/products-{d}/coding.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["fetcher"] == "claude":
            said.setdefault(r["key"], []).append(r.get("said_copy_age"))
    dated = old = old_said = 0
    for (dom, i), rec in summ[d].items():
        a = rec["fetch"]["claude"].get("age_days")
        if a is None:
            continue
        dated += 1
        if a > 7:
            old += 1
            v = said.get(f"{dom}|{i}|claude", [])
            if v and all(s == "y" for s in v):
                old_said += 1
    lead4[d] = {"dated": dated, "older_than_7_days": old, "said_so": old_said}
out["lead4"] = lead4

# Lead 5. Stores whose robots.txt disallows at least one AI agent token (homepage path), per run day.
lead5 = {}
for d in DAYS:
    hits = []
    for rec_path in sorted((HERE / f"runs/pilot-{d}").glob("*/record.json")):
        rec = json.loads(rec_path.read_text())
        rules = (rec.get("robots") or {}).get("rules") or {}
        if any(v.get("homepage_allowed") is False for k, v in rules.items() if k not in AI_TOKENS_EXCLUDE):
            hits.append(rec["domain"])
    lead5[d] = {"count": len(hits), "of": len(list((HERE / f"runs/pilot-{d}").glob("*/record.json"))), "stores": hits}
out["lead5"] = lead5

# Beside the leads: coded vs rule-based access agreement (Grading section), price while blocked, conflicts.
agree = tot = 0
for d in DAYS:
    for x in final[d]:
        rule = "turned_away" if x["outcome"] in ("no_access", "shell_page") else "blind_to_price" if x["outcome"] == "no_price" else "opened"
        coded = "turned_away" if x["final_access"] in TA else x["final_access"]
        tot += 1; agree += rule == coded
out["coded_vs_rule_access_agreement"] = {"agree": agree, "of": tot}
out["price_while_blocked"] = {d: sum(1 for x in final[d] if x["final_outcome"] == "price_while_blocked") for d in DAYS}
out["price_conflict_pages"] = {d: len({(x["domain"], x["idx"]) for x in final[d] if x.get("conflict")}) for d in DAYS}
(HERE / "runs/RESULTS.json").write_text(json.dumps(out, indent=1))

print(f"LEAD 1  {len(lead1)} of {len(stores)} stores with product pages turned away at least two of the three live fetchers on most product pages: {', '.join(lead1)}")
print("LEAD 2  blind to price (per day of 100; pooled of 300)")
for f in F:
    v = out["lead2"][f]; print(f"   {f:<11} {' / '.join(str(v[d]) for d in DAYS)}   pooled {sum(v.values())} of 300")
print("LEAD 3  price matched the store's page (pooled; rate only on 20+ graded)")
for f in F:
    r = lead3[f]; print(f"   {f:<11} {r['pooled']['match']} of {r['pooled']['graded']}  = {r['pooled']['per_100']} per 100   days: " + ", ".join(f"{r[d]['match']}/{r[d]['graded']}" for d in DAYS))
print("LEAD 4  Anthropic copies older than 7 days (of dated answers), and said so")
for d in DAYS:
    v = lead4[d]; print(f"   {d}  {v['older_than_7_days']} of {v['dated']} dated (of 100 pages); said so {v['said_so']}")
print("LEAD 5  stores whose robots.txt disallows at least one AI agent")
for d in DAYS:
    v = lead5[d]; print(f"   {d}  {v['count']} of {v['of']}")
print(f"coded vs rule access agreement: {agree} of {tot}; price while blocked {out['price_while_blocked']}; conflict pages {out['price_conflict_pages']}")
