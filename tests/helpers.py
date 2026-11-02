import os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import bot
class Base(unittest.TestCase):
    LAYERS = "none"
    def setUp(self):
        d = tempfile.mkdtemp()
        self.env = dict(os.environ)
        os.environ.update(MIRROR_STATE=d + "/s.json", MIRROR_LOG=d + "/l.log", MIRROR_FUNCS=d + "/f.json",
                          MIRROR_COST=d + "/c.json", MIRROR_LAYERS=self.LAYERS)
        for k in ("MIRROR_FAKE_REPLY", "MIRROR_FAKE_DEFINE", "MIRROR_GOAL"): os.environ.pop(k, None)
        self.real_post = bot.post; self.s = bot.fresh()
    def tearDown(self):
        bot.post = self.real_post; os.environ.clear(); os.environ.update(self.env)
    def prop(self, reply, define=None):
        os.environ["MIRROR_FAKE_REPLY"] = reply
        if define is not None: os.environ["MIRROR_FAKE_DEFINE"] = define
        return bot.cmd_propose(self.s)
    def step(self, reply, define=None): self.prop(reply, define); return bot.cmd_approve(self.s)
    def capture(self, reply='{"cmd":"stop"}', usage=None):
        """Fake the HTTP post; record request bodies."""
        sent = []
        def fake(body):
            sent.append(body)
            return {"choices": [{"message": {"content": reply}}], "usage": usage or {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}}
        bot.post = fake; os.environ.pop("MIRROR_FAKE_REPLY", None); return sent
    def log(self):
        with open(os.environ["MIRROR_LOG"]) as fh: return fh.read()
