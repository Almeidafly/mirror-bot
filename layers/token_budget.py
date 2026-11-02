"""Layer 3: token budget. Reads usage from every Grok response, logs it per call, and keeps running totals.
Also uses a compact prompt, a small max_tokens, and makes 'look' a local human-only command."""
import os
import bot
def max_tokens(): return int(os.environ.get("MIRROR_MAX_TOKENS", "1024"))  # grok-4 counts hidden reasoning as completion
def compact(): return True
def fresh(s): s["tokens"] = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}; s["last_tokens"] = 0
def body(b): return dict(b, max_tokens=max_tokens())
def sys(s, compact): return "Goal includes using FEW tokens. Think briefly."
def view(v, s):
    out = {"p": [v["x"], v["y"]], "h": v["heading"], "v": v["visited"]}
    for k, val in v.items():
        if k not in ("x", "y", "heading", "visited"): out["pend" if k == "pending" else k] = val
    return out
def usage(s, u, tag):
    p, c = u.get("prompt_tokens", 0), u.get("completion_tokens", 0); t = u.get("total_tokens", p + c)
    T = s["tokens"]; T["prompt"] += p; T["completion"] += c; T["total"] += t; T["calls"] += 1; s["last_tokens"] += t
    bot.dlog("tokens", {"call": tag}, f"prompt={p} completion={c} total={t} running_total={T['total']}")
def parse_name(c): return (None, "look is human-only (state is already in the prompt)") if c == "look" else None
def result(r, s, d):
    used = s.get("last_tokens", 0); s["last_tokens"] = 0
    return r + f" | tokens {used}/{s['tokens']['total']}"
def goal_extra(s):
    T = s["tokens"]; return f", tokens total={T['total']} (prompt {T['prompt']}, completion {T['completion']}, {T['calls']} calls)"
def cmd_look(s):  # human-only, local; no API call
    T = s["tokens"]; return f"pos ({s['x']},{s['y']}) {s['heading']} visited {len(s['visited'])} {bot.cj(s['visited'])} pending {bot.cj(s['pending'])} tokens {T['total']} ({T['calls']} calls)"
def cli(): return {"look": cmd_look}
