"""Layer 0: core. Runs with MIRROR_LAYERS=none."""
import os, json
from helpers import Base, bot
class Core(Base):
    def test_allowlisted(self):
        for r in ['{"cmd":"forward","n":3}', '{"cmd":"left"}', '{"cmd":"right"}', '{"cmd":"stop"}']:
            self.assertTrue(self.prop(r).startswith("pending"), r); bot.cmd_deny(self.s)
    def test_propose_does_not_execute_then_approve(self):
        self.prop('{"cmd":"forward","n":2}'); self.assertEqual((self.s["x"], self.s["y"]), (0, 0))
        self.assertIn("forward 2 -> (2,0)", bot.cmd_approve(self.s)); self.assertIsNone(self.s["pending"])
    def test_unbounded(self):
        for _ in range(4): self.step('{"cmd":"forward","n":3}')
        self.assertEqual(self.s["x"], 12)
        self.step('{"cmd":"left"}'); self.step('{"cmd":"forward","n":3}'); self.assertEqual((self.s["x"], self.s["y"]), (12, -3))
    def test_turns(self):
        self.step('{"cmd":"right"}'); self.assertEqual(self.s["heading"], "S"); self.step('{"cmd":"left"}'); self.step('{"cmd":"left"}')
        self.assertEqual(self.s["heading"], "N")
    def test_deny(self):
        self.prop('{"cmd":"right"}'); self.assertIn("denied", bot.cmd_deny(self.s)); self.assertEqual(self.s["heading"], "E")
    def test_refusals(self):
        for r, why in [('Sure! {"cmd":"left"}', "invalid JSON"), ('{"cmd":"teleport"}', "unknown command"),
                       ('{"cmd":"teleport","x":2}', "unexpected"), ('{"cmd":"forward","n":4}', "n 1-3"),
                       ('{"cmd":"forward","n":"2"}', "n 1-3"), ('{"cmd":"left","why":"x"}', "unexpected"),
                       ('[{"cmd":"left"}]', "not a command"), ('{"cmd":"look"}', "unknown command")]:
            out = self.prop(r); self.assertTrue(out.startswith("refused") and why in out, out); self.assertIsNone(self.s["pending"])
    def test_api_error_and_no_double_pending(self):
        k = os.environ.pop("XAI_API_KEY", None)
        self.assertIn("API error", bot.cmd_propose(self.s))
        if k: os.environ["XAI_API_KEY"] = k
        self.prop('{"cmd":"stop"}'); self.assertIn("already pending", self.prop('{"cmd":"left"}'))
    def test_approve_empty(self): self.assertIn("nothing pending", bot.cmd_approve(self.s))
    def test_log(self):
        self.step('{"cmd":"left"}'); l = self.log()
        self.assertIn("cmd=propose", l); self.assertIn("cmd=approve", l)
    def test_grok_request(self):
        sent = self.capture('{"cmd":"left"}'); self.assertIn("pending", bot.cmd_propose(self.s))
        self.assertEqual(sent[0]["model"], os.environ.get("MIRROR_MODEL", "grok-4")); self.assertIn("forward", sent[0]["messages"][0]["content"])
    def test_layers_flag(self):
        self.assertEqual(bot.active(), [])
        os.environ["MIRROR_LAYERS"] = "bogus"; self.assertEqual(bot.active(), [])
    def test_state_roundtrip(self):
        self.step('{"cmd":"forward","n":1}'); bot.save(self.s); self.assertEqual(bot.load()["x"], 1)
if __name__ == "__main__":
    import unittest; unittest.main()
