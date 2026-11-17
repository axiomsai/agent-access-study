#!/usr/bin/env python3
"""Grade each fetcher's product answer against the browser control (rule-based first pass; pre-lock pilot).

    python3 grade.py runs/products-2026-11-03 runs/control-2026-11-03/control-transcribed.jsonl
"""
import collections, json, sys
from pathlib import Path

prod, ctl_path = Path(sys.argv[1]), Path(sys.argv[2])
ctl = {(c["domain"], c["idx"]): c for c in map(json.loads, ctl_path.read_text().splitlines())}
recs = json.loads((prod / "summary.json").read_text())
F = ["claude", "gemini", "openai", "perplexity"]
rows, tally = [], {f: collections.Counter() for f in F}
age = collections.Counter()
for r in recs:
    c = ctl.get((r["domain"], r["idx"]), {})
    truth = c.get("ld_price", c.get("page_price"))
    alts = c.get("alt_prices", [])
    gradable = truth is not None and not c.get("blk") and not c.get("low_confidence")
    # Amendment 2026-11-05: when the page's structured-data price and its visible price differ, the page is a
    # price conflict. It is recorded, never judged: no answer on it counts as a match or as wrong.
    conflict = c.get("ld_price") is not None and c.get("page_price") is not None and abs(float(c["ld_price"]) - float(c["page_price"])) > 0.01
    for f in F:
        x = r["fetch"][f]
        v = x["verdict"]
        if f == "claude" and x.get("age_days") is not None:
            age["claude_with_date"] += 1
            if x["age_days"] > 7:
                age["claude_older_than_7d"] += 1
            if x["age_days"] > 90:
                age["claude_older_than_90d"] += 1
        if v in ("blocked", "api_error", "unknown"):
            out = "no_access"
        elif v == "served_thin":
            out = "shell_page"
        elif x.get("price") is None:
            out = "no_price"
        elif not gradable:
            out = "ungradable"
        elif conflict:
            out = "price_conflict"
        elif abs(x["price"] - float(truth)) <= 0.01:
            out = "price_match"
        elif any(abs(x["price"] - float(a)) <= 0.01 for a in alts):
            out = "matched_other_listed_price"
        else:
            out = "price_wrong"
        tally[f][out] += 1
        cm = None
        if out == "price_conflict":
            p = x["price"]
            cm = ("structured" if abs(p - float(c["ld_price"])) <= 0.01 else "visible" if abs(p - float(c["page_price"])) <= 0.01
                  else "other_listed" if any(abs(p - float(a)) <= 0.01 for a in alts) else "neither")
        rows.append({"domain": r["domain"], "idx": r["idx"], "fetcher": f, "verdict": v, "price": x.get("price"), "truth": truth,
                     "conflict": conflict, "conflict_match": cm, "ld_price": c.get("ld_price"), "page_price": c.get("page_price"),
                     "alts": alts, "outcome": out, "age_days": x.get("age_days"), "opened": x.get("opened")})
(prod / "graded.json").write_text(json.dumps(rows, indent=1))
print("per fetcher, 100 product pages (20 stores x 5):")
for f in F:
    t = tally[f]; g = t["price_match"] + t["price_wrong"] + t["matched_other_listed_price"]
    print(f"  {f:<11} {dict(t)}   graded={g}  match={t['price_match']}/{g}")
print("claude copy dates:", dict(age))
cf = [x for x in rows if x["outcome"] == "price_conflict"]
print("\nprice conflicts (recorded, not judged):", len({(x["domain"], x["idx"]) for x in rows if x["conflict"]}), "pages")
for x in cf:
    print(f"  {x['domain']:<14} p{x['idx']} {x['fetcher']:<10} said {x['price']}  structured {x['ld_price']}  visible {x['page_price']}  -> {x['conflict_match']}")
# Amendment 2026-11-05 (b): answers that gave a price while turned away are counted and listed; their prices are never graded.
pb = [x for x in rows if x["outcome"] in ("no_access", "shell_page") and x["price"] is not None]
print(f"\ngave a price while turned away: {len(pb)}", dict(collections.Counter(x["fetcher"] for x in pb)))
for x in pb:
    print(f"  {x['domain']:<14} p{x['idx']} {x['fetcher']:<10} said {x['price']}  control {x['truth']}")
wrong = [x for x in rows if x["outcome"] == "price_wrong"]
print("\nwrong prices by store:", dict(collections.Counter(x["domain"] for x in wrong)))
for x in wrong[:40]:
    print(f"  {x['domain']:<14} p{x['idx']} {x['fetcher']:<10} said {x['price']} truth {x['truth']} age={x['age_days']}")
