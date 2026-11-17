#!/usr/bin/env python3
"""Two blind coders classify every product-page fetch answer: access class, price given, and whether a stale copy was disclosed.
Coders come from labs other than the fetcher's (PREREG, Grading). Deterministic price match stays in grade.py.

    .venv/bin/python code_fetch.py runs/products-2026-11-03 [--cap 10]
Writes {run}/coding.jsonl (one line per fetch per coder) and {run}/coding-summary.json, and prints agreement.
"""
import argparse, collections, concurrent.futures as cf, json, os, sys, threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agent-grounding"))
import common  # noqa: E402  vendor callers + env

CODERS = {"claude": ("anthropic", "claude-haiku-5-5"), "gemini": ("google", "gemini-3.1-flash-lite"), "gpt": ("openai", "gpt-5.4-mini")}
PAIR = {"claude": ("gemini", "gpt"), "gemini": ("claude", "gpt"), "openai": ("claude", "gemini"), "perplexity": ("gemini", "gpt")}
PRICE = {"claude-haiku-5-5": (0.10, 0.50), "gemini-3.1-flash-lite": (0.10, 0.40), "gpt-5.4-mini": (0.25, 2.00)}
ACCESS = ["opened", "blind_to_price", "shell_or_challenge", "refused_or_error"]
spend = {"usd": 0.0}
lock = threading.Lock()

SYSTEM = """You code one answer from an AI web-fetch tool for a research study. The tool was asked to open one store product page and answer in one line: NAME | PRICE | STOCK | OPENED.
Classify from the answer and the tool metadata only. Do not use outside knowledge.
access, exactly one of:
- opened: the tool reached the real product page and the answer gives a price
- blind_to_price: the tool reached the real page but the answer gives no price (NONE, unknown, not shown)
- shell_or_challenge: the answer shows the tool got a captcha, robot check, access-denied, "JavaScript is disabled", an empty shell, or a different page than the product
- refused_or_error: the tool reported an error, a block, a refusal, a timeout, or "not allowed"
price_given: the price the answer states as the current selling price, as a number, or null.
said_copy_age: "y" if the answer tells the user the page copy may be old or gives its retrieval date; "n" if it does not; "na" if no copy date was supplied in the metadata.
Return only JSON: {"access": "...", "price_given": number|null, "said_copy_age": "y"|"n"|"na", "quote": "the words from the answer that decide access"}"""


def load_items(run):
    items = []
    for rec in json.loads((run / "summary.json").read_text()):
        for f in ("claude", "gemini", "openai", "perplexity"):
            raw = json.loads((run / rec["domain"] / f"p{rec['idx']}-{f}.json").read_text())
            meta = {"tool_error": raw.get("tool_error"), "retrieved_at": raw.get("retrieved_at"), "doc_chars": raw.get("doc_chars"),
                    "url_status": raw.get("url_status"), "actions": raw.get("actions"), "cited_store": raw.get("cited_store"), "api_error": raw.get("error")}
            items.append({"key": f"{rec['domain']}|{rec['idx']}|{f}", "fetcher": f, "answer": (raw.get("answer") or "")[:3000],
                          "meta": {k: v for k, v in meta.items() if v not in (None, [], "")}})
    return items


def code(item, coder, cap):
    vendor, model = CODERS[coder]
    user = f"Tool metadata: {json.dumps(item['meta'], default=str)[:1500]}\n\nAnswer:\n{item['answer'] or '(empty)'}"
    kw = {"max_tokens": 1500}
    if vendor == "google":
        kw["thinking"] = "low"
    try:
        r = common.call(vendor, model, SYSTEM, user, **kw)
        p = PRICE[model]; c = r["usage"]["input"] / 1e6 * p[0] + r["usage"]["output"] / 1e6 * p[1]
        with lock:
            spend["usd"] += c
            if spend["usd"] > cap:
                raise SystemExit(f"cap ${cap} passed")
        out = common.parse_json(r["text"])
    except SystemExit:
        raise
    except Exception as e:
        out = {"error": f"{type(e).__name__}: {e}"[:200]}
    return {"key": item["key"], "fetcher": item["fetcher"], "coder": coder, **out}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run"); ap.add_argument("--cap", type=float, default=10.0)
    a = ap.parse_args(); run = Path(a.run)
    common.load_env()
    items = load_items(run)
    jobs = [(it, c) for it in items for c in PAIR[it["fetcher"]]]
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        rows = list(ex.map(lambda j: code(j[0], j[1], a.cap), jobs))
    (run / "coding.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    by = collections.defaultdict(list)
    for r in rows:
        by[r["key"]].append(r)
    agree = collections.Counter(); final = {}
    for k, rs in by.items():
        acc = [r.get("access") for r in rs]
        if len(rs) == 2 and acc[0] == acc[1] and acc[0] in ACCESS:
            agree["access_agree"] += 1; final[k] = acc[0]
        else:
            agree["access_disagree"] += 1; final[k] = "DISPUTE:" + "/".join(str(x) for x in acc)
        said = {r.get("said_copy_age") for r in rs}
        if "y" in said or "n" in said:
            agree["said_y" if said == {"y"} else ("said_n" if said == {"n"} else "said_split")] += 1
    summ = {"items": len(by), "spend_usd": round(spend["usd"], 3), "agreement": dict(agree),
            "access_by_fetcher": {f: dict(collections.Counter(v for k, v in final.items() if k.endswith("|" + f))) for f in PAIR},
            "disputes": [k for k, v in final.items() if v.startswith("DISPUTE")]}
    (run / "coding-summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps({k: v for k, v in summ.items() if k != "disputes"}, indent=1)); print("disputes:", len(summ["disputes"]))


if __name__ == "__main__":
    main()
