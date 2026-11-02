# Almeidafly: Mirror Bot, in layers

Mirror Bot is a stdlib-only Python sandbox robot that **only does what the xAI Grok API says**. Grok proposes one JSON command, and a human approves or denies it. There is no local heuristic and no autonomous loop.

The repo is built as **cumulative layers**. Each layer has its own commit, branch, tag, and GitHub release. Clone the repo and you can use all of the layers or none of them: check out an earlier tag, or turn layers off at runtime.

## Quick start
    git clone https://github.com/fitzyracing1/Almeidafly && cd Almeidafly
    export XAI_API_KEY=...            # env only; never commit it
    python3 mirror.py propose         # Grok proposes one command (nothing runs)
    python3 mirror.py approve         # run the pending command verbatim
    python3 mirror.py deny            # discard it
    python3 -m unittest discover -s tests -v    # offline tests, no network

Settings: `MIRROR_MODEL` (default `grok-4`) and `MIRROR_GOAL` (overrides the task text). Runtime files are `state.json`, `driver.log`, and `functions.json`. They are git-ignored.

## Turning layers on and off
`MIRROR_LAYERS` = `all` (the default), `none` (core only), or a comma list such as `functions,token_budget`. A layer whose file is missing at the checked-out tag is skipped. Every layer lives in its own module under `layers/` and plugs into the core (`bot.py`) through hooks. Running `python3 mirror.py` with no argument prints the active layers.

To use exactly the code of one layer, check out its tag: `git checkout v0.2.0` (or the branch `layer-2-hidden-grid-goal`).

## Layers
| Tag | Branch | Flag name | Adds |
|---|---|---|---|
| v0.0.0 | layer-0-core | (always on) | Grok-only driver, propose/approve/deny gate, strict allowlist (`forward` n 1-3, `left`, `right`, `stop`), refusals, `driver.log`, unbounded world |
| v0.1.0 | layer-1-functions | `functions` | Unknown command name → a second Grok call defines it from primitives (strictly validated: name regex, 1-8 steps, repeat 1-5, no other keys, no code). It becomes a pending new function and is saved to `functions.json` only on `approve` |
| v0.2.0 | layer-2-hidden-grid-goal | `hidden_grid` | Hidden 3x3 world (cells 0..2). `forward` stops there silently, and only the local log records `[local: blocked]`. The goal is to visit all 9 cells, and `goal reached` is logged once. No size, edge, or boundary word ever reaches Grok (tested) |
