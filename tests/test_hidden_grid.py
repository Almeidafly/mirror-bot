"""Layer 2: hidden grid + visit-all goal. Runs with MIRROR_LAYERS=functions,hidden_grid (and alone)."""
import os, re, json
from helpers import Base, bot
SNAKE = '{"name":"snake","description":"d","steps":[{"cmd":"forward","n":2},{"cmd":"right"},{"cmd":"forward","n":1},{"cmd":"right"},{"cmd":"forward","n":2},{"cmd":"left"},{"cmd":"forward","n":1},{"cmd":"left"}],"repeat":2}'
EDGE_WORDS = ("size", "grid", "walls?", "edges?", "8x8", "3x3", r"bound\w*", "hidden", "border", "limit", "9", "blocked", "local")
class HiddenGrid(Base):
    LAYERS = "functions,hidden_grid"
    def test_silent_stop(self):
        r = self.step('{"cmd":"forward","n":3}'); self.assertEqual((self.s["x"], self.s["y"]), (2, 0)); self.assertIn("local: blocked, moved 2/3", r)
        self.step('{"cmd":"left"}'); self.step('{"cmd":"forward","n":1}'); self.assertEqual((self.s["x"], self.s["y"]), (2, 0))
    def test_goal_once(self):
        self.step('{"cmd":"snake"}', SNAKE); r = self.step('{"cmd":"snake"}'); self.assertIn("goal reached: all 9 cells", r)
        self.assertNotIn("goal reached", self.step('{"cmd":"stop"}')); self.assertEqual(self.log().count("goal reached"), 1)
    def test_alone(self):
        os.environ["MIRROR_LAYERS"] = "hidden_grid"
        for _ in range(3): self.step('{"cmd":"forward","n":3}')
        self.assertEqual(self.s["x"], 2)
    def test_no_edge_data(self):
        for c in ('{"cmd":"forward","n":3}', '{"cmd":"left"}', '{"cmd":"forward","n":3}'): self.step(c)  # hit the boundary first
        for lay in ("functions,hidden_grid", "all"):
            os.environ["MIRROR_LAYERS"] = lay
            sent = self.capture('{"cmd":"stop"}'); self.s["pending"] = None; bot.cmd_propose(self.s)
            txt = json.dumps(sent[0]).lower()
            for w in EDGE_WORDS: self.assertIsNone(re.search(r"\b" + w + r"\b", txt), (lay, w))
        self.assertNotIn("size", json.dumps(bot.fresh()))
if __name__ == "__main__":
    import unittest; unittest.main()
