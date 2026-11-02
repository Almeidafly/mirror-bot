"""Layer 3: token budget. Runs with MIRROR_LAYERS=all (present layers) and token_budget alone."""
import os, json
from helpers import Base, bot
class TokenBudget(Base):
    LAYERS = "functions,hidden_grid,token_budget"
    U = {"prompt_tokens": 100, "completion_tokens": 7, "total_tokens": 150}
    def test_usage_logged_and_totaled(self):
        sent = self.capture('{"cmd":"left"}', self.U)
        bot.cmd_propose(self.s); self.assertEqual(sent[0]["max_tokens"], 1024)
        self.assertIn("tokens 150/150", bot.cmd_approve(self.s))
        bot.cmd_propose(self.s); self.assertIn("tokens 150/300", bot.cmd_approve(self.s))
        self.assertEqual(self.s["tokens"], {"prompt": 200, "completion": 14, "total": 300, "calls": 2})
        self.assertIn("prompt=100 completion=7 total=150 running_total=300", self.log())
    def test_max_tokens_env(self):
        os.environ["MIRROR_MAX_TOKENS"] = "300"; sent = self.capture(); bot.cmd_propose(self.s); self.assertEqual(sent[0]["max_tokens"], 300)
    def test_compact_prompt(self):
        sent = self.capture(); bot.cmd_propose(self.s); m = sent[0]["messages"]; txt = m[0]["content"] + m[1]["content"]
        self.assertLess(len(txt), 600); self.assertIn("few tokens", txt.lower()); self.assertIn("save calls", txt); self.assertIn('{"p":[0,0]', txt)
        os.environ["MIRROR_LAYERS"] = "functions,hidden_grid"; sent = self.capture(); self.s["pending"] = None; bot.cmd_propose(self.s)
        self.assertGreater(len(sent[0]["messages"][0]["content"]), len(m[0]["content"]))  # off -> verbose prompt
    def test_goal_line_has_tokens(self):
        os.environ["MIRROR_FAKE_DEFINE"] = '{"name":"snake","description":"d","steps":[{"cmd":"forward","n":2},{"cmd":"right"},{"cmd":"forward","n":1},{"cmd":"right"},{"cmd":"forward","n":2},{"cmd":"left"},{"cmd":"forward","n":1},{"cmd":"left"}],"repeat":2}'
        self.capture('{"cmd":"snake"}', self.U); bot.cmd_propose(self.s); bot.cmd_approve(self.s); bot.cmd_propose(self.s)
        r = bot.cmd_approve(self.s); self.assertIn("goal reached: all 9 cells, tokens total=", r)
    def test_look_human_only(self):
        self.assertIn("refused: look is human-only", self.prop('{"cmd":"look"}')); self.assertIsNone(self.s["pending"])
        self.assertIn("not a primitive", self.prop('{"cmd":"x"}', '{"name":"x","description":"d","steps":[{"cmd":"look"}]}'))
        sent = self.capture(); bot.cmd_propose(self.s); self.assertNotIn("look", json.dumps(sent[0]))
        self.assertIn("pos (0,0) E", bot.commands()["look"](self.s)); self.assertEqual(self.s["heading"], "E")
    def test_alone(self):
        os.environ["MIRROR_LAYERS"] = "token_budget"; self.s = bot.fresh(); sent = self.capture('{"cmd":"forward","n":3}', self.U)
        bot.cmd_propose(self.s); self.assertIn("tokens 150/150", bot.cmd_approve(self.s)); self.assertEqual(self.s["x"], 3)
if __name__ == "__main__":
    import unittest; unittest.main()
