#!/usr/bin/env python3
"""Agent Access Study: product-page read. Each vendor's own API fetch tool opens each product page in stores.yaml and
reports name, price and stock in a fixed line. The browser control (control_*.json, loaded in Chrome) is graded
against it afterwards by grade.py.

    .venv/bin/python products.py [--cap 40] [--only amazon.com,...]
"""
import argparse, concurrent.futures as cf, datetime as dt, json, re, sys
from pathlib import Path

import yaml

import pilot  # fetchers, cost meter, classify

HERE = Path(__file__).resolve().parent
OUT = HERE / "runs" / f"products-{dt.date.today().isoformat()}"
pilot.PROMPT = ("Open this exact product page with your web tool: {url}\n"
                "Answer in exactly this one line and nothing else:\n"
                "NAME: <product name as the page shows it> | PRICE: <the current selling price shown, like $12.34, or NONE> | "
                "STOCK: <IN STOCK, OUT OF STOCK or UNKNOWN> | OPENED: <YES, or NO: the reason (error, blocked, captcha, not allowed)>\n"
                "Use only what the page shows today. Do not guess or use memory.")
LINE = re.compile(r"NAME:\s*(?P<name>.*?)\s*\|\s*PRICE:\s*(?P<price>.*?)\s*\|\s*STOCK:\s*(?P<stock>.*?)\s*\|\s*OPENED:\s*(?P<opened>.*)", re.I | re.S)


def parse_line(ans):
    m = LINE.search(ans or "")
    if not m:
        return {"parsed": False}
    p = re.search(r"\$\s?([\d,]+(?:\.\d{2})?)", m["price"])
    return {"parsed": True, "name": m["name"].strip()[:200], "price": float(p.group(1).replace(",", "")) if p else None,
            "price_raw": m["price"].strip()[:60], "stock": m["stock"].strip().upper()[:20], "opened": m["opened"].strip()[:160]}


def one(domain, url, idx, cap):
    d = OUT / domain; d.mkdir(parents=True, exist_ok=True)
    rec = {"domain": domain, "url": url, "idx": idx, "at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "fetch": {}}
    calls = {"claude": lambda: pilot.fetch_claude(url, cap), "gemini": lambda: pilot.fetch_gemini(url, cap),
             "openai": lambda: pilot.fetch_openai(url, cap), "perplexity": lambda: pilot.fetch_perplexity(url, domain.split("/")[0], cap)}
    for name, fn in calls.items():
        try:
            res = fn()
        except SystemExit:
            raise
        except Exception as e:
            res = {"error": f"{type(e).__name__}: {e}"[:400]}
        (d / f"p{idx}-{name}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
        verdict, why = pilot.classify(name, res, re.sub(r"^https?://(www\.|us\.)?", "", url).split("/")[0])
        rec["fetch"][name] = {"verdict": verdict, "why": why, **parse_line(res.get("answer")), "retrieved_at": res.get("retrieved_at"),
                              "age_days": res.get("age_days"), "cost_usd": res.get("cost_usd", 0)}
    (d / f"p{idx}-record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=float, default=40.0); ap.add_argument("--only")
    a = ap.parse_args()
    pilot.load_env()
    st = yaml.safe_load((HERE / "stores.yaml").read_text())["stores"]
    jobs = [(dom, u, i) for dom, v in st.items() for i, u in enumerate(v["products"], 1) if not a.only or dom in a.only.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for rec in ex.map(lambda j: one(*j, a.cap), jobs):
            recs.append(rec)
            print(f"{rec['domain']:<15} p{rec['idx']} " + " ".join(f"{k}={v['verdict']}:{v.get('price')}" for k, v in rec["fetch"].items()), flush=True)
    (OUT / "summary.json").write_text(json.dumps(recs, indent=1, ensure_ascii=False))
    print(f"\n{len(recs)} product pages, spend about ${pilot.spend['usd']:.2f} -> {OUT}")


if __name__ == "__main__":
    main()
