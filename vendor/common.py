#!/usr/bin/env python3
"""Shared pieces for the Agent Grounding Study: env, prices, one caller per vendor, usage log."""
import json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ENV_FILE = os.path.expanduser("~/cortex/private/cortex-private/tools/deep-research/.env")
USAGE = os.path.join(OUT, "usage.jsonl")

# List prices per million tokens (input, output). APPROXIMATE for the 2026 minis; the report flags them. Edit here, re-run report.py.
PRICES = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-opus-5-5": (4.00, 20.00),
    "gpt-5.4-mini": (0.25, 2.00),
    "gpt-6.1-sol": (2.00, 10.00),   # 2026-10-13: the frontier OpenAI answer model of the five-topic study (providers.json pin)
    "gemini-3.1-flash-lite": (0.10, 0.40),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "gemini-4-argon": (2.00, 10.00),   # 2026-10-19: the frontier Google answer model of the what-to-do line test (providers.json: $2 in / $10 out until 2026-12-01, then $4 / $20)
    "gpt-5.5": (1.25, 10.00),
}
MODELS = {  # answer models; key = short name used in files and tables
    "haiku45": {"id": "claude-haiku-4-5-20251001", "vendor": "anthropic", "label": "Claude Haiku 4.5", "tier": "cheap"},
    "gpt54mini": {"id": "gpt-5.4-mini", "vendor": "openai", "label": "GPT-5.4 mini", "tier": "cheap"},
    "flashlite31": {"id": "gemini-3.1-flash-lite", "vendor": "google", "label": "Gemini 3.1 Flash-Lite", "tier": "cheap"},
    "opus55": {"id": "claude-opus-5-5", "vendor": "anthropic", "label": "Claude Opus 5.5 (ceiling)", "tier": "ceiling"},
    "gpt61sol": {"id": "gpt-6.1-sol", "vendor": "openai", "label": "GPT-6.1 Sol", "tier": "ceiling"},
    "gemini31pro": {"id": "gemini-3.1-pro-preview", "vendor": "google", "label": "Gemini 3.1 Pro", "tier": "ceiling"},
    "argon": {"id": "gemini-4-argon", "vendor": "google", "label": "Gemini 4 Argon", "tier": "ceiling"},   # 2026-10-19 (Karen): swapped in for Gemini 3.1 Pro as an answer model; call_gemini's thinkingLevel "low" is the level-only config Argon takes
}
ARMS = ["alone", "axioms", "wrong"]
WRONG_FOLDER = {"sunscreen": "mattresses", "skincare": "mattresses", "mattresses": "sunscreen-sun-protection", "mattress": "sunscreen-sun-protection"}
RIGHT_FOLDER = {"sunscreen": "sunscreen-sun-protection", "skincare": "skincare-actives", "mattresses": "mattresses", "mattress": "mattresses"}


def P(kind, judge=None):
    """Path for a file of the active question set (env SET; empty = the pilot)."""
    st = os.environ.get("SET", "")
    if not st:
        legacy = {"questions": os.path.join(HERE, "questions.json"), "retrieval": os.path.join(OUT, "retrieval.json"), "keys": os.path.join(OUT, "keys.json"),
                  "answers": os.path.join(OUT, "answers.json"), "verdicts": os.path.join(OUT, f"verdicts-{judge}.json"), "report": os.path.join(OUT, "report.json")}
        return legacy[kind]
    name = {"questions": f"{st}-questions.json", "retrieval": f"{st}-retrieval.json", "keys": f"{st}-keys.json", "answers": f"{st}-answers.json",
            "verdicts": f"{st}-verdicts-{judge}.json", "report": f"{st}-report.json"}[kind]
    return os.path.join(OUT, name)


def load_env():
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cost_usd(model_id, usage):
    p = PRICES.get(model_id) or PRICES.get(re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model_id)) or (0, 0)
    return usage["input"] / 1e6 * p[0] + usage["output"] / 1e6 * p[1]


def log_usage(stage, model, usage, cost, extra=None):
    os.makedirs(OUT, exist_ok=True)
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "stage": stage, "model": model, **usage, "cost_usd": round(cost, 5)}
    if extra:
        row.update(extra)
    with open(USAGE, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def spent(stage_prefix=None):
    if not os.path.exists(USAGE):
        return 0.0
    tot = 0.0
    for line in open(USAGE):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if stage_prefix is None or r.get("stage", "").startswith(stage_prefix):
            tot += r.get("cost_usd", 0)
    return tot


def parse_json(text):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in text: " + text[:200])
    return json.loads(m.group(0))


# ---------- vendor callers. Each returns {"text", "usage": {"input","output"}, "model", "secs", "extra"} ----------

def call_anthropic(model, system, user, max_tokens=2000, json_schema=None, tools=None, effort=None, timeout=300):
    import anthropic
    client = anthropic.Anthropic(timeout=timeout)
    kw = {}
    oc = {}
    if effort:
        oc["effort"] = effort
    if json_schema:
        oc["format"] = {"type": "json_schema", "schema": json_schema}
    if oc:
        kw["output_config"] = oc
    if tools:
        kw["tools"] = tools
    messages = [{"role": "user", "content": user}]
    total = {"input": 0, "output": 0}
    searches = 0
    t0 = time.time()
    for _ in range(4):  # pause_turn continuations when tools run
        r = client.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages, **kw)
        u = r.usage
        total["input"] += u.input_tokens + (u.cache_read_input_tokens or 0) + (u.cache_creation_input_tokens or 0)
        total["output"] += u.output_tokens
        stu = getattr(u, "server_tool_use", None)
        if stu is not None:
            searches += getattr(stu, "web_search_requests", 0) or 0
        if r.stop_reason == "refusal":
            raise RuntimeError("refusal")
        if r.stop_reason == "pause_turn":
            messages = messages + [{"role": "assistant", "content": r.content}]
            continue
        text = "\n".join(b.text for b in r.content if b.type == "text")
        return {"text": text, "usage": total, "model": r.model, "secs": time.time() - t0, "extra": {"searches": searches}}
    raise RuntimeError("no final answer after continuations")


def call_openai(model, system, user, max_tokens=2000, json_schema=None, reasoning="low", timeout=300):
    key = os.environ["OPENAI_API_KEY"]
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_completion_tokens": max_tokens}
    if reasoning:
        body["reasoning_effort"] = reasoning
    if json_schema:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "out", "schema": json_schema, "strict": False}}
    t0 = time.time()
    r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + key}, json=body, timeout=timeout)
    if r.status_code == 400 and "reasoning_effort" in body:
        del body["reasoning_effort"]
        t0 = time.time()
        r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + key}, json=body, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"openai HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    ch = d["choices"][0]
    u = d.get("usage", {})
    reasoning_toks = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    return {"text": ch["message"]["content"] or "", "usage": {"input": u.get("prompt_tokens", 0), "output": u.get("completion_tokens", 0)},
            "model": d.get("model", model), "secs": time.time() - t0, "extra": {"reasoning_tokens": reasoning_toks, "finish": ch.get("finish_reason")}}


def call_openai_responses(model, system, user, max_tokens=2000, reasoning="low", web=True, timeout=300):
    key = os.environ["OPENAI_API_KEY"]
    body = {"model": model, "instructions": system, "input": user, "max_output_tokens": max_tokens}
    if reasoning:
        body["reasoning"] = {"effort": reasoning}
    if web:
        body["tools"] = [{"type": "web_search"}]
    t0 = time.time()
    r = requests.post("https://api.openai.com/v1/responses", headers={"Authorization": "Bearer " + key}, json=body, timeout=timeout)
    if r.status_code == 400 and web and "web_search" in r.text:
        body["tools"] = [{"type": "web_search_preview"}]
        t0 = time.time()
        r = requests.post("https://api.openai.com/v1/responses", headers={"Authorization": "Bearer " + key}, json=body, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"openai responses HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    text, searches = [], 0
    for item in d.get("output", []):
        if item.get("type") == "web_search_call":
            searches += 1
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text.append(c.get("text", ""))
    u = d.get("usage", {})
    return {"text": "\n".join(text), "usage": {"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0)},
            "model": d.get("model", model), "secs": time.time() - t0, "extra": {"searches": searches, "status": d.get("status")}}


def call_gemini(model, system, user, max_tokens=2000, json_schema=None, thinking="low", temperature=None, timeout=300, tools=None):
    key = os.environ["GOOGLE_AI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    gen = {"maxOutputTokens": max_tokens}
    if temperature is not None:
        gen["temperature"] = temperature
    if json_schema:
        gen["responseMimeType"] = "application/json"
        gen["responseSchema"] = json_schema
    attempts = []
    if thinking == "low":
        attempts = [{"thinkingLevel": "low"}, {"thinkingBudget": 0}, None]
    elif thinking == "judge":
        attempts = [{"thinkingBudget": 2048}, None]
    else:
        attempts = [None]
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    last = None
    for tc in attempts:
        g = dict(gen)
        if tc:
            g["thinkingConfig"] = tc
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": g}
        if tools:
            body["tools"] = tools
        t0 = time.time()
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code == 400 and tc is not None:
            last = r.text[:200]
            continue
        if r.status_code != 200:
            raise RuntimeError(f"gemini HTTP {r.status_code}: {r.text[:300]}")
        d = r.json()
        cand = d["candidates"][0]
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
        um = d.get("usageMetadata", {})
        gm = cand.get("groundingMetadata") or {}
        queries = gm.get("webSearchQueries") or []
        return {"text": text, "usage": {"input": um.get("promptTokenCount", 0), "output": um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)},
                "model": d.get("modelVersion", model), "secs": time.time() - t0, "extra": {"thinking": tc, "finish": cand.get("finishReason"), "searches": len(queries), "grounded": bool(gm)}}
    raise RuntimeError(f"gemini 400 on every thinking config: {last}")


def call(vendor, model, system, user, **kw):
    if vendor == "anthropic":
        return call_anthropic(model, system, user, **kw)
    if vendor == "openai":
        return call_openai(model, system, user, **kw)
    if vendor == "google":
        return call_gemini(model, system, user, **kw)
    raise ValueError(vendor)
