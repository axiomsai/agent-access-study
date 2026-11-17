#!/usr/bin/env python3
"""Agent Access Study, PILOT read (2026-11-03, before the lock; excluded from published rates).

For each store homepage: robots.txt rules per agent token, one naive control load, and one fetch by each vendor's
own API fetch tool (Anthropic web fetch, Gemini URL context, OpenAI web search, Perplexity Sonar). Every raw response
is saved; the classification here is a first rule-based pass, and the locked study re-grades with two blind coders.

    .venv/bin/python pilot.py [--cap 30] [--only amazon.com,target.com]
"""
import argparse, concurrent.futures as cf, datetime as dt, json, os, re, sys, threading, time, urllib.request, urllib.robotparser
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ENV = Path.home() / "cortex/private/cortex-private/tools/deep-research/.env"
OUT = HERE / "runs" / f"pilot-{dt.date.today().isoformat()}"
UA_STUDY = "ProductAI-AgentAccessStudy/0.1 (research; +https://axioms.ai)"
UA_BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
TOKENS = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "PerplexityBot", "Perplexity-User", "ClaudeBot", "Claude-User",
          "Claude-SearchBot", "Google-Extended", "Meta-ExternalAgent", "Meta-ExternalFetcher", "Amazonbot", "Applebot-Extended", "*"]
BLOCK_MARKERS = ["access denied", "captcha", "are you a human", "are you a robot", "press & hold", "press and hold",
                 "pardon our interruption", "verify you are human", "request unsuccessful", "incapsula", "perimeterx",
                 "px-captcha", "403 forbidden", "you have been blocked", "/blocked", "robot or human", "unusual traffic",
                 "enable javascript and cookies", "just a moment", "javascript is disabled", "please enable javascript"]
PROMPT = ("Open this exact URL with your web tool and report only the page's title and one product or category name "
          "you can see on it: {url}\nIf you cannot open it, say exactly why (error, blocked, captcha, not allowed). Do not guess.")

PRICE = {"claude": (4.00, 20.00), "gemini": (0.10, 0.40), "openai": (0.25, 2.00), "perplexity": (1.00, 1.00)}
TOOL_FEE = {"claude": 0.0, "gemini": 0.0, "openai": 0.01, "perplexity": 0.005}   # per call, list-price approximations
spend = {"usd": 0.0}
lock = threading.Lock()


def load_env():
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def charge(vendor, tin, tout, cap):
    p = PRICE[vendor]
    c = tin / 1e6 * p[0] + tout / 1e6 * p[1] + TOOL_FEE[vendor]
    with lock:
        spend["usd"] += c
        if spend["usd"] > cap:
            raise SystemExit(f"cap ${cap} passed")
    return round(c, 5)


def markers(text):
    t = (text or "").lower()
    return [m for m in BLOCK_MARKERS if m in t]


def http_get(url, ua, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(400_000).decode("utf-8", "replace")
            return {"status": r.status, "final_url": r.geturl(), "bytes": len(body), "body": body}
    except urllib.error.HTTPError as e:
        body = e.read(100_000).decode("utf-8", "replace") if e.fp else ""
        return {"status": e.code, "final_url": url, "bytes": len(body), "body": body}
    except Exception as e:
        return {"status": None, "error": f"{type(e).__name__}: {e}"}


def read_robots(domain):
    r = http_get(f"https://www.{domain}/robots.txt", UA_STUDY)
    if r.get("status") != 200:
        r2 = http_get(f"https://{domain}/robots.txt", UA_STUDY)
        if r2.get("status") == 200:
            r = r2
    rules = {}
    if r.get("status") == 200:
        rp = urllib.robotparser.RobotFileParser(); rp.parse(r["body"].splitlines())
        named = r["body"].lower()
        for t in TOKENS:
            rules[t] = {"homepage_allowed": rp.can_fetch(t, f"https://www.{domain}/"),
                        "named_in_file": t == "*" or re.search(rf"user-agent:\s*{re.escape(t.lower())}\b", named) is not None}
    return {"status": r.get("status"), "error": r.get("error"), "rules": rules, "raw": r.get("body", "")[:200_000]}


def control(url):
    r = http_get(url, UA_BROWSER)
    title = re.search(r"<title[^>]*>(.*?)</title>", r.get("body", ""), re.S | re.I)
    return {"status": r.get("status"), "final_url": r.get("final_url"), "bytes": r.get("bytes"), "error": r.get("error"),
            "title": title.group(1).strip()[:200] if title else None, "markers": markers(r.get("body", "")[:20000])}


def fetch_claude(url, cap):
    import anthropic
    client = anthropic.Anthropic()
    kw = dict(model="claude-opus-5-5", max_tokens=2000, output_config={"effort": "low"},
              tools=[{"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 1, "max_content_tokens": 6000}],
              messages=[{"role": "user", "content": PROMPT.format(url=url)}])
    m = client.messages.create(**kw)
    blocks = [b.model_dump() for b in m.content]
    res = [b for b in blocks if b.get("type") == "web_fetch_tool_result"]
    err, doc_text, fetched_url, retrieved_at = None, "", None, None
    for b in res:
        c = b.get("content") or {}
        if c.get("type", "").endswith("error"):
            err = c.get("error_code")
        else:
            fetched_url = c.get("url"); retrieved_at = c.get("retrieved_at")
            src = ((c.get("content") or {}).get("source") or {})
            doc_text = src.get("data") if isinstance(src.get("data"), str) else json.dumps(src)[:20000]
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    return {"model": m.model, "stop_reason": m.stop_reason, "tool_called": bool(res), "tool_error": err, "fetched_url": fetched_url, "retrieved_at": retrieved_at,
            "age_days": (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(retrieved_at)).days if retrieved_at else None,
            "doc_chars": len(doc_text or ""), "doc_markers": markers((doc_text or "")[:20000]), "answer": text,
            "cost_usd": charge("claude", m.usage.input_tokens, m.usage.output_tokens, cap), "raw": blocks}


def fetch_gemini(url, cap):
    import requests
    model = "gemini-3.1-flash-lite"
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      headers={"x-goog-api-key": os.environ["GOOGLE_AI_API_KEY"]}, timeout=120,
                      json={"contents": [{"role": "user", "parts": [{"text": PROMPT.format(url=url)}]}], "tools": [{"url_context": {}}]})
    d = r.json()
    if r.status_code != 200:
        return {"http": r.status_code, "error": json.dumps(d)[:500], "cost_usd": 0, "raw": d}
    cand = (d.get("candidates") or [{}])[0]
    meta = (cand.get("urlContextMetadata") or cand.get("url_context_metadata") or {}).get("urlMetadata") or []
    um = d.get("usageMetadata", {})
    return {"model": d.get("modelVersion", model), "url_status": [(x.get("retrievedUrl"), x.get("urlRetrievalStatus")) for x in meta],
            "answer": "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", [])), "finish": cand.get("finishReason"),
            "cost_usd": charge("gemini", um.get("promptTokenCount", 0) + um.get("toolUsePromptTokenCount", 0), um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0), cap),
            "raw": d}


def fetch_openai(url, cap):
    import requests
    r = requests.post("https://api.openai.com/v1/responses", timeout=180, headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                      json={"model": "gpt-5.4-mini", "tools": [{"type": "web_search"}], "input": PROMPT.format(url=url)})
    d = r.json()
    if r.status_code != 200:
        return {"http": r.status_code, "error": json.dumps(d)[:500], "cost_usd": 0, "raw": d}
    calls = [o for o in d.get("output", []) if o.get("type") == "web_search_call"]
    actions = [(o.get("status"), (o.get("action") or {}).get("type"), (o.get("action") or {}).get("url") or (o.get("action") or {}).get("query")) for o in calls]
    text = "".join(c.get("text", "") for o in d.get("output", []) if o.get("type") == "message" for c in o.get("content", []))
    u = d.get("usage", {})
    return {"model": d.get("model"), "actions": actions, "answer": text,
            "cost_usd": charge("openai", u.get("input_tokens", 0), u.get("output_tokens", 0), cap) + 0.01 * max(0, len(calls) - 1), "raw": d}


def fetch_perplexity(url, domain, cap):
    import requests
    r = requests.post("https://api.perplexity.ai/chat/completions", timeout=120, headers={"Authorization": "Bearer " + os.environ["PERPLEXITY_API_KEY"]},
                      json={"model": "sonar", "messages": [{"role": "user", "content": PROMPT.format(url=url)}], "search_domain_filter": [domain]})
    d = r.json()
    if r.status_code != 200:
        return {"http": r.status_code, "error": json.dumps(d)[:500], "cost_usd": 0, "raw": d}
    u = d.get("usage", {})
    cites = d.get("citations") or [x.get("url") for x in d.get("search_results", []) if x.get("url")]
    return {"model": d.get("model"), "citations": cites, "cited_store": any(domain in (c or "") for c in cites),
            "answer": d["choices"][0]["message"]["content"],
            "cost_usd": charge("perplexity", u.get("prompt_tokens", 0), u.get("completion_tokens", 0), cap), "raw": d}


REFUSE = re.compile(r"(can(?:no|')t (?:open|access|retrieve|fetch)|unable to (?:open|access|retrieve|fetch)|blocked|captcha|denied|not allowed|403|forbidden|robots\.txt|could not (?:open|access|retrieve|fetch)|couldn't (?:open|access|retrieve|fetch)|failed to)", re.I)


def classify(f, res, domain):
    """First-pass rule read: served / blocked / robots / unknown, with the reason."""
    if not res or res.get("error") or res.get("http"):
        return "api_error", (res or {}).get("error", "")[:120]
    ans = res.get("answer", "") or ""
    if f == "claude":
        if res.get("tool_error"):
            return ("robots" if "robots" in (res["tool_error"] or "") else "blocked"), f"tool_error={res['tool_error']}"
        if not res.get("tool_called"):
            return "unknown", "no fetch call"
        if res["doc_markers"]:
            return "blocked", f"challenge page ({', '.join(res['doc_markers'])}, {res['doc_chars']} chars)"
        age = res.get("age_days")
        tag = f"{res['doc_chars']} chars, copy dated {(res.get('retrieved_at') or '')[:10]} ({age} days old)"
        if age is not None and age > 7:
            return "served_stale", tag
        if res["doc_chars"] < 400:
            return "served_thin", tag
        return "served", tag
    if f == "gemini":
        st = [s for _, s in res.get("url_status", [])]
        if any(s and "SUCCESS" in s for s in st):
            return ("blocked", "success status but answer reports a block") if REFUSE.search(ans) and not re.search(r"title", ans, re.I) else ("served", ",".join(st))
        if st:
            return "blocked", ",".join(st)
        return "unknown", "no URL context metadata"
    if f == "openai":
        opened = [a for a in res.get("actions", []) if a[1] == "open_page" and a[2] and domain in a[2]]
        if opened and markers(ans):
            return "served_thin", "opened a shell page: " + ", ".join(markers(ans))
        if opened:
            return ("blocked", "opened, answer reports a block") if REFUSE.search(ans) and len(ans) < 400 else ("served", "open_page on store")
        if REFUSE.search(ans):
            return "blocked", "no open_page; answer reports it could not open"
        return "unknown", "searched only: " + "; ".join(str(a[1]) for a in res.get("actions", []))[:80]
    if f == "perplexity":
        if res.get("cited_store") and not REFUSE.search(ans):
            return "indexed", "store page cited from Perplexity's search index (not a live fetch)"
        return ("blocked" if REFUSE.search(ans) else "unknown"), "no store citation" if not res.get("cited_store") else "cited, answer reports a block"
    return "unknown", ""


def one_store(domain, cap):
    d = OUT / domain; d.mkdir(parents=True, exist_ok=True)
    url = f"https://www.{domain}/"
    rec = {"domain": domain, "url": url, "started": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    rb = read_robots(domain); (d / "robots.txt").write_text(rb.pop("raw")); rec["robots"] = rb
    rec["control"] = control(url)
    rec["control"]["ok"] = rec["control"]["status"] == 200 and bool(rec["control"]["title"])   # 202/403 or no title: needs a real-browser check
    calls = {"claude": lambda: fetch_claude(url, cap), "gemini": lambda: fetch_gemini(url, cap),
             "openai": lambda: fetch_openai(url, cap), "perplexity": lambda: fetch_perplexity(url, domain, cap)}
    rec["fetch"] = {}
    for name, fn in calls.items():
        try:
            res = fn()
        except SystemExit:
            raise
        except Exception as e:
            res = {"error": f"{type(e).__name__}: {e}"[:400]}
        (d / f"{name}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False))
        verdict, why = classify(name, res, domain)
        rec["fetch"][name] = {"verdict": verdict, "why": why, "answer": (res.get("answer") or "")[:300], "cost_usd": res.get("cost_usd", 0)}
    (d / "record.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    return rec


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=float, default=30.0); ap.add_argument("--only")
    a = ap.parse_args()
    load_env()
    stores = yaml.safe_load((HERE / "stores-pilot.yaml").read_text())["stores"]
    if a.only:
        stores = [s for s in stores if s in a.only.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for rec in ex.map(lambda s: one_store(s, a.cap), stores):
            recs.append(rec)
            print(f"{rec['domain']:<16} control={rec['control']['status']} " + " ".join(f"{k}={v['verdict']}" for k, v in rec["fetch"].items()), flush=True)
    (OUT / "summary.json").write_text(json.dumps(recs, indent=1, ensure_ascii=False))
    print(f"\n{len(recs)} stores, spend about ${spend['usd']:.2f} -> {OUT}")


if __name__ == "__main__":
    main()
