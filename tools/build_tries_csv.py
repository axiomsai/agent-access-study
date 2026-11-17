#!/usr/bin/env python3
"""Write data/tries.csv: one row per counted try (4 tools x 100 product pages x 3 days = 1,200 rows).

Reads only files in this repository: runs/products-2026-11-{05,07,09}/final.json (the final outcome per try, from
final.py), coding.jsonl (the two blind coders), rulings.csv (rulings on disputes) and stores.yaml (the product URLs).
The chart_outcome column uses the five outcomes on the study page; the per-tool totals it prints match Figure 1.

    python3 tools/build_tries_csv.py
"""
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAYS = ["2026-11-05", "2026-11-07", "2026-11-09"]
TOOLS = {"claude": ("Anthropic", "Anthropic web fetch"), "gemini": ("Google", "Google URL context"),
         "openai": ("OpenAI", "OpenAI web search"), "perplexity": ("Perplexity", "Perplexity Sonar (search index)")}
CODERS = {"claude": "Claude", "gemini": "Gemini", "gpt": "GPT"}
# final.py's outcome -> the five outcomes the study page charts
CHART = {"price_match": "Price matched", "price_wrong": "Price wrong", "matched_other_listed_price": "Price wrong",
         "no_price": "Got in, no price", "turned_away": "Turned away", "price_while_blocked": "Turned away",
         "ungradable": "Not graded", "price_conflict": "Not graded"}
COLUMNS = ["day", "store", "page", "product_url", "company", "tool", "chart_outcome", "final_outcome", "final_access",
           "coder_1", "coder_1_access", "coder_2", "coder_2_access", "ruling", "ruling_reason", "price_given",
           "control_price", "other_store_prices", "copy_age_days", "tool_said_opened", "raw_response", "note"]


def products():
    """stores.yaml -> {domain: [url, ...]}. Plain parsing, so the script needs no packages."""
    out, cur = {}, None
    for line in (ROOT / "stores.yaml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([a-z0-9.-]+\.[a-z]+):\s*$", line)
        if m:
            cur = m.group(1)
        m = re.match(r"^\s+products:\s*\[(.*)\]\s*$", line)
        if m and cur:
            out[cur] = [u.strip().strip('"') for u in m.group(1).split(",")]
    return out


def money(v):
    return "" if v is None else f"{float(v):.2f}"


def main():
    urls = products()
    rows, totals = [], collections.Counter()
    for day in DAYS:
        run = ROOT / "runs" / f"products-{day}"
        coders = collections.defaultdict(list)
        for line in (run / "coding.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            coders[r["key"]].append((CODERS.get(r["coder"], r["coder"]), r.get("access") or ""))
        rulings = {}
        if (run / "rulings.csv").exists():
            with open(run / "rulings.csv", encoding="utf-8") as f:
                rulings = {r["key"]: r for r in csv.DictReader(f)}
        for x in json.loads((run / "final.json").read_text(encoding="utf-8")):
            key = f"{x['domain']}|{x['idx']}|{x['fetcher']}"
            c = coders.get(key, []) + [("", ""), ("", "")]
            rule = rulings.get(key, {})
            chart = CHART[x["final_outcome"]]
            totals[(x["fetcher"], chart)] += 1
            raw = run / x["domain"] / f"p{x['idx']}-{x['fetcher']}.json"
            company, tool = TOOLS[x["fetcher"]]
            rows.append({
                "day": day, "store": x["domain"], "page": x["idx"], "product_url": urls[x["domain"]][x["idx"] - 1],
                "company": company, "tool": tool, "chart_outcome": chart, "final_outcome": x["final_outcome"],
                "final_access": x["final_access"], "coder_1": c[0][0], "coder_1_access": c[0][1],
                "coder_2": c[1][0], "coder_2_access": c[1][1], "ruling": rule.get("ruling", ""),
                "ruling_reason": rule.get("reason", ""), "price_given": money(x["price"]),
                "control_price": money(x["truth"]), "other_store_prices": " ".join(money(a) for a in x.get("alts") or []),
                "copy_age_days": "" if x.get("age_days") is None else x["age_days"],
                "tool_said_opened": x.get("opened") or "",
                "raw_response": raw.relative_to(ROOT).as_posix() if raw.exists() else "", "note": x.get("note", ""),
            })
    rows.sort(key=lambda r: (r["day"], r["store"], r["page"], r["company"]))
    out = ROOT / "data" / "tries.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out.relative_to(ROOT)}")
    for fetcher, (company, _) in TOOLS.items():
        print(f"  {company:<10} " + "  ".join(f"{k}: {totals[(fetcher, k)]}" for k in
              ["Price matched", "Price wrong", "Got in, no price", "Turned away", "Not graded"]))


if __name__ == "__main__":
    main()
