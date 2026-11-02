"""Layer 5: API cost optimizer (offline; HTTP faked)."""
import os, json, tempfile
from helpers import Base, bot
from layers import api_cost as C
def resp(content, total, prompt=None):
    return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": prompt or total - 5, "completion_tokens": 5, "total_tokens": total}}
class ApiCost(Base):
    LAYERS = "all"
    def setUp(self):
        super().setUp(); os.environ["MIRROR_COST_MODELS"] = "grok-4,grok-cheap"
        self.file = tempfile.mkdtemp() + "/req.json"; self.req = {"model": "grok-4", "messages": [{"role": "user", "content": "long " * 50 + 'reply {"cmd":"stop"}'}]}
        with open(self.file, "w") as fh: json.dump(self.req, fh)
        self.cand = {"model": "grok-cheap", "max_tokens": 64, "messages": [{"role": "user", "content": 'reply {"cmd":"stop"}'}]}
        self.sent = []
    def fake(self, outputs):
        it = iter(outputs)
        def f(body): self.sent.append(body); return next(it)
        bot.post = f
    def test_propose_measures_and_saves_nothing(self):
        self.fake([resp('{"cmd":"stop"}', 400)]); os.environ["MIRROR_FAKE_OPT"] = json.dumps({"request": self.cand, "changes": ["shorter", "cheaper model"]})
        self.fake([resp('{"cmd":"stop"}', 400), resp('{"cmd":"left"}', 60)])
        r = C.propose(self.file); self.assertIn("tokens 400 -> 60", r); self.assertIn("same output shape: True", r)
        self.assertEqual(self.sent[0], self.req); self.assertEqual(self.sent[1], self.cand)  # both measured by real calls
        with open(self.file) as fh: self.assertEqual(json.load(fh), self.req)
        self.assertFalse(os.path.exists(self.file.replace(".json", ".optimized.json")))
        self.assertIn("already pending", C.propose(self.file))
        self.assertIn("approved", C.approve())
        with open(self.file.replace(".json", ".optimized.json")) as fh: self.assertEqual(json.load(fh), self.cand)
        with open(self.file) as fh: self.assertEqual(json.load(fh), self.req)
    def test_deny_discards(self):
        os.environ["MIRROR_FAKE_OPT"] = json.dumps({"request": self.cand}); self.fake([resp("{}", 100), resp("{}", 50)])
        C.propose(self.file); self.assertIn("denied", C.deny()); self.assertIn("nothing pending", C.approve())
        self.assertFalse(os.path.exists(self.file.replace(".json", ".optimized.json")))
    def test_bad_candidates_refused(self):
        bad = [{"model": "grok-4", "messages": [{"role": "user", "content": "x"}], "tools": []},
               {"model": "gpt-9", "messages": [{"role": "user", "content": "x"}]},
               {"model": "grok-cheap", "messages": []},
               {"model": "grok-cheap", "messages": [{"role": "user", "content": "x"}], "max_tokens": "10"}]
        for cand in bad:
            os.environ["MIRROR_FAKE_OPT"] = json.dumps({"request": cand}); self.fake([resp("{}", 100)])
            self.assertIn("refused: candidate invalid", C.propose(self.file)); self.assertIsNone(C.load_c()["pending"])
        os.environ["MIRROR_FAKE_OPT"] = "prose"; self.fake([resp("{}", 100)]); self.assertIn("not {request", C.propose(self.file))
    def test_shape_check(self):
        self.assertTrue(C.same_shape('{"cmd":"stop"}', '{"cmd":"left"}')); self.assertFalse(C.same_shape('{"cmd":"stop"}', "ok"))
    def test_export_mirror(self):
        out = tempfile.mkdtemp() + "/m.json"; C.export_mirror(out)
        with open(out) as fh: b = json.load(fh)
        self.assertIn("max_tokens", b); self.assertIsNone(C.validate(b, [b["model"]]))
    def test_disabled(self):
        import subprocess, sys
        env = dict(os.environ, MIRROR_LAYERS="functions"); r = subprocess.run([sys.executable, os.path.join(bot.HERE, "cost.py"), "deny"], env=env, capture_output=True, text=True)
        self.assertIn("api_cost layer disabled", r.stdout)
if __name__ == "__main__":
    import unittest; unittest.main()
