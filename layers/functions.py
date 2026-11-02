"""Layer 1: Grok-invented functions. An unknown command name triggers a second Grok call that defines it
from primitives; the spec is strictly validated and saved to functions.json only on approve."""
import json, os, re
import bot
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$"); MAX_STEPS = 8; MAX_REPEAT = 5; MAX_DESC = 200
def fpath(): return bot.path("MIRROR_FUNCS", "functions.json")
def load_funcs():
    if not os.path.exists(fpath()): return {}
    with open(fpath()) as fh: return json.load(fh)
def save_funcs(f):
    with open(fpath(), "w") as fh: json.dump(f, fh, indent=1)

def sys(s, compact):
    f = load_funcs()
    if compact: return 'Or {"cmd":"<fn>"}. Fns: ' + bot.cj({k: v["description"] for k, v in f.items()}) + ". Unknown snake_case name = new fn you will define. Reusable multi-step fns save calls."
    return ('Registered functions (call as {"cmd":"<name>"}): ' + json.dumps(f) + ". If a useful multi-step command is missing, "
            'you may propose a NEW name as {"cmd":"<snake_case_name>"}; you will then be asked to define it from primitives, and a human approves it.')
def parse_name(c):
    if c in load_funcs(): return {"cmd": c}, None
    if not NAME_RE.match(c): return None, "invalid function name"
    return {"new": c}, None

def ask_define(s, name):
    if "MIRROR_FAKE_DEFINE" in os.environ: return os.environ["MIRROR_FAKE_DEFINE"]  # test injection only
    if bot.compact():
        sysm = (f'Define fn "{name}". Reply ONE JSON only: {{"name":"{name}","description":"short","steps":[...],"repeat":1-{MAX_REPEAT}}}. '
                f'steps: 1-{MAX_STEPS} primitives: {{"cmd":"left"|"right"|"stop"}} or {{"cmd":"forward","n":1-3}}. Be brief.')
    else:
        sysm = (f"Define the new Mirror Bot function '{name}'. Reply with exactly ONE JSON object and nothing else: "
                f'{{"name":"{name}","description":"<= {MAX_DESC} chars","steps":[...],"repeat":1}}. steps: 1-{MAX_STEPS} primitives only, each one of '
                '{"cmd":"forward","n":1-3} {"cmd":"left"} {"cmd":"right"} {"cmd":"stop"}. ' f"repeat: integer 1-{MAX_REPEAT}. No other keys, no code.")
    st = bot.cj(bot.view(s)) if bot.compact() else "Current state:\n" + json.dumps(bot.view(s))
    return bot.call_grok([{"role": "system", "content": sysm}, {"role": "user", "content": st}], s, "define")

def validate_spec(raw, name):
    try: d = json.loads(raw)
    except Exception: return None, "spec invalid JSON"
    if not isinstance(d, dict): return None, "spec not an object"
    if not set(d) <= {"name", "description", "steps", "repeat"} or not {"name", "description", "steps"} <= set(d): return None, "spec keys must be name, description, steps, optional repeat"
    if d["name"] != name: return None, "spec name mismatch"
    if not isinstance(d["description"], str) or not 0 < len(d["description"]) <= MAX_DESC: return None, f"description must be 1-{MAX_DESC} chars"
    st = d["steps"]
    if not isinstance(st, list) or not 1 <= len(st) <= MAX_STEPS: return None, f"steps must be a list of 1-{MAX_STEPS}"
    for x in st:
        p, err = bot.parse_prim(x)
        if err: return None, f"bad step {json.dumps(x)}: {err}"
    rp = d.get("repeat", 1)
    if type(rp) is not int or not 1 <= rp <= MAX_REPEAT: return None, f"repeat must be integer 1-{MAX_REPEAT}"
    return {"name": name, "description": d["description"], "steps": st, "repeat": rp}, None

def define(s, name):
    try: raw = ask_define(s, name)
    except Exception as e: r = f"refused: API error while defining: {e}"; bot.dlog("define", None, r); return r
    spec, err = validate_spec(raw.strip(), name)
    if err: r = f"refused: {err}"; bot.dlog("define", raw, r); return r
    s["pending"] = {"define": spec}; r = f"pending new function {json.dumps(spec)} (nothing executed)"; bot.dlog("define", raw, r); return r
def approve_define(s, d):
    f = load_funcs(); sp = d["define"]; f[sp["name"]] = {k: sp[k] for k in ("description", "steps", "repeat")}; save_funcs(f)
    return f"registered function {sp['name']}: {json.dumps(f[sp['name']])}"
def run(s, d):
    f = load_funcs().get(d["cmd"])
    if not f: return None
    out = []
    for _ in range(f["repeat"]):
        for st in f["steps"]:
            out.append(bot.run_prim(s, st))
            if st["cmd"] == "stop": return f"{d['cmd']}: " + " | ".join(out)
    return f"{d['cmd']}: " + " | ".join(out)
