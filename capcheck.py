#!/usr/bin/env python3
"""Control run (PREREG amendment 2026-11-11): Anthropic web fetch with and without max_content_tokens=6000.
    .venv/bin/python capcheck.py [--cap 40]
"""
import argparse, concurrent.futures as cf, datetime as dt, json, re
from pathlib import Path
import yaml
import pilot, products

HERE = Path(__file__).resolve().parent
OUT = HERE / "runs" / f"capcheck-{dt.date.today().isoformat()}"
ORIG = pilot.fetch_claude


def fetch(url, cap, limit):
    import anthropic
    client = anthropic.Anthropic()
    tool = {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 1}
    if limit:
        tool["max_content_tokens"] = limit
    m = client.messages.create(model="claude-opus-5-5", max_tokens=2000, output_config={"effort": "low"}, tools=[tool],
                               messages=[{"role": "user", "content": pilot.PROMPT.format(url=url)}])
    blocks = [b.model_dump() for b in m.content]
    res = [b for b in blocks if b.get("type") == "web_fetch_tool_result"]
    err, doc_text, retrieved_at = None, "", None
    for b in res:
        c = b.get("content") or {}
        if c.get("type", "").endswith("error"):
            err = c.get("error_code")
        else:
            retrieved_at = c.get("retrieved_at")
            src = ((c.get("content") or {}).get("source") or {})
            doc_text = src.get("data") if isinstance(src.get("data"), str) else json.dumps(src)
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    return {"model": m.model, "tool_called": bool(res), "tool_error": err, "retrieved_at": retrieved_at,
            "age_days": (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(retrieved_at)).days if retrieved_at else None,
            "doc_chars": len(doc_text or ""), "doc_markers": pilot.markers((doc_text or "")[:20000]), "answer": text,
            "input_tokens": m.usage.input_tokens, "cost_usd": pilot.charge("claude", m.usage.input_tokens, m.usage.output_tokens, cap), "raw": blocks}


def one(domain, url, idx, cap):
    d = OUT / domain; d.mkdir(parents=True, exist_ok=True)
    rec = {"domain": domain, "idx": idx, "url": url, "arms": {}}
    for arm, limit in (("A_capped", 6000), ("B_uncapped", None)):
        try:
            r = fetch(url, cap, limit)
        except SystemExit:
            raise
        except Exception as e:
            r = {"error": f"{type(e).__name__}: {e}"[:400]}
        (d / f"p{idx}-{arm}.json").write_text(json.dumps(r, indent=1, default=str, ensure_ascii=False))
        v, why = pilot.classify("claude", r, re.sub(r"^https?://(www\.|us\.)?", "", url).split("/")[0])
        pl = products.parse_line(r.get("answer"))
        rec["arms"][arm] = {"verdict": v, "why": why, "price": pl.get("price"), "opened": pl.get("opened"),
                            "doc_chars": r.get("doc_chars"), "input_tokens": r.get("input_tokens"), "cost_usd": r.get("cost_usd", 0)}
    (d / f"p{idx}-record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=float, default=40.0); a = ap.parse_args()
    pilot.load_env(); pilot.PROMPT = products.pilot.PROMPT
    st = yaml.safe_load((HERE / "stores.yaml").read_text())["stores"]
    jobs = [(dom, u, i) for dom, v in st.items() for i, u in enumerate(v.get("products") or [], 1)]
    OUT.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(8) as ex:
        recs = list(ex.map(lambda j: one(*j, a.cap), jobs))
    (OUT / "records.json").write_text(json.dumps(recs, indent=1, ensure_ascii=False))
    print(len(recs), "pages; spend $%.2f" % pilot.spend["usd"])


if __name__ == "__main__":
    main()
