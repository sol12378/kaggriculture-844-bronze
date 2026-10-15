"""Build self-contained replay-guided residuals on the pinned public parent."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PARENT = ROOT / "ready_2500_final_20260930/main.py"
PARENT_SHA = "f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2"
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == PARENT_SHA

WRAPPER = r'''

# Replay-guided residual, 2026-09-30. Among top-two public replay decisions,
# COLLECT_FERTILIZER was selected 1,403/1,558 times on fed, cared-for cows with
# fertilizer ready and no product; PASS was selected once. The parent route and
# market actions remain intact. No raw opponent replay is bundled.
_TOP20_PARENT = agent
_TOP20_MODE = {mode!r}

def _top20_repair(obs, action):
    if not isinstance(action, dict):
        return action
    try:
        farm = obs["farms"][int(obs["player"])]
        positions = [farm["farmer"], *(farm.get("hands") or [])]
        commands = [action.get("farmer"), *(action.get("hands") or [])]
        if len(positions) != len(commands):
            return action
        out = None
        handled = set()
        for actor, (pos, command) in enumerate(zip(positions, commands)):
            key = tuple(pos)
            if command != ["PASS"] or key in handled:
                continue
            x, y = pos
            tile = farm["tiles"][y][x]
            if not isinstance(tile, dict):
                continue
            op = None
            if tile.get("animal"):
                if _TOP20_MODE in ("cow_fert_care", "cow_fert_care_water") and not tile.get("cared_today"):
                    op = "CARE"
                elif tile.get("animal") == "COW" and tile.get("fertilizer_available"):
                    op = "COLLECT_FERTILIZER"
            elif tile.get("kind") == "PLANT" and _TOP20_MODE in ("cow_fert_water", "cow_fert_care_water"):
                if not tile.get("watered_today"):
                    op = "WATER"
            if op is None:
                continue
            if out is None:
                out = {{"farmer": list(action.get("farmer") or ["PASS"]),
                        "hands": [list(c) for c in (action.get("hands") or [])],
                        "market": [list(o) for o in (action.get("market") or [])]}}
            if actor == 0:
                out["farmer"] = [op]
            else:
                out["hands"][actor - 1] = [op]
            handled.add(key)
        return out if out is not None else action
    except Exception:
        return action

def agent(observation, configuration=None):
    action = _TOP20_PARENT(observation, configuration)
    return _top20_repair(observation, action)

# kaggle_environments 1.32.7 selects the last inserted callable, not the name.
submission_agent = agent
'''

for mode in ("cow_fert", "cow_fert_care", "cow_fert_water", "cow_fert_care_water"):
    folder = HERE / "candidate_{}".format(mode)
    folder.mkdir(exist_ok=True)
    contents = PARENT.read_text(encoding="utf-8") + WRAPPER.format(mode=mode)
    compile(contents, str(folder / "main.py"), "exec")
    (folder / "main.py").write_text(contents, encoding="utf-8")
    shutil.copyfile(ROOT / "ready_2500_final_20260930/LICENSE", folder / "LICENSE")
    (folder / "NOTICE").write_text(
        (ROOT / "ready_2500_final_20260930/NOTICE").read_text(encoding="utf-8")
        + "Original replay-guided local action repair appended by this project.\n",
        encoding="utf-8",
    )
    print(mode, hashlib.sha256((folder / "main.py").read_bytes()).hexdigest())
metadata = {"parent_sha256": PARENT_SHA, "modes": ["cow_fert", "cow_fert_care", "cow_fert_water", "cow_fert_care_water"], "submission_performed": False}
(HERE / "BUILD_AUDIT.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
