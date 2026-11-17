#!/usr/bin/env python3
"""Final per-answer outcome for one run day: the coded access class (two coders, Karen's rulings on disputes) decides
access, and the deterministic grade (grade.py) decides the price only on answers whose final class is opened.
Amendment 2026-11-07. Reads graded.json, coding.jsonl, rulings.csv; writes final.json and prints the day's table.

    python3 final.py runs/products-2026-11-07
"""
import collections, csv, json, sys
from pathlib import Path

R = Path(sys.argv[1])
TA = {"refused_or_error", "shell_or_challenge"}
F = ["claude", "gemini", "openai", "perplexity"]
graded = json.loads((R / "graded.json").read_text())
coded = collections.defaultdict(list)
for line in (R / "coding.jsonl").read_text().splitlines():
    r = json.loads(line)
    coded[r["key"]].append(r.get("access"))
rulings = {}
if (R / "rulings.csv").exists():
    for row in csv.DictReader(open(R / "rulings.csv")):
        rulings[row["key"]] = row["ruling"]

out, open_keys = [], []
for x in graded:
    key = f"{x['domain']}|{x['idx']}|{x['fetcher']}"
    acc = coded.get(key, [])
    if len(acc) == 2 and acc[0] == acc[1]:
        final = acc[0]
    elif set(acc) <= TA:
        final = "turned_away"  # standing ruling 2026-11-05: refused vs challenge are both turned away
    elif key in rulings and rulings[key] not in ("", "OPEN"):
        final = rulings[key]
    else:
        final = "disputed"
        open_keys.append(key)
    if final in TA or final == "turned_away":
        outcome = "price_while_blocked" if x["price"] is not None else "turned_away"
    elif final == "blind_to_price":
        outcome = "no_price"
    elif final == "opened":
        outcome = x["outcome"] if x["outcome"] not in ("no_access", "shell_page") else "rule_says_no_access"
    else:
        outcome = "disputed"
    # Amendment 2026-11-11: Depop's Thursday control price includes its buyer fee (item x 1.05 + 0.70); the item price counts as a match.
    if outcome == "price_wrong" and x["domain"] == "depop.com" and R.name == "products-2026-11-05" and x["price"] is not None \
            and x["truth"] is not None and abs(x["price"] - (float(x["truth"]) - 0.70) / 1.05) <= 0.01:
        outcome = "price_match"
        x = {**x, "note": "item price; control included Depop buyer fee (amendment 2026-11-11)"}
    out.append({**x, "coded": acc, "final_access": final, "final_outcome": outcome})

(R / "final.json").write_text(json.dumps(out, indent=1))
print(f"{R.name}: final outcomes (coded access + rulings; price graded only when opened)")
for f in F:
    t = collections.Counter(o["final_outcome"] for o in out if o["fetcher"] == f)
    g = t["price_match"] + t["price_wrong"] + t["matched_other_listed_price"]
    print(f"  {f:<11} match {t['price_match']}/{g}  wrong {t['price_wrong']}  other_listed {t['matched_other_listed_price']}  "
          f"conflict {t['price_conflict']}  no_price {t['no_price']}  turned_away {t['turned_away']}  "
          f"price_while_blocked {t['price_while_blocked']}  ungradable {t['ungradable']}  other {dict((k, v) for k, v in t.items() if k in ('disputed', 'rule_says_no_access'))}")
pb = [o for o in out if o["final_outcome"] == "price_while_blocked"]
print(f"gave a price while turned away: {len(pb)}, of which equal to the control: "
      f"{sum(1 for o in pb if o['truth'] is not None and abs(o['price'] - float(o['truth'])) <= 0.01)}")
if open_keys:
    print("OPEN, needs Karen:", open_keys)
