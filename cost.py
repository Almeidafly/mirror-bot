#!/usr/bin/env python3
"""API cost optimizer CLI (layer 5).
  python3 cost.py export-mirror mirror_request.json   # Mirror Bot's own Grok call as a request file
  python3 cost.py propose <request.json>              # real calls: measure before, Grok proposes, measure after
  python3 cost.py approve | deny                      # approve writes <request>.optimized.json"""
import sys, bot
def main(a):
    if "api_cost" not in bot.active(): print("refused: api_cost layer disabled (MIRROR_LAYERS)"); sys.exit(2)
    from layers import api_cost as C
    if a[:1] == ["export-mirror"] and len(a) == 2: print(C.export_mirror(a[1]))
    elif a[:1] == ["propose"] and len(a) == 2: print(C.propose(a[1]))
    elif a == ["approve"]: print(C.approve())
    elif a == ["deny"]: print(C.deny())
    else: print(__doc__); sys.exit(2)
if __name__ == "__main__": main(sys.argv[1:])
