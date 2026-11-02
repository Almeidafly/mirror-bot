"""Layer 1: functions. Runs with MIRROR_LAYERS=functions."""
import os, json
from helpers import Base, bot
from layers import functions as F
SPEC = '{"name":"zigzag","description":"forward 1, right, forward 1, left","steps":[{"cmd":"forward","n":1},{"cmd":"right"},{"cmd":"forward","n":1},{"cmd":"left"}],"repeat":2}'
class Functions(Base):
    LAYERS = "functions"
    def test_invent_approve_use(self):
        out = self.prop('{"cmd":"zigzag"}', SPEC); self.assertIn("pending new function", out)
        self.assertEqual(F.load_funcs(), {}); self.assertEqual((self.s["x"], self.s["y"]), (0, 0))
        self.assertIn("registered function zigzag", bot.cmd_approve(self.s)); self.assertIn("zigzag", F.load_funcs())
        self.assertIn('pending {"cmd": "zigzag"}', self.prop('{"cmd":"zigzag"}', "SHOULD NOT BE ASKED"))
        bot.cmd_approve(self.s); self.assertEqual((self.s["x"], self.s["y"], self.s["heading"]), (2, 2, "E"))
    def test_deny_new_function(self):
        self.prop('{"cmd":"zigzag"}', SPEC); bot.cmd_deny(self.s); self.assertEqual(F.load_funcs(), {})
    def test_define_api_error(self):
        os.environ["MIRROR_FAKE_REPLY"] = '{"cmd":"zigzag"}'
        def boom(b): raise RuntimeError("HTTP 500")
        bot.post = boom
        self.assertIn("API error while defining", bot.cmd_propose(self.s)); self.assertIsNone(self.s["pending"])
    def test_function_stop_halts(self):
        self.step('{"cmd":"halt"}', '{"name":"halt","description":"d","steps":[{"cmd":"forward","n":1},{"cmd":"stop"},{"cmd":"forward","n":3}],"repeat":3}')
        self.step('{"cmd":"halt"}'); self.assertEqual(self.s["x"], 1)
    def test_bad_specs_refused(self):
        bad = {"x": "spec invalid JSON",
               '{"name":"other","description":"d","steps":[{"cmd":"left"}]}': "name mismatch",
               '{"name":"x","description":"d","steps":[{"cmd":"left"}],"code":"import os"}': "keys",
               '{"name":"x","description":"d","steps":[{"cmd":"shell","arg":"rm -rf /"}]}': "not a primitive",
               '{"name":"x","description":"d","steps":[{"cmd":"zigzag"}]}': "not a primitive",
               '{"name":"x","description":"d","steps":[]}': "steps",
               '{"name":"x","description":"d","steps":' + json.dumps([{"cmd": "left"}] * 9) + '}': "steps",
               '{"name":"x","description":"d","steps":[{"cmd":"left"}],"repeat":6}': "repeat",
               '{"name":"x","description":"d","steps":[{"cmd":"forward","n":9}]}': "n 1-3",
               '{"name":"x","description":"' + "a" * 201 + '","steps":[{"cmd":"left"}]}': "description"}
        for spec, why in bad.items():
            out = self.prop('{"cmd":"x"}', spec); self.assertTrue(out.startswith("refused") and why in out, out); self.assertIsNone(self.s["pending"])
        self.assertEqual(F.load_funcs(), {})
    def test_invalid_name(self): self.assertIn("invalid function name", self.prop('{"cmd":"Teleport!"}'))
    def test_registry_in_prompt(self):
        F.save_funcs({"zigzag": {"description": "d", "steps": [{"cmd": "left"}], "repeat": 1}})
        sent = self.capture('{"cmd":"stop"}'); bot.cmd_propose(self.s); self.assertIn("zigzag", sent[0]["messages"][0]["content"])
    def test_disabled_means_unknown(self):
        os.environ["MIRROR_LAYERS"] = "none"; self.assertIn("unknown command", self.prop('{"cmd":"zigzag"}', SPEC))
if __name__ == "__main__":
    import unittest; unittest.main()
