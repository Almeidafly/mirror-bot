"""Layer 4: stuck fix. Tells Grok when the last command had no effect, and refuses re-proposing that same command."""
def fresh(s): s["no_effect"] = None
def after_run(s, d, before):
    s["no_effect"] = d if (s["x"], s["y"], s["heading"]) == before and d.get("cmd") != "stop" else None
def view(v, s):
    if s.get("no_effect"): v["note"] = "last move had no effect: " + s["no_effect"]["cmd"]
    return v
def sys(s, compact): return "If note says no effect, change plan." if compact else "If the state has a note that the last move had no effect, choose a different command."
def check(s, d):
    return "repeat of a command that had no effect; choose another" if s.get("no_effect") and d == s["no_effect"] else None
