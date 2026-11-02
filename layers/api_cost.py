"""Layer 5: API cost optimizer. Takes an xAI chat-completions request you own (a JSON file). Grok proposes a
cheaper equivalent (smaller prompt, cheaper model, lower max_tokens, cache-friendly ordering). The bot measures
before and after with real calls. Nothing is saved or applied until approve, which writes <file>.optimized.json
(the original file is never modified). First target: Mirror Bot's own Grok call (export-mirror)."""
import json, os, urllib.request
import bot
ALLOWED_KEYS = {"model", "messages", "max_tokens", "temperature", "top_p", "stop", "response_format", "seed"}
def cpath(): return bot.path("MIRROR_COST", "cost_state.json")
def load_c():
    if not os.path.exists(cpath()): return {"pending": None}
    with open(cpath()) as fh: return json.load(fh)
def save_c(c):
    with open(cpath(), "w") as fh: json.dump(c, fh, indent=1)
def models():
    if os.environ.get("MIRROR_COST_MODELS"): return [m.strip() for m in os.environ["MIRROR_COST_MODELS"].split(",")]
    req = urllib.request.Request("https://api.x.ai/v1/models", headers={"Authorization": "Bearer " + os.environ.get("XAI_API_KEY", ""), "User-Agent": "mirror-bot/3.0"})
    return [m["id"] for m in json.loads(urllib.request.urlopen(req, timeout=30).read())["data"] if "imagine" not in m["id"]]

def measure(body):
    r = bot.post(body); u = r.get("usage") or {}
    return {"model": body.get("model"), "prompt": u.get("prompt_tokens", 0), "completion": u.get("completion_tokens", 0),
            "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0), "total": u.get("total_tokens", 0),
            "cached": (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0), "usd_ticks": u.get("cost_in_usd_ticks"),
            "output": (r["choices"][0]["message"]["content"] or "")[:500]}

def validate(req, allowed_models):
    if not isinstance(req, dict): return "request must be an object"
    if not set(req) <= ALLOWED_KEYS: return f"keys must be a subset of {sorted(ALLOWED_KEYS)}"
    if req.get("model") not in allowed_models: return f"model must be one of {allowed_models}"
    m = req.get("messages")
    if not isinstance(m, list) or not m or not all(isinstance(x, dict) and set(x) == {"role", "content"} and x["role"] in ("system", "user", "assistant") and isinstance(x["content"], str) for x in m):
        return "messages must be a non-empty list of {role, content} strings"
    if "max_tokens" in req and (type(req["max_tokens"]) is not int or not 1 <= req["max_tokens"] <= 32768): return "max_tokens must be integer 1-32768"
    return None

def same_shape(a, b):
    """Equivalence check: if the original output is JSON, the candidate output must be JSON with the same keys."""
    try: ja = json.loads(a.strip())
    except Exception: return bool(b.strip())
    try: jb = json.loads(b.strip())
    except Exception: return False
    return (set(ja) == set(jb)) if isinstance(ja, dict) and isinstance(jb, dict) else type(ja) == type(jb)

OPT_SYS = ("You cut the cost of an xAI chat-completions request without changing what it asks for or its output format. "
           'Reply ONE JSON only: {"request":{...},"changes":["short reason",...]}. Allowed request keys: ' + ", ".join(sorted(ALLOWED_KEYS)) + ". "
           "Levers: shorter/compact messages (keep every rule and the exact reply format), a cheaper model from the list, "
           "lower max_tokens, static text first so prompt caching hits. Models: ")
def ask_optimizer(req, before, allowed):
    if "MIRROR_FAKE_OPT" in os.environ: return os.environ["MIRROR_FAKE_OPT"], {}
    r = bot.post({"model": os.environ.get("MIRROR_MODEL", "grok-4"), "max_tokens": 4096,
                  "messages": [{"role": "system", "content": OPT_SYS + bot.cj(allowed) + "."},
                               {"role": "user", "content": "Request:\n" + bot.cj(req) + "\nMeasured usage:\n" + bot.cj({k: before[k] for k in ("prompt", "completion", "reasoning", "total", "usd_ticks")})}]})
    return r["choices"][0]["message"]["content"] or "", r.get("usage") or {}

def propose(file):
    c = load_c()
    if c["pending"]: return "refused: a cost proposal is already pending (cost.py approve or deny)"
    with open(file) as fh: req = json.load(fh)
    allowed = models(); err = validate(req, allowed + [req.get("model")])
    if err: return f"refused: original request invalid: {err}"
    try: before = measure(req)
    except Exception as e: return f"refused: API error measuring original: {e}"
    try: raw, ou = ask_optimizer(req, before, allowed)
    except Exception as e: return f"refused: API error asking optimizer: {e}"
    try: d = json.loads(raw.strip()); cand = d["request"]; changes = d.get("changes", [])
    except Exception: r = "refused: optimizer reply is not {request, changes} JSON"; bot.dlog("cost-propose", raw, r); return r
    err = validate(cand, allowed)
    if err: r = f"refused: candidate invalid: {err}"; bot.dlog("cost-propose", raw, r); return r
    try: after = measure(cand)
    except Exception as e: return f"refused: API error measuring candidate: {e}"
    eq = same_shape(before["output"], after["output"])
    c["pending"] = {"file": file, "candidate": cand, "changes": changes, "before": before, "after": after, "same_output_shape": eq,
                    "optimizer_tokens": ou.get("total_tokens", 0)}
    save_c(c)
    r = (f"pending cost proposal for {file} (nothing saved): tokens {before['total']} -> {after['total']}"
         f" (prompt {before['prompt']}->{after['prompt']}, completion {before['completion']}->{after['completion']}),"
         f" usd_ticks {before['usd_ticks']} -> {after['usd_ticks']}, model {before['model']} -> {after['model']},"
         f" same output shape: {eq}, optimizer call cost {ou.get('total_tokens', 0)} tokens; changes: {changes}")
    bot.dlog("cost-propose", {"file": file}, r); return r
def approve():
    c = load_c(); p = c["pending"]
    if not p: return "refused: nothing pending"
    out = p["file"].rsplit(".json", 1)[0] + ".optimized.json"
    with open(out, "w") as fh: json.dump(p["candidate"], fh, indent=1)
    c["pending"] = None; save_c(c)
    r = f"approved: wrote {out} (original untouched); tokens {p['before']['total']} -> {p['after']['total']}"; bot.dlog("cost-approve", {"file": p["file"]}, r); return r
def deny():
    c = load_c(); p = c["pending"]; c["pending"] = None; save_c(c)
    r = "denied cost proposal" if p else "nothing pending"; bot.dlog("cost-deny", None, r); return r
def export_mirror(out):
    s = bot.fresh(); body = bot.request_body(bot.build_messages(s))
    with open(out, "w") as fh: json.dump(body, fh, indent=1)
    return f"wrote Mirror Bot's own propose request ({','.join(bot.active()) or 'core'}) to {out}"
