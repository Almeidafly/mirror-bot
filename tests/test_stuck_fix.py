"""Layer 4: stuck fix."""
import os, re, json
from helpers import Base, bot
from test_hidden_grid import EDGE_WORDS
class StuckFix(Base):
    LAYERS = "functions,hidden_grid,token_budget,stuck_fix"
    def corner(self): self.step('{"cmd":"forward","n":3}')  # now at (2,0) facing E
    def test_note_and_refuse_repeat(self):
        self.corner(); self.step('{"cmd":"forward","n":1}')
        self.assertEqual(bot.view(self.s)["note"], "last move had no effect: forward")
        self.assertIn("refused: repeat of a command that had no effect", self.prop('{"cmd":"forward","n":1}'))
        self.assertTrue(self.prop('{"cmd":"forward","n":2}').startswith("pending"))  # different command is allowed
    def test_function_that_moved_nothing(self):
        spin = '{"name":"push","description":"d","steps":[{"cmd":"forward","n":1},{"cmd":"left"},{"cmd":"right"}],"repeat":1}'
        self.corner(); self.step('{"cmd":"push"}', spin); self.step('{"cmd":"push"}')
        self.assertIn("refused: repeat", self.prop('{"cmd":"push"}'))
        self.step('{"cmd":"right"}'); self.assertNotIn("note", bot.view(self.s)); self.assertTrue(self.prop('{"cmd":"push"}').startswith("pending"))
    def test_note_reaches_grok_without_edge_words(self):
        self.corner(); self.step('{"cmd":"forward","n":1}'); sent = self.capture(); bot.cmd_propose(self.s)
        txt = json.dumps(sent[0]).lower(); self.assertIn("no effect", txt)
        for w in EDGE_WORDS: self.assertIsNone(re.search(r"\b" + w + r"\b", txt), w)
    def test_alone_unbounded_never_stuck(self):
        os.environ["MIRROR_LAYERS"] = "stuck_fix"; self.s = bot.fresh()
        self.step('{"cmd":"forward","n":3}'); self.assertIsNone(self.s["no_effect"])
    def test_disabled(self):
        os.environ["MIRROR_LAYERS"] = "functions,hidden_grid,token_budget"; self.s = bot.fresh()
        self.corner(); self.step('{"cmd":"forward","n":1}'); self.assertTrue(self.prop('{"cmd":"forward","n":1}').startswith("pending"))
if __name__ == "__main__":
    import unittest; unittest.main()
