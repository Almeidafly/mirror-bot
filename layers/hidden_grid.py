"""Layer 2: hidden 3x3 world and a visit-all goal. The size exists only bot-side; Grok never sees it."""
import bot
HIDDEN_N = 3  # bot-side only, never sent to Grok
def fresh(s): s["goal_logged"] = False
def inside(x, y): return 0 <= x < HIDDEN_N and 0 <= y < HIDDEN_N
def goal(g, s, compact):
    return "Visit all cells, then stop. p=pos,h=heading,v=visited. If forward fails to move, adapt." if compact else \
           "Goal: visit every cell, then stop. If a forward does not change your position as expected, adapt."
def after_approve(s):
    if len(s["visited"]) < HIDDEN_N * HIDDEN_N or s.get("goal_logged"): return None
    g = f"goal reached: all {len(s['visited'])} cells" + "".join(x for x in bot.hook("goal_extra", s) if x) + f", path={bot.cj(s['visited'])}"
    s["goal_logged"] = True; bot.dlog("goal", None, g); return g
