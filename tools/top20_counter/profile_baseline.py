"""Profile exact official-engine baseline losses and replay-guided idle opportunities."""

from __future__ import annotations

import contextlib
import io
import json
from collections import Counter
from pathlib import Path

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "ready_2500_final_20260930/main.py"
V4 = ROOT / "submission_ready_20260930/main.py"
rows = []
for seed in (15100203, 15100289, 17830011, 17830071):
    for seat in (0, 1):
        players = [str(BASE), str(V4)] if seat == 0 else [str(V4), str(BASE)]
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
            last = env.run(players)[-1]
        counts = Counter()
        phases = []
        for step in range(719):
            obs = env.steps[step][seat].get("observation")
            action = env.steps[step + 1][seat].get("action")
            if not isinstance(obs, dict) or not isinstance(action, dict):
                continue
            farm = obs["farms"][seat]
            positions = [farm["farmer"], *farm["hands"]]
            commands = [action.get("farmer"), *(action.get("hands") or [])]
            inventories = (obs.get("private") or {}).get("inventories") or []
            for actor, (position, command) in enumerate(zip(positions, commands)):
                if not isinstance(command, list) or not command:
                    continue
                counts["op:" + command[0]] += 1
                if command != ["PASS"]:
                    continue
                counts["pass"] += 1
                x, y = position
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict):
                    if tile.get("animal"):
                        if not tile.get("cared_today"):
                            counts["pass:uncared:" + str(tile["animal"])] += 1
                        if not tile.get("fed_today"):
                            counts["pass:unfed:" + str(tile["animal"])] += 1
                            if actor < len(inventories) and inventories[actor].get("WHEAT", 0) > 0:
                                counts["pass:unfed_with_wheat:" + str(tile["animal"])] += 1
                    if tile.get("animal") and tile.get("fertilizer_available"):
                        counts["pass:fert:" + str(tile["animal"])] += 1
                    if tile.get("animal") and tile.get("yield_units", 0) > 0:
                        counts["pass:animal_yield:" + str(tile["animal"])] += 1
                    if tile.get("kind") == "PLANT" and not tile.get("watered_today"):
                        counts["pass:dry_crop:" + str(tile.get("crop"))] += 1
                    if tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0:
                        counts["pass:crop_yield:" + str(tile.get("crop"))] += 1
                elif tile is None:
                    counts["pass:empty"] += 1
            if step in (23, 143, 287, 431, 575, 718):
                phases.append({"step": step, "own_money": farm["money"],
                               "rival_money": obs["farms"][1 - seat]["money"]})
        row = {"seed": seed, "seat": seat,
               "own_reward": last[seat]["reward"], "opponent_reward": last[1 - seat]["reward"],
               "counts": dict(counts), "phases": phases,
               "log_excerpt": log.getvalue()[:250]}
        rows.append(row)
        print(seed, seat, row["own_reward"], row["opponent_reward"],
              {k: v for k, v in counts.items() if k.startswith("pass:")}, flush=True)
(HERE / "BASELINE_LOSS_PROFILE.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
